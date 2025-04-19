import json

from sqlalchemy.ext.asyncio import AsyncSession

# from module_admin.dao.task_dao import JobDao
from module_admin.entity.vo.task_vo import (
    JobExecuteModel,
    TaskModel,
    JobExecuteResponseModel,
    TaskProgressModel,
    JobSchedulerModel,
    JobLogModel,
)
from redis.asyncio import Redis as asyncio_redis
import json
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.dao.task_dao import TaskDao
from module_admin.dao.job_log_dao import JobLogDao
from typing import List
import httpx
import asyncio
from typing import List, Dict


class JobSchedulerService:
    """
    任务相关方法, 算子层接口
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8088",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        初始化异步任务客户端
        :param base_url: API服务地址
        :param timeout: 单次请求超时时间(秒)
        :param max_retries: 最大重试次数
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            base_url=base_url, timeout=timeout, limits=httpx.Limits(max_connections=100)
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def _send_request(
        self, method: str, endpoint: str, params: Dict = None, json: List[Dict] = None
    ) -> List[JobExecuteResponseModel]:
        """核心请求方法（含重试逻辑）"""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(
                    method=method, url=endpoint, params=params, json=json
                )
                response.raise_for_status()
                return [
                    JobExecuteResponseModel(**item) for item in response.json()["data"]
                ]
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"API请求失败: {str(e)}") from e
                await asyncio.sleep(2**attempt)

    async def add_jobs(
        self, job_info: List[JobExecuteModel]
    ) -> List[JobExecuteResponseModel]:
        """
        批量添加任务（对应/add_job接口）
        :param tasks: 任务参数列表
        :return: 任务执行结果列表
        """
        return 1
        # return await self._send_request(
        #     method="GET",
        #     endpoint="/add_job",
        #     json=[task.model_dump() for task in job_info],
        # )

    async def stop_jobs(self, job_uids: List[str]) -> List[JobExecuteResponseModel]:
        """
        批量停止任务（对应/stop_job接口）
        :param job_uids: 任务ID列表
        :return: 任务停止结果列表
        """
        return await self._send_request(
            method="GET", endpoint="/stop_job", params={"job_uid": job_uids}
        )

    async def close(self):
        """关闭连接池"""
        await self.client.aclose()


class AsyncJobUtil:
    """
    拓扑任务执行类
    """

    @classmethod
    async def add_job_to_redis(cls, query_redis: asyncio_redis, page_object: TaskModel):

        # # 初始化任务计数器
        # dep_num = len(job_dependencies)

        task_progress = TaskProgressModel()
        task_progress.task_uid = page_object.task_uid
        task_progress.run_ststus = "running"
        task_progress.task_complated = 0
        task_progress.task_len = len(page_object.task_yaml)
        task_progress.task_jobs = []

        for task_job in page_object.task_yaml:
            job_uid = task_job.job_uid
            job_dependencies = json.loads(task_job.job_dependencies)
            dep_num = len(job_dependencies)

            task_progress.task_jobs.append(job_uid)

            job_param = JobSchedulerModel(**task_job.model_dump())
            job_param.task_uid = page_object.task_uid

            await query_redis.set(
                f"job_param:{job_uid}", json.dumps(job_param.model_dump())
            )
            await query_redis.expire(f"job_param:{job_uid}", 86400)

            if dep_num == 0:
                await query_redis.sadd("ready_job", job_uid)
                await query_redis.expire(f"ready_job", 3600)

            else:
                await query_redis.set(f"dep_count:{job_uid}", dep_num)
                await query_redis.expire(f"dep_count:{job_uid}", 86400)
                # 记录反向依赖关系
                for dep in job_dependencies:
                    dep_key = f"deps:{dep}"
                    dependents = json.loads(await query_redis.get(dep_key) or "[]")
                    if job_uid not in dependents:
                        dependents.append(job_uid)
                        await query_redis.set(dep_key, json.dumps(dependents))
                        # 设置依赖关系数据存活时间为24小时（确保异常情况下自动清理）
                        await query_redis.expire(dep_key, 86400)

        await query_redis.set(
            f"task_progress:{page_object.task_uid}",
            json.dumps(task_progress.model_dump()),
        )
        await query_redis.expire(f"task_progress:{page_object.task_uid}", 86400)

        return CrudResponseModel(is_success=True, message="添加成功")

    @classmethod
    async def get_job_param(cls, query_redis: asyncio_redis, job_uid: str):
        return JobSchedulerModel(
            **json.loads(await query_redis.get(f"job_param:{job_uid}") or "{}")
        )

    @classmethod
    async def get_ready_job(cls, query_redis: asyncio_redis):
        job_uid = await query_redis.spop("ready_job")
        # hack: 最后一个uid弹出后会导致删除"ready_job"
        # if job_uid and (await query_redis.ttl(f"ready_job") > 0):
        if job_uid:
            job_param = await cls.get_job_param(query_redis, job_uid)
            if job_param.job_uid:
                return job_param
        return None

    @classmethod
    async def get_all_ready_job(cls, query_redis: asyncio_redis):
        job_execute_list = []
        while True:
            job_execute = await cls.get_ready_job(query_redis)
            if job_execute:
                job_execute_list.append(job_execute)
            else:
                break
        return job_execute_list

    @classmethod
    async def execute_ready_job(cls, query_redis: asyncio_redis, query_db: AsyncSession):
        """
        执行一次定时任务service

        :param query_redis: redis对象
        :param query_db: orm对象
        :return: 执行定时任务结果
        """
        job_execute_list = await cls.get_all_ready_job(query_redis)
        if job_execute_list:
            # JobSchedulerService.remove_scheduler_job(job_uid=job_info.job_uid)
            for job_info in job_execute_list:
                job = JobLogModel(**job_info.model_dump())
                job.job_message = "任务开始执行"
                await JobLogDao.add_job_log_dao(
                    query_db, job
                )
                
            query_db.commit()
            
            async with JobSchedulerService() as job_scheduler:
                await job_scheduler.add_jobs(job_info=job_execute_list)

        return CrudResponseModel(is_success=True, message="执行成功")

    @classmethod
    async def execute_ready_job_reset(
        cls, query_redis: asyncio_redis, query_db: AsyncSession, task: TaskModel
    ):
        """
        执行一次定时任务service

        :param query_redis: redis对象
        :param query_db: orm对象
        :return: 执行定时任务结果
        """
        task.task_progress = 0
        task.run_status = "running"

        await TaskDao.edit_task_dao(
            query_db,
            task.model_dump(),
        )
        return await cls.execute_ready_job(query_redis, query_db)

    @classmethod
    async def update_task_progress(
        cls,
        query_redis: asyncio_redis,
        query_db: AsyncSession,
        task_uid: str,
        job_uid: str,
    ):
        task_progress = TaskProgressModel(
            **json.loads(await query_redis.get(f"task_progress:{task_uid}") or "{}")
        )
        task_progress.task_complated = task_progress.task_complated + 1

        # hack: 多次提交数据不一致问题
        task_object = await TaskDao.get_task_detail_by_uid(query_db, task_uid)
        if task_object.run_status == "running":
            if task_progress.task_complated < task_progress.task_len:
                await TaskDao.edit_task_dao(
                    query_db,
                    {
                        "task_uid": task_progress.task_uid,
                        "task_progress": task_progress.task_complated
                        / task_progress.task_len,
                    },
                )
                await query_redis.set(
                    f"task_progress:{task_uid}", json.dumps(task_progress.model_dump())
                )
                await query_redis.expire(f"task_progress:{task_uid}", 86400)
            else:
                await cls.del_task_config(query_redis, task_uid, query_db)
                await TaskDao.edit_task_dao(
                    query_db,
                    {
                        "task_uid": task_progress.task_uid,
                        "run_status": "complated",
                        "task_progress": 1,
                    },
                )
            await query_db.commit()

            dependents = json.loads(await query_redis.getdel(f"deps:{job_uid}") or "[]")
            # 更新所有依赖该任务的任务计数器
            for dependent in dependents:
                remaining = await query_redis.decr(
                    f"dep_count:{dependent}"
                )  # 自动减1并返回新值
                await query_redis.expire(f"dep_count:{dependent}", 86400)
                if remaining == 0:
                    await query_redis.delete(f"dep_count:{dependent}")
                    await query_redis.sadd("ready_job", dependent)
                    await query_redis.expire(f"ready_job", 3600)

    @classmethod
    async def del_task_config(
        cls, query_redis: asyncio_redis, task_uid: str, query_db: AsyncSession
    ):
        task_progress = json.loads(
            await query_redis.getdel(f"task_progress:{task_uid}") or "{}"
        )
        for job_uid in task_progress.get("task_jobs", []):
            await query_redis.delete(f"job_param:{job_uid}")
            await query_redis.delete(f"dep_count:{job_uid}")
            await query_redis.delete(f"deps:{job_uid}")

        await TaskDao.edit_task_dao(
            query_db,
            {
                "task_uid": task_progress.get("task_uid"),
                "run_status": "failed",
            },
        )

    @classmethod
    async def complete_job_services(
        cls,
        query_redis: asyncio_redis,
        completion_status: JobExecuteResponseModel,
        query_db: AsyncSession,
    ):
        job_uid = completion_status.job_uid

        # 更新进度
        job_param = JobSchedulerModel(
            **json.loads(await query_redis.getdel(f"job_param:{job_uid}") or "{}")
        )
        task_uid = job_param.task_uid

        if not completion_status.success and task_uid:
            # test: 任务执行失败，删除所有依赖该任务的任务
            await cls.del_task_config(query_redis, task_uid, query_db)
            return job_param

        if task_uid and completion_status.success:
            await cls.update_task_progress(query_redis, query_db, task_uid, job_uid)
            await cls.execute_ready_job(query_redis)

        return job_param
