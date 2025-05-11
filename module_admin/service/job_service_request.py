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
from module_admin.dao.task_dao import TaskDao
from module_admin.dao.job_log_dao import JobLogDao
import httpx
import asyncio
from typing import List, Optional, Dict
from datetime import datetime
from utils.log_util import logger


# 定义常量管理Redis键名
class RedisKeys:
    JOB_PARAM = "job_param:{job_uid}"
    DEP_COUNT = "dep_count:{job_uid}"
    DEPS = "deps:{job_uid}"
    TASK_PROGRESS = "task_progress:{task_uid}"
    READY_JOBS = "ready_job"


class JobSchedulerService:
    """
    任务相关方法, 算子层接口
    """

    def __init__(
        self,
        # base_url: str = "http://127.0.0.1:8088/dev-api",
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
        # self.client is removed

    # __aenter__, __aexit__, and close methods are removed as self.client is removed

    async def _send_request(
        self, method: str, endpoint: str, params: Dict = None, json: List[Dict] = None
    ) -> List[JobExecuteResponseModel]:
        """核心请求方法（含重试逻辑）"""
        full_url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        for attempt in range(self.max_retries):
            try:
                response = httpx.request(
                    method=method,
                    url=full_url,
                    params=params,
                    json=json,
                    timeout=self.timeout,
                )
                response.raise_for_status()  # Raises an exception for 4XX/5XX responses
                # Assuming the response structure is {"data": [...]}
                response_data = response.json()
                if "data" in response_data and isinstance(response_data["data"], list):
                    return [
                        JobExecuteResponseModel(**item)
                        for item in response_data["data"]
                    ]
                # Handle cases where "data" might be missing or not a list, or adjust as per actual API contract
                logger.error(
                    f"API response format error for {method} {full_url}: 'data' field is missing or not a list. Response: {response_data}"
                )
                raise RuntimeError("API响应格式错误: 'data'字段缺失或非列表")

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.error(
                    f"API request failed on attempt {attempt + 1}/{self.max_retries} for {method} {full_url}: {str(e)}"
                )
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"API请求失败: {str(e)}") from e
                await asyncio.sleep(2**attempt)  # Exponential backoff
            except Exception as e:  # Catch other potential errors like JSONDecodeError
                logger.error(
                    f"An unexpected error occurred on attempt {attempt + 1}/{self.max_retries} for {method} {full_url}: {str(e)}"
                )
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"API请求发生未知错误: {str(e)}") from e
                await asyncio.sleep(2**attempt)
        # This part should ideally not be reached if max_retries is > 0
        # because the loop should either return or raise an exception.
        # Adding a fallback raise for safety, though.
        raise RuntimeError("API请求在所有重试后均失败，且未抛出预期异常")

    async def add_jobs(
        self, job_info: List[JobExecuteModel]
    ) -> List[JobExecuteResponseModel]:
        """
        批量添加任务（对应/add_job接口）
        :param job_info: 任务参数列表. Changed from 'tasks' to 'job_info' to match usage.
        :return: 任务执行结果列表
        """
        response = await self._send_request(
            method="POST",
            endpoint="/operator/add_job",  # Ensure endpoint starts with / if base_url doesn't end with /
            json=[task.model_dump() for task in job_info],
        )
        # Corrected to return the list of response models as per type hint
        
        add_status = all([job.success for job in response])
        return add_status

    async def stop_jobs(self, job_uids: List[str]) -> List[JobExecuteResponseModel]:
        """
        批量停止任务（对应/stop_job接口）
        :param job_uids: 任务ID列表
        :return: 任务停止结果列表
        """
        response = await self._send_request(
            method="GET",
            endpoint="/operator/stop_job",
            params={"job_uids": job_uids},  # Ensure endpoint starts with /
        )
        # Corrected: _send_request returns List[JobExecuteResponseModel]
        # The assert response.status_code == 200 was incorrect as response is a list.
        # The return True was incorrect as the type hint is List[JobExecuteResponseModel].
        return response

    # async def close(self): # Removed as self.client is removed
    #     """关闭连接池"""
    #     await self.client.aclose()


class RedisJobStore:
    """负责所有Redis数据操作"""

    def __init__(self, redis: asyncio_redis):
        self.redis = redis

    async def store_job(self, job: JobSchedulerModel):
        """存储任务参数"""
        key = RedisKeys.JOB_PARAM.format(job_uid=job.job_uid)
        await self.redis.set(key, json.dumps(job.model_dump()))
        await self.redis.expire(key, 86400)

    async def get_job(self, job_uid: str) -> JobSchedulerModel:
        """获取任务参数"""
        data = await self.redis.get(RedisKeys.JOB_PARAM.format(job_uid=job_uid))
        return JobSchedulerModel(**json.loads(data)) if data else None

    async def add_to_ready_queue(self, job_uid: str):
        """加入就绪队列"""
        await self.redis.sadd(RedisKeys.READY_JOBS, job_uid)
        await self.redis.expire(RedisKeys.READY_JOBS, 3600)

    async def pop_ready_job(self) -> Optional[str]:
        """取出一个就绪任务"""
        return await self.redis.spop(RedisKeys.READY_JOBS)

    async def get_all_ready_jobs(self) -> List[str]:
        """获取所有就绪任务"""
        job_uids = []

        while True:
            job_uid = await self.pop_ready_job()
            if not job_uid:
                break
            job_uids.append(job_uid)

        return job_uids

    async def init_dep_count(self, job_uid: str, count: int):
        """初始化依赖计数器"""
        key = RedisKeys.DEP_COUNT.format(job_uid=job_uid)
        await self.redis.set(key, count)
        await self.redis.expire(key, 86400)

    async def decrement_dep_count(self, job_uid: str) -> int:
        """减少依赖计数器并返回新值"""
        return await self.redis.decr(RedisKeys.DEP_COUNT.format(job_uid=job_uid))

    async def add_dependent(self, dep_job_uid: str, job_uid: str):
        """添加反向依赖关系"""
        dep_key = RedisKeys.DEPS.format(job_uid=dep_job_uid)
        dependents = await self.get_dependents(dep_job_uid)
        if job_uid not in dependents:
            dependents.append(job_uid)
            await self.redis.set(dep_key, json.dumps(dependents))
            # 设置依赖关系数据存活时间为24小时（确保异常情况下自动清理）
            await self.redis.expire(dep_key, 86400)

    async def get_dependents(self, job_uid: str) -> List[str]:
        """获取所有依赖此任务的任务列表"""
        data = await self.redis.get(RedisKeys.DEPS.format(job_uid=job_uid))
        return json.loads(data) if data else []

    async def save_task_progress(self, progress: TaskProgressModel):
        """保存任务进度"""
        key = RedisKeys.TASK_PROGRESS.format(task_uid=progress.task_uid)
        await self.redis.set(key, json.dumps(progress.model_dump()))
        await self.redis.expire(key, 86400)

    async def get_task_progress(self, task_uid: str) -> TaskProgressModel:
        """获取任务进度"""
        data = await self.redis.get(RedisKeys.TASK_PROGRESS.format(task_uid=task_uid))
        return TaskProgressModel(**json.loads(data)) if data else None

    async def cleanup_task(self, task_uid: str):
        """清理任务相关数据"""
        progress = await self.get_task_progress(task_uid)
        if not progress:
            return

        # 删除所有关联的job数据
        for job_uid in progress.task_jobs:
            await self.redis.delete(RedisKeys.JOB_PARAM.format(job_uid=job_uid))
            await self.redis.delete(RedisKeys.DEP_COUNT.format(job_uid=job_uid))
            await self.redis.delete(RedisKeys.DEPS.format(job_uid=job_uid))
            await self.redis.srem(RedisKeys.READY_JOBS, job_uid)  # 新增：从就绪队列移除

        # 删除任务进度
        await self.redis.delete(RedisKeys.TASK_PROGRESS.format(task_uid=task_uid))


class DependencyManager:
    """管理任务依赖关系"""

    def __init__(self, redis_store: RedisJobStore):
        self.redis = redis_store

    async def register_dependencies(self, job: JobSchedulerModel):
        """注册任务依赖"""
        dependencies = json.loads(job.job_dependencies)
        if not dependencies:
            await self.redis.add_to_ready_queue(job.job_uid)
            return

        await self.redis.init_dep_count(job.job_uid, len(dependencies))
        for dep_job_uid in dependencies:
            await self.redis.add_dependent(dep_job_uid, job.job_uid)

    async def handle_completion(self, completed_job_uid: str):
        """处理任务完成后的依赖更新"""
        dependents = await self.redis.get_dependents(completed_job_uid)
        for job_uid in dependents:
            remaining = await self.redis.decrement_dep_count(job_uid)
            if remaining == 0:
                await self.redis.add_to_ready_queue(job_uid)


class TaskProgressTracker:
    """管理任务进度跟踪"""

    def __init__(self, redis_store: RedisJobStore, db: AsyncSession):
        self.redis = redis_store
        self.db = db

    async def initialize(self, task: TaskModel) -> TaskProgressModel:
        """初始化任务进度"""
        progress = TaskProgressModel(
            task_uid=task.task_uid,
            run_status="running",
            task_completed=0,
            task_len=len(task.task_yaml),
            task_jobs=[job.job_uid for job in task.task_yaml],
        )
        await self.redis.save_task_progress(progress)
        await self._update_db(
            task_uid=task.task_uid,
            updates={"run_status": "running", "task_progress": 0},
        )
        return progress

    async def increment_progress(self, task_uid: str):
        """增加完成计数并更新状态"""
        progress = await self.redis.get_task_progress(task_uid)
        if not progress:
            return

        progress.task_completed += 1
        if progress.task_completed == progress.task_len:
            await self.mark_completed(task_uid)
        else:
            await self.redis.save_task_progress(progress)
            await self._update_db(
                task_uid=task_uid,
                updates={"task_progress": progress.task_completed / progress.task_len},
            )

    async def mark_completed(self, task_uid: str):
        """标记任务完成"""
        await self.redis.cleanup_task(task_uid)
        await self._update_db(
            task_uid=task_uid, updates={"run_status": "completed", "task_progress": 1.0}
        )

    async def mark_failed(self, task_uid: str):
        """标记任务失败"""
        await self.redis.cleanup_task(task_uid)
        await self._update_db(task_uid=task_uid, updates={"run_status": "failed"})

    async def _update_db(self, task_uid: str, updates: dict):
        """更新数据库状态"""
        await TaskDao.edit_task_dao(self.db, {"task_uid": task_uid, **updates})
        await self.db.commit()


class JobExecutor:
    """任务执行器"""

    def __init__(self, redis_store: RedisJobStore, db: AsyncSession):
        self.redis = redis_store
        self.db = db

    async def execute_all_ready_jobs(self):
        """执行所有就绪任务"""
        # while True:

        #     job_uid = await self.redis.pop_ready_job()
        #     if not job_uid:
        #         break
        #     await self.execute_one_ready_job(job_uid)

        job_uids = await self.redis.get_all_ready_jobs()
        if not job_uids:
            return

        job_executor = []
        for job_uid in job_uids:
            await self.add_job_log(job_uid, "任务开始执行", "0", commit=False)
            job_param = await self.redis.get_job(job_uid)
            job_executor.append(JobExecuteModel(**job_param.model_dump()))

        await self.db.commit()

        scheduler = JobSchedulerService()
        await scheduler.add_jobs(job_executor)

    async def add_job_log(
        self, job_uid: str, job_message: str, status: str, commit: bool = True
    ):
        """添加任务日志"""
        job: JobSchedulerModel = await self.redis.get_job(job_uid)
        # 记录日志
        log = JobLogModel(
            **job.model_dump(),
            job_message=job_message,
            status=status,
            create_time=datetime.now(),
        )
        await JobLogDao.add_job_log_dao(self.db, log)
        if commit:
            await self.db.commit()


class TaskSchedulerService:
    """任务调度入口类"""

    def __init__(self, redis: asyncio_redis, db: AsyncSession):
        self.redis_store = RedisJobStore(redis)
        self.dependency_mgr = DependencyManager(self.redis_store)
        self.progress_tracker = TaskProgressTracker(self.redis_store, db)
        self.executor = JobExecutor(self.redis_store, db)

    async def add_task(self, task: TaskModel):
        """添加新任务"""
        await self.progress_tracker.initialize(task)
        for job_data in task.task_yaml:
            job = JobSchedulerModel(**job_data.model_dump(), task_uid=task.task_uid)
            await self.redis_store.store_job(job)
            await self.dependency_mgr.register_dependencies(job)

    async def handle_job_completion(self, job_uid: str, success: bool):
        """处理任务完成事件"""
        job = await self.redis_store.get_job(job_uid)
        if not job or not job.task_uid:
            return

        if success:
            # 记录日志
            await self.executor.add_job_log(job_uid, "任务执行成功", "0")
            await self.dependency_mgr.handle_completion(job_uid)
            await self.progress_tracker.increment_progress(job.task_uid)
            await self.executor.execute_all_ready_jobs()  # 触发后续任务执行
        else:
            # todo: 记录日志错误信息
            await self.executor.add_job_log(job_uid, "任务执行失败", "1")
            await self.progress_tracker.mark_failed(job.task_uid)

    async def stop_task(self, task_uid: str):
        """停止指定任务流"""
        progress = await self.redis_store.get_task_progress(task_uid)
        if not progress:
            raise ValueError(f"任务流 {task_uid} 不存在或已完成")

        # 停止所有关联任务
        async with JobSchedulerService() as scheduler:
            await scheduler.stop_jobs(progress.task_jobs)  # 调用已有停止接口

        # 清理Redis数据
        await self.redis_store.cleanup_task(task_uid)

        # 更新数据库状态
        await self.progress_tracker._update_db(
            task_uid=task_uid,
            updates={"run_status": "stopped", "update_time": datetime.now()},
        )
