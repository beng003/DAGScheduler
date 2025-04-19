from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.task_do import SysJobLog
from module_admin.entity.vo.task_vo import JobLogModel


class JobLogDao:
    """
    任务流日志管理模块数据库操作层
    """

    @classmethod
    async def add_job_log_dao(cls, db: AsyncSession, task_log: JobLogModel):
        """
        新增定时任务流日志数据库操作

        :param db: orm对象
        :param task_log: 定时任务流日志对象
        :return:
        """
        db_task_log = SysJobLog(**task_log.model_dump())
        db.add(db_task_log)
        await db.flush()

        return db_task_log