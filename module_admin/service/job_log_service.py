from sqlalchemy.orm import Session
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.task_vo import JobLogModel
from module_admin.dao.job_log_dao import JobLogDao


class JobLogService:
    """
    任务日志管理模块服务层
    """

    @classmethod
    def add_job_log_services(cls, query_db: Session, page_object: JobLogModel):
        """
        新增定时任务日志信息service

        :param query_db: orm对象
        :param page_object: 新增定时任务日志对象
        :return: 新增定时任务日志校验结果
        """
        try:
            JobLogDao.add_job_log_dao(query_db, page_object)
            query_db.commit()
            result = dict(is_success=True, message='新增成功')
        except Exception as e:
            query_db.rollback()
            result = dict(is_success=False, message=str(e))

        return CrudResponseModel(**result)