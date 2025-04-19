from config.database import Base
from sqlalchemy import Column, BigInteger, String, DateTime, Enum, Index, CHAR, text, JSON
from sqlalchemy.dialects.mysql import FLOAT


class SysTask(Base):
    __tablename__ = 'sys_task'
    
    task_uid = Column(String(64), primary_key=True, unique=True, nullable=False, comment='任务流UID，唯一标识')
    task_name = Column(String(64), default='', comment='任务流名称')
    task_initiator = Column(String(64), default='', comment='任务发起者')
    task_group = Column(String(64), default='default', comment='任务流组名(mysql/redis)')
    task_yaml = Column(JSON, default='', comment='任务流依赖关系')
    concurrent = Column(CHAR(1), default='1', comment='是否并发执行（0允许 1禁止）')
    cron_expression = Column(String(255), default='', comment='cron执行表达式')
    misfire_policy = Column(String(20), default='3', comment='错误策略（1立即执行 2执行一次 3放弃执行）')
    status = Column(CHAR(1), default='0', comment='定时状态（0正常 1暂停）')
    run_status = Column(String(20), default='not started', comment='任务执行状态')
    task_progress = Column(FLOAT(5,4), default=0, comment='执行进度（0-100%）, 0未开始，-1失败, 1执行成功')
    priority = Column(CHAR(1), default='0', comment='任务优先级')
    create_by = Column(String(64), default='', comment='创建者')
    create_time = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    update_by = Column(String(64), default='', comment='更新者')
    update_time = Column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间')
    remark = Column(String(500), default='', comment='备注信息')

    __table_args__ = (
        Index('idx_task_uid', 'task_uid'),
        {'comment': '定时任务流调度表'}
    )


class SysJobLog(Base):
    __tablename__ = 'sys_job_log'
    
    job_log_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='任务日志ID')
    job_uid = Column(String(64), nullable=False, comment='任务UID')
    task_uid = Column(String(64), nullable=False, comment='任务流UID') 
    job_name = Column(String(64), nullable=False, comment='任务名称')
    job_parties = Column(String(128), default='', comment='任务参与方')
    job_dependencies = Column(String(2560), default='', comment='任务依赖关系')
    job_executor = Column(String(64), default='default', comment='任务执行器')
    invoke_target = Column(String(500), nullable=False, comment='调用目标字符串')
    job_args = Column(String(255), default='', comment='位置参数')
    job_kwargs = Column(String(2000), default='', comment='关键字参数')
    job_message = Column(String(500), comment='日志信息')
    status = Column(String(1), nullable=False, default='success', comment='执行状态')
    exception_info = Column(String(2000), default='', comment='异常信息')
    create_time = Column(DateTime, comment='创建时间')

    __table_args__ = (
        Index('idx_job_uid', 'job_uid'),
        Index('idx_status', 'status'),
        Index('idx_time', 'create_time'),
        {'comment': '定时任务调度日志表'}
    )


class SysTaskLog(Base):
    __tablename__ = 'sys_task_log'
    
    task_log_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='任务流日志ID')
    task_uid = Column(String(64), nullable=False, comment='任务流UID')
    task_name = Column(String(64), nullable=False, comment='任务流名称')
    task_initiator = Column(String(64), default='', comment='任务发起者')
    task_group = Column(String(64), nullable=False, comment='任务流组名')
    task_trigger = Column(String(255), default='', comment='任务触发器')
    task_message = Column(String(500), comment='日志信息')
    exception_info = Column(String(2000), default='', comment='异常信息')
    create_time = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')

    __table_args__ = (
        Index('idx_task_uid', 'task_uid'),
        Index('idx_time', 'create_time'),
        {'comment': '定时任务流调度日志表'}
    )