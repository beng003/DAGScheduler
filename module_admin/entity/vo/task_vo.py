from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size
from typing import Literal, Optional, List
from module_admin.annotation.pydantic_annotation import as_query
import json
from utils.common_util import SnakeCaseUtil


class JobExecuteModel(BaseModel):
    """
    定时任务执行模型
    """

    model_config = ConfigDict(
        alias_generator=SnakeCaseUtil.camel_to_snake, from_attributes=True
    )

    job_uid: Optional[str] = Field(
        default=None, max_length=64, description="任务UID，唯一标识"
    )
    job_executor: str = Field(
        default="default", max_length=64, description="任务执行器"
    )
    invoke_target: Optional[str] = Field(
        default=None, max_length=500, description="调用目标字符串"
    )
    job_args: Optional[str] = Field(
        default=None, max_length=255, description="位置参数"
    )
    job_kwargs: Optional[str] = Field(
        default=None, max_length=2000, description="关键字参数"
    )

    # note: @NotBlank：验证调用目标字符串不能为空（非空校验）
    # @Size：验证字符串长度在0-500字符之间（长度校验）
    # 方法返回字段值的同时会自动触发装饰器的验证逻辑
    @NotBlank(field_name="invoke_target", message="调用目标字符串不能为空")
    @Size(
        field_name="invoke_target",
        min_length=0,
        max_length=500,
        message="调用目标字符串长度不能超过500个字符",
    )
    def get_invoke_target(self):
        return self.invoke_target

    def validate_fields(self):
        self.get_invoke_target()

class JobModel(JobExecuteModel):
    """
    定时任务模型
    """
    model_config = ConfigDict(
        alias_generator=SnakeCaseUtil.camel_to_snake, from_attributes=True
    )
    
    job_name: Optional[str] = Field(default=None, description="任务名称")
    job_parties: Optional[str] = Field(
        default=None, max_length=128, description="任务参与方"
    )
    job_dependencies: Optional[str] = Field(
        default=None,
        max_length=2560,
        description="任务依赖关系, 包含任务流内的任务id",
    )

class JobSchedulerModel(JobModel):
    model_config = ConfigDict(
        alias_generator=SnakeCaseUtil.camel_to_snake,
        from_attributes=True,
        extra="ignore",  # 可选值：'allow' | 'ignore' | 'forbid'
        frozen=False,  # 是否允许修改实例属性
    )

    task_uid: Optional[str] = Field(
        default=None, max_length=64, description="任务所属任务流UID，唯一标识"
    )





class JobExecuteResponseModel(BaseModel):
    """
    定时任务执行模型
    """

    model_config = ConfigDict(
        alias_generator=SnakeCaseUtil.camel_to_snake, from_attributes=True
    )

    job_uid: Optional[str] = Field(
        default=None, max_length=64, description="任务UID，唯一标识"
    )
    success: bool = Field(default=False, description="是否成功")
    error_detail: Optional[str] = Field(default=None, description="错误详情")


class TaskModel(BaseModel):
    """
    定时任务流模型
    """

    model_config = ConfigDict(
        alias_generator=SnakeCaseUtil.camel_to_snake, from_attributes=True
    )

    task_uid: Optional[str] = Field(
        default=None, max_length=64, description="任务流UID，唯一标识"
    )
    task_name: Optional[str] = Field(default=None, description="任务流名称")
    task_initiator: Optional[str] = Field(default=None, description="任务流参与方")
    task_group: Optional[str] = Field(
        default="default", max_length=64, description="任务流组名(mysql/redis)"
    )

    task_yaml: List[JobModel] = Field(
        default=[], description="任务流中的任务依赖关系, 包含任务流内的任务id"
    )
    concurrent: Optional[str] = Field(
        default="1", description="是否并发执行（0允许 1禁止）"
    )
    cron_expression: Optional[str] = Field(
        default="", max_length=255, description="定时策略cron执行表达式"
    )
    misfire_policy: Optional[str] = Field(
        default="3", description="计划执行错误策略（1立即执行 2执行一次 3放弃执行）"
    )
    status: Optional[str] = Field(default="1", description="定时状态（0正常 1暂停）")
    run_status: Optional[str] = Field(default="not started", description="任务执行状态")
    task_progress: Optional[float] = Field(
        default=0, description="任务流执行进度（0未开始 -1失败 1已完成）"
    )
    priority: Optional[str] = Field(
        default="0",
        max_length=1,
        description="任务优先级（默认为0, 数值越大优先级越高）",
    )
    create_by: Optional[str] = Field(default=None, description="创建者")
    create_time: Optional[datetime] = Field(default=None, description="创建时间")
    update_by: Optional[str] = Field(default=None, description="更新者")
    update_time: Optional[datetime] = Field(default=None, description="更新时间")
    remark: Optional[str] = Field(default=None, max_length=500, description="备注信息")

    @NotBlank(field_name="cron_expression", message="Cron执行表达式不能为空")
    @Size(
        field_name="cron_expression",
        min_length=0,
        max_length=255,
        message="Cron执行表达式不能超过255个字符",
    )
    def get_cron_expression(self):
        return self.cron_expression

    # todo: 添加环验证
    @field_validator("task_yaml")
    def validate_dependencies(cls, value: List[JobModel]):
        task_uids = {job.job_uid for job in value if job.job_uid}
        for job in value:
            job_dependencies = json.loads(job.job_dependencies or "[]")
            if job_dependencies:
                for dep_uid in job_dependencies:
                    if dep_uid not in task_uids:
                        raise ValueError(f"任务{job.job_name}依赖的任务{dep_uid}不存在")
        return value

    def validate_fields(self):
        self.get_cron_expression()


class TaskProgressModel(BaseModel):
    """
    定时任务流进度模型
    """

    model_config = ConfigDict(
        alias_generator=SnakeCaseUtil.camel_to_snake, from_attributes=True
    )

    task_uid: Optional[str] = Field(
        default=None, max_length=64, description="任务流UID，唯一标识"
    )
    run_ststus: Optional[str] = Field(default="not started", description="任务执行状态")
    task_completed: Optional[int] = Field(default=0, description="任务完成数量")
    task_len: Optional[int] = Field(default=0, description="任务总数量")
    task_jobs: Optional[List[str]] = Field(default=[], description="任务流中的任务uid")


class JobLogModel(JobModel):
    """
    定时任务调度日志表对应pydantic模型
    """

    model_config = ConfigDict(
        alias_generator=SnakeCaseUtil.camel_to_snake, from_attributes=True
    )

    job_log_id: Optional[int] = Field(default=None, description="任务日志ID")
    task_uid: Optional[str] = Field(default=None, description="任务流UID，唯一标识")
    job_message: Optional[str] = Field(default=None, description="日志信息")
    status: Optional[Literal["0", "1"]] = Field(
        default=None, description="执行状态（0正常 1失败）"
    )
    exception_info: Optional[str] = Field(default=None, description="异常信息")
    create_time: Optional[datetime] = Field(default=None, description="创建时间")


class TaskLogModel(BaseModel):
    """
    定时任务流调度日志表对应pydantic模型
    """

    model_config = ConfigDict(
        alias_generator=SnakeCaseUtil.camel_to_snake, from_attributes=True
    )

    task_log_id: Optional[int] = Field(default=None, description="任务流日志ID")
    task_uid: str = Field(default=None, max_length=64, description="任务流UID")
    task_name: str = Field(default=None, max_length=64, description="任务流名称")
    task_initiator: Optional[str] = Field(default=None, description="任务流参与方")
    task_group: Optional[str] = Field(
        default="default", max_length=64, description="任务流组名(mysql/redis)"
    )
    task_trigger: str = Field(default="", max_length=255, description="任务触发器")
    task_message: Optional[str] = Field(None, max_length=500, description="日志信息")
    exception_info: str = Field(default="", max_length=2000, description="异常信息")
    create_time: Optional[datetime] = Field(default=None, description="创建时间")


class TaskQueryModel(BaseModel):
    """
    定时任务管理不分页查询模型
    """

    model_config = ConfigDict(
        alias_generator=SnakeCaseUtil.camel_to_snake, from_attributes=True
    )

    task_uid: Optional[str] = Field(
        default=None, max_length=64, description="任务流UID，唯一标识"
    )
    task_name: Optional[str] = Field(default=None, description="任务流名称")
    task_initiator: Optional[str] = Field(default=None, description="任务流参与方")
    task_group: Optional[str] = Field(
        default="default", max_length=64, description="任务流组名(mysql/redis)"
    )

    concurrent: Optional[str] = Field(
        default="1", description="是否并发执行（0允许 1禁止）"
    )
    cron_expression: Optional[str] = Field(
        default="", max_length=255, description="定时策略cron执行表达式"
    )
    misfire_policy: Optional[str] = Field(
        default="3", description="计划执行错误策略（1立即执行 2执行一次 3放弃执行）"
    )
    status: Optional[str] = Field(default="1", description="定时状态（0正常 1暂停）")
    task_progress: Optional[int] = Field(
        default=0, description="任务流执行进度（0未开始 -1失败 100已完成）"
    )
    priority: Optional[str] = Field(
        default="0",
        max_length=1,
        description="任务优先级（默认为0, 数值越大优先级越高）",
    )
    create_by: Optional[str] = Field(default=None, description="创建者")
    create_time: Optional[datetime] = Field(default=None, description="创建时间")
    update_by: Optional[str] = Field(default=None, description="更新者")
    update_time: Optional[datetime] = Field(default=None, description="更新时间")
    remark: Optional[str] = Field(default=None, max_length=500, description="备注信息")

    begin_time: Optional[str] = Field(default=None, description="开始时间")
    end_time: Optional[str] = Field(default=None, description="结束时间")


# note: @as_query装饰器将类转换为查询模型
# 查询参数适配
# 将Pydantic模型转换为FastAPI能识别的查询参数格式
# 自动处理继承自父类 JobQueryModel 的字段
# 支持通过URL参数接收查询条件，例如：
# /jobs?pageNum=2&pageSize=20&jobName=test
# question: 为什么是JobQueryModel的子类JobPageQueryModel？
@as_query
class TaskPageQueryModel(TaskQueryModel):
    """
    定时任务管理分页查询模型
    """

    page_num: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=10, description="每页记录数")


class EditTaskModel(TaskModel):
    """
    编辑定时任务模型
    """

    type: Optional[str] = Field(default=None, description="操作类型")


class TaskLogQueryModel(TaskLogModel):
    """
    定时任务日志不分页查询模型
    """

    begin_time: Optional[str] = Field(default=None, description="开始时间")
    end_time: Optional[str] = Field(default=None, description="结束时间")


@as_query
class TaskLogPageQueryModel(TaskLogQueryModel):
    """
    定时任务日志管理分页查询模型
    """

    page_num: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=10, description="每页记录数")


class DeleteTaskModel(BaseModel):
    """
    删除定时任务模型
    """

    model_config = ConfigDict(
        alias_generator=SnakeCaseUtil.camel_to_snake, from_attributes=True
    )

    task_uids: str = Field(description="需要删除的定时任务ID")
