from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from config.get_db import get_db
from utils.log_util import logger
import time
from module_admin.service.task_service import TaskService
from module_admin.service.job_service import TaskSchedulerService
from module_admin.entity.vo.task_vo import (
    TaskModel,
    TaskPageQueryModel,
    JobExecuteResponseModel,
)
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


# question: LoginService.get_current_user?
taskController = APIRouter(prefix="/monitor")


@taskController.get(
    "/task/{task_uid}",
    response_model=TaskModel,
)
async def query_detail_task(
    request: Request, task_uid: str, query_db: AsyncSession = Depends(get_db)
):
    task_detail_result = await TaskService.task_detail_services_by_uid(
        query_db, task_uid
    )
    logger.info(f"获取task_uid为{task_uid}的信息成功")

    return ResponseUtil.success(data=task_detail_result)


@taskController.get(
    "/task_list",
    response_model=PageResponseModel,
)
async def get_task_list(
    request: Request,
    # note: as_query
    # 这里的task_page_query是一个对象，不是字典
    # 通过as_query装饰器将请求参数转换为TaskPageQueryModel对象
    task_page_query: TaskPageQueryModel = Depends(TaskPageQueryModel.as_query),
    # task_page_query: TaskPageQueryModel = TaskPageQueryModel.as_query,
    # task_page_query: TaskPageQueryModel.as_query,
    query_db: AsyncSession = Depends(get_db),
):
    # 获取分页数据
    notice_page_query_result = await TaskService.get_task_list_services(
        query_db, task_page_query, is_page=True
    )
    logger.info("获取成功")

    return ResponseUtil.success(model_content=notice_page_query_result)


@taskController.post(
    "/add_task",
    response_model=PageResponseModel,
)
async def add_task(
    request: Request,
    add_task: TaskModel,
    query_db: AsyncSession = Depends(get_db),
):
    add_task.create_time = datetime.now()
    add_task.update_time = datetime.now()
    add_task_result = await TaskService.add_task_services(
        query_db, request.app.state.redis, add_task
    )
    logger.info(add_task_result.message)

    return ResponseUtil.success(
        msg=add_task_result.message,
    )


@taskController.post(
    "/job_complated",
    response_model=PageResponseModel,
)
async def job_complated(
    request: Request,
    job_complated: JobExecuteResponseModel,
    query_db: AsyncSession = Depends(get_db),
):
    task_scheduler = TaskSchedulerService(request.app.state.redis, query_db)
    await task_scheduler.handle_job_completion(job_complated.job_uid, job_complated.success)
    return ResponseUtil.success(msg="记录成功")


@taskController.put(
    "/task/start/{task_uid}",
)
async def execute_system_task(
    request: Request,
    task_uid: str,
    query_db: AsyncSession = Depends(get_db),
):
    execute_task = TaskModel(
        task_uid=task_uid,
        update_ime=datetime.now(),
    )
    execute_task_result = await TaskService.execute_task_once_services(
        query_db, execute_task, request.app.state.redis
    )
    logger.info(execute_task_result.message)

    return ResponseUtil.success(
        msg=execute_task_result.message, data={"task_uid": execute_task.task_uid}
    )