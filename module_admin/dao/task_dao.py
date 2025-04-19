from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.task_do import SysTask
from module_admin.entity.vo.task_vo import (
    TaskModel,
    TaskPageQueryModel,
)
from utils.page_util import PageUtil


class TaskDao:
    """
    定时任务流管理模块数据库操作层
    """

    @classmethod
    async def get_task_detail_by_uid(cls, db: AsyncSession, task_uid: str):
        """
        根据定时任务流uid获取定时任务流详细信息

        :param db: orm对象
        :param task_uid: 定时任务流uid
        :return: 定时任务流信息对象
        """
        task_info = (
            (await db.execute(select(SysTask).where(SysTask.task_uid == task_uid)))
            .scalars()
            .first()
        )

        return task_info

    @classmethod
    async def get_task_detail_by_info(cls, db: AsyncSession, task: TaskModel):
        """
        根据定时任务流参数获取定时任务流信息

        :param db: orm对象
        :param task: 定时任务流参数对象
        :return: 定时任务流信息对象
        """
        
        # todo: 修改通过除uid以外的其他字段查询
        task_info = (
            (
                await db.execute(
                    select(SysTask).where(
                        SysTask.task_name == task.task_name if task.task_name else True,
                        SysTask.task_uid == task.task_uid if task.task_uid else True,
                    )
                )
            )
            .scalars()
            .first()
        )

        return task_info

    @classmethod
    async def get_task_list(
        cls, db: AsyncSession, query_object: TaskPageQueryModel, is_page: bool = False
    ):
        """
        根据查询参数获取定时任务流列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 定时任务流列表信息对象
        """
        query = (
            select(SysTask)
            .where(
                (
                    SysTask.task_name.like(f"%{query_object.task_name}%")
                    if query_object.task_name
                    else True
                ),
                (
                    SysTask.task_group == query_object.task_group
                    if query_object.task_group
                    else True
                ),
                SysTask.status == query_object.status if query_object.status else True,
            )
            .order_by(SysTask.task_uid)
            .distinct()
        )
        task_list = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return task_list

    @classmethod
    async def get_job_list_for_scheduler(cls, db: AsyncSession):
        """
        获取定时任务流列表信息

        :param db: orm对象
        :return: 定时子任务列表信息对象
        """
        # note: AsyncSession.execute()方法返回的是一个Result对象，通过scalars()方法获取所有结果
        # (await db.execute(   # 异步执行SQL查询
        #     select(SysTask)   # 查询SysTask表所有字段
        #     .where(...)      # 添加过滤条件
        #     .distinct()      # 去重（确保结果唯一）
        # ))
        # .scalars()  # 将Row对象转换为ORM模型实例
        # .all()     # 获取全部结果
        query = (
            select(SysTask)
            .where(
                SysTask.status == "0",
            )
            .distinct()
        )

        task_list = (await db.execute(query)).scalars().all()

        return task_list

    @classmethod
    async def add_task_dao(cls, db: AsyncSession, task: TaskModel):
        """
        新增定时任务流数据库操作

        :param db: orm对象
        :param task: 定时任务流对象
        :return:
        """
        db_task = SysTask(**task.model_dump())
        db.add(db_task)
        await db.flush()

        return db_task

    @classmethod
    async def edit_task_dao(cls, db: AsyncSession, task: dict):
        """
        编辑定时任务流数据库操作

        :param db: orm对象
        :param task: 需要更新的定时任务流字典
        :return:
        """
        await db.execute(update(SysTask), [task])


    @classmethod
    async def delete_task_dao(cls, db: AsyncSession, task: TaskModel):
        """
        删除定时任务流数据库操作

        :param db: orm对象
        :param task: 定时任务流对象
        :return:
        """
        await db.execute(delete(SysTask).where(SysTask.task_uid.in_([task.task_uid])))
