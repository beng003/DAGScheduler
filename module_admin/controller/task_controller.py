from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from config.get_db import get_db
from utils.log_util import logger
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
taskController = APIRouter(prefix="/scheduler")


@taskController.get(
    "/task/get",
    response_model=TaskModel,
)
async def query_detail_task(
    request: Request,
    task_uid: str = Query(..., description="任务唯一标识"),  # 作为查询参数
    query_db: AsyncSession = Depends(get_db),
):
    task_detail_result = await TaskService.task_detail_services_by_uid(
        query_db, task_uid
    )
    logger.info(f"获取task_uid为{task_uid}的信息成功")

    return ResponseUtil.success(data=task_detail_result)


@taskController.get(
    "/task/list",
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
    "/task/add",
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
    logger.info(add_task_result.message+"，task_uid："+add_task_result.result['task_uid'])

    return ResponseUtil.success(
        msg=add_task_result.message, dict_content=add_task_result.result
    )


@taskController.post(
    "/job_completed",
    response_model=PageResponseModel,
)
async def job_completed(
    request: Request,
    job_completed: JobExecuteResponseModel,
    background_tasks: BackgroundTasks,
    query_db: AsyncSession = Depends(get_db),
):
    task_scheduler = TaskSchedulerService(request.app.state.redis, query_db)
    background_tasks.add_task(
        task_scheduler.handle_job_completion,
        job_completed.job_uid,
        job_completed.success,
        job_completed.error_detail,
    )
    return ResponseUtil.success(
        msg="记录成功", dict_content={"job_uid": job_completed.job_uid}
    )


@taskController.post("/task/start")
async def execute_system_task(
    request: Request,
    task_uid: str = Query(..., description="任务唯一标识"),  # 作为查询参数
    query_db: AsyncSession = Depends(get_db),
):
    execute_task = TaskModel(
        task_uid=task_uid,
        update_time=datetime.now(),
    )
    execute_task_result = await TaskService.execute_task_once_services(
        query_db, execute_task, request.app.state.redis
    )
    logger.info(execute_task_result.message)

    return ResponseUtil.success(
        msg=execute_task_result.message,
        dict_content={"task_uid": execute_task.task_uid},
    )
    
    # import aiohttp
    # import json
    
    # payload = json.dumps([
    #     {
    #         "job_uid": "psi3",
    #         "job_executor": "default",
    #         "invoke_target": "module_task.scheduler_test.job",
    #         "job_args": "",
    #         "job_kwargs": ""
    #     },
    #     {
    #         "job_uid": "psi4",
    #         "job_executor": "default",
    #         "invoke_target": "module_task.scheduler_test.job",
    #         "job_args": "",
    #         "job_kwargs": ""
    #     }
    # ])
    
    # headers = {'Content-Type': 'application/json'}
    
    # async with aiohttp.ClientSession() as session:
    #     try:
    #         async with session.post(
    #             "http://127.0.0.1:8088/operator/add_job",
    #             data=payload,
    #             headers=headers,
    #             ssl=False  # 自签名证书需要关闭 SSL 验证
    #         ) as response:
    #             data = await response.text()
    #             print(f"Status: {response.status}")
    #             print(f"Response: {data}")
    #     except aiohttp.ClientError as e:
    #         print(f"Request failed: {e}")

    # return ResponseUtil.success(msg="任务启动成功", dict_content={"task_uid": task_uid})

@taskController.post("/task/stop")
async def stop_task(
    request: Request,
    task_uid: str = Query(..., description="任务唯一标识"),  # 作为查询参数
    query_db: AsyncSession = Depends(get_db),
):
    await TaskService.stop_task_services(
        query_db=query_db, query_redis=request.app.state.redis, task_uid=task_uid
    )
    logger.info("任务停止成功")

    return ResponseUtil.success(msg="任务停止成功", dict_content={"task_uid": task_uid})
