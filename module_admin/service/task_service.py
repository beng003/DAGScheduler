from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from config.constant import CommonConstant
from exceptions.exception import ServiceException
from module_admin.dao.task_dao import TaskDao
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.task_vo import (
    DeleteTaskModel,
    EditTaskModel,
    TaskModel,
    TaskPageQueryModel,
)
from redis.asyncio import Redis as asyncio_redis
from module_admin.service.job_service import TaskSchedulerService
from utils.common_util import SnakeCaseUtil
import uuid


class TaskService:
    """
    定时任务流管理模块服务层
    """

    @classmethod
    async def get_task_list_services(
        cls,
        query_db: AsyncSession,
        query_object: TaskPageQueryModel,
        is_page: bool = False,
    ):
        """
        获取定时任务流列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 定时任务流列表信息对象
        """
        task_list_result = await TaskDao.get_task_list(query_db, query_object, is_page)

        return task_list_result

    # hack: 定时任务是否存在还是子任务是否存在？
    @classmethod
    async def check_task_unique_services(
        cls, query_db: AsyncSession, page_object: TaskModel
    ):
        """
        校验定时任务流是否存在service

        :param query_db: orm对象
        :param page_object: 定时任务流对象
        :return: 校验结果
        """
        task_uid = -1 if page_object.task_uid is None else page_object.task_uid
        task = await TaskDao.get_task_detail_by_info(query_db, page_object)
        if task and task.task_uid != task_uid:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_task_services(
        cls, query_db: AsyncSession, query_redis: asyncio_redis, page_object: TaskModel
    ):
        """
        新增定时任务流信息service

        :param query_db: orm对象
        :param page_object: 新增定时任务流对象
        :return: 新增定时任务流校验结果
        """
        page_object.task_uid = str(uuid.uuid4())

        if not await cls.check_task_unique_services(query_db, page_object):
            raise ServiceException(
                message=f"新增定时任务流{page_object.task_name}失败，定时任务流已存在"
            )
        else:
            try:

                add_task = await TaskDao.add_task_dao(query_db, page_object)
                task_info = await cls.task_detail_services_by_uid(
                    query_db, add_task.task_uid
                )

                # todo: 添加任务执行代码
                if task_info.status == '0':
                    task_scheduler = TaskSchedulerService(query_redis, query_db)
                    await task_scheduler.add_task(task_info)
                    await task_scheduler.executor.execute_all_ready_jobs()

                await query_db.commit()
                result = dict(
                    is_success=True,
                    message="新增成功",
                    result={"task_uid": task_info.task_uid},
                )
            except Exception as e:
                await query_db.rollback()
                raise e

        return CrudResponseModel(**result)

    # # todo: 编辑任务流信息
    # @classmethod
    # async def edit_task_services(
    #     cls, query_db: AsyncSession, page_object: EditTaskModel
    # ):
    #     """
    #     编辑定时任务流信息service

    #     :param query_db: orm对象
    #     :param page_object: 编辑定时任务流对象
    #     :return: 编辑定时任务流校验结果
    #     """
    #     edit_task = page_object.model_dump(exclude_unset=True)
    #     if page_object.type == "status":
    #         del edit_task["type"]
    #     task_info = await cls.task_detail_services(query_db, page_object.task_uid)
    #     if task_info:
    #         if page_object.type != "status":
    #             if not CronUtil.validate_cron_expression(page_object.cron_expression):
    #                 raise ServiceException(
    #                     message=f"修改定时任务流{page_object.task_name}失败，Cron表达式不正确"
    #                 )
    #             elif StringUtil.contains_ignore_case(
    #                 page_object.invoke_target, CommonConstant.LOOKUP_RMI
    #             ):
    #                 raise ServiceException(
    #                     message=f"修改定时任务流{page_object.task_name}失败，目标字符串不允许rmi调用"
    #                 )
    #             elif StringUtil.contains_any_ignore_case(
    #                 page_object.invoke_target,
    #                 [CommonConstant.LOOKUP_LDAP, CommonConstant.LOOKUP_LDAPS],
    #             ):
    #                 raise ServiceException(
    #                     message=f"修改定时任务流{page_object.task_name}失败，目标字符串不允许ldap(s)调用"
    #                 )
    #             elif StringUtil.contains_any_ignore_case(
    #                 page_object.invoke_target,
    #                 [CommonConstant.HTTP, CommonConstant.HTTPS],
    #             ):
    #                 raise ServiceException(
    #                     message=f"修改定时任务流{page_object.task_name}失败，目标字符串不允许http(s)调用"
    #                 )
    #             elif StringUtil.startswith_any_case(
    #                 page_object.invoke_target, JobConstant.JOB_ERROR_LIST
    #             ):
    #                 raise ServiceException(
    #                     message=f"修改定时任务流{page_object.task_name}失败，目标字符串存在违规"
    #                 )
    #             elif not StringUtil.startswith_any_case(
    #                 page_object.invoke_target, JobConstant.JOB_WHITE_LIST
    #             ):
    #                 raise ServiceException(
    #                     message=f"修改定时任务流{page_object.task_name}失败，目标字符串不在白名单内"
    #                 )
    #             elif not await cls.check_task_unique_services(query_db, page_object):
    #                 raise ServiceException(
    #                     message=f"修改定时任务流{page_object.task_name}失败，定时任务流已存在"
    #                 )
    #         try:
    #             await TaskDao.edit_task_dao(query_db, edit_task)
    #             SchedulerUtil.remove_scheduler_task(task_uid=edit_task.get("task_uid"))
    #             if edit_task.get("status") == "0":
    #                 task_info = await cls.task_detail_services(
    #                     query_db, edit_task.get("task_uid")
    #                 )
    #                 SchedulerUtil.add_scheduler_task(task_info=task_info)
    #             await query_db.commit()
    #             return CrudResponseModel(is_success=True, message="更新成功")
    #         except Exception as e:
    #             await query_db.rollback()
    #             raise e
    #     else:
    #         raise ServiceException(message="定时任务流不存在")

    # todo: 执行任务流一次
    @classmethod
    async def execute_task_once_services(
        cls, query_db: AsyncSession, page_object: TaskModel, query_redis: asyncio_redis
    ):
        """
        执行一次定时任务流service

        :param query_db: orm对象
        :param page_object: 定时任务流对象
        :return: 执行一次定时任务流结果
        """
        # for job in page_object.task_yaml:
        #     SchedulerUtil.remove_scheduler_job(job_uid=job.job_uid)
        task_info = await cls.task_detail_services_by_uid(
            query_db, page_object.task_uid
        )
        task_info.update_time = page_object.update_time
        task_info.update_by = page_object.update_by
        if task_info:
            task_scheduler = TaskSchedulerService(query_redis, query_db)
            await task_scheduler.add_task(task_info)
            await task_scheduler.executor.execute_all_ready_jobs()

            await query_db.commit()
            return CrudResponseModel(is_success=True, message="执行成功")
        else:
            raise ServiceException(message="定时任务流不存在")

    @classmethod
    async def stop_task_services(
        cls,
        query_db: AsyncSession,
        query_redis: asyncio_redis,
        task_uid: str,
    ) -> CrudResponseModel:
        """
        停止任务流service

        :param query_db: 数据库会话
        :param task_uid: 任务流UID
        :param update_by: 操作人
        :return: 操作结果
        """
        task_info = await cls.task_detail_services_by_uid(query_db, task_uid)
        if not task_info:
            raise ServiceException(message="任务流不存在")

        scheduler = TaskSchedulerService(query_redis, query_db)
        try:
            await scheduler.stop_task(task_uid)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message="已终止任务流")
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"终止任务流失败: {str(e)}")

    @classmethod
    async def delete_task_services(
        cls, query_db: AsyncSession, page_object: DeleteTaskModel
    ):
        """
        删除定时任务流信息service

        :param query_db: orm对象
        :param page_object: 删除定时任务流对象
        :return: 删除定时任务流校验结果
        """
        if page_object.task_uids:
            task_uid_list = page_object.task_uids.split(",")
            try:
                for task_uid in task_uid_list:
                    await TaskDao.delete_task_dao(query_db, TaskModel(taskUid=task_uid))
                    # todo: 从定时任务中删除对应的子任务
                    # SchedulerUtil.remove_scheduler_task(task_uid=task_uid)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message="删除成功")
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message="传入定时任务流id为空")

    @classmethod
    async def task_detail_services_by_uid(cls, query_db: AsyncSession, task_uid: str):
        """
        获取定时任务流详细信息service

        :param query_db: orm对象
        :param task_uid: 定时任务流uid
        :return: 定时任务流id对应的信息
        """
        task = await TaskDao.get_task_detail_by_uid(query_db, task_uid=task_uid)

        if task:
            result = TaskModel(**SnakeCaseUtil.transform_result(task))
        else:
            result = TaskModel(**dict())

        return result
