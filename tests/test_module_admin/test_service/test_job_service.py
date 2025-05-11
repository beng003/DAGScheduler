# import pytest
# from tests.test_data import job_list
# from module_admin.service.job_service import JobSchedulerService
# from module_admin.entity.vo.task_vo import JobExecuteModel


# class TestJobSchedulerService:
#     job_info = [JobExecuteModel(**job) for job in job_list]
#     scheduler = JobSchedulerService()
    
#     @pytest.mark.job
#     @pytest.mark.anyio
#     async def test_add_jobs(cls):
#         add_status = await cls.scheduler.add_jobs(job_info=cls.job_info)
#         assert add_status is True
