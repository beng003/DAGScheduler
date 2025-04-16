from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from config.get_db import get_db
from utils.log_util import logger
from utils.response_util import ResponseUtil
import time

# question: LoginService.get_current_user?
taskController = APIRouter(
    prefix="/monitor"
)

@taskController.get(
    "/task/{task_uid}/run_status",
)
async def get_system_task_list(
    request: Request,
    task_uid: str,
    query_db: AsyncSession = Depends(get_db),
):
    # 获取分页数据
    time.sleep(2)
    logger.info("获取成功")

    return ResponseUtil.success(msg = f"获取成功{task_uid}", data = {"taskUid": task_uid, "runStatus": "success", "taskProgress": 100})