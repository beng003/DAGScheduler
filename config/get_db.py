from utils.log_util import logger
# 添加缺失的导入
from config.database import AsyncSessionLocal, async_engine, Base
import traceback
from config.env import DataBaseConfig


async def get_db():
    """
    每一个请求处理完毕后会关闭当前连接，不同的请求使用不同的连接

    :return:
    """
    
    # note: yield 会保留函数局部变量和执行位置，而 return 完全退出函数上下文。
    async with AsyncSessionLocal() as current_db:
        yield current_db


async def init_create_table():
    """
    应用启动时初始化数据库连接

    :return:
    """
    logger.info('初始化数据库连接...')
    # 记录数据库连接参数（注意：不记录密码）
    logger.debug(f'连接参数: 主机={DataBaseConfig.db_host}, 端口={DataBaseConfig.db_port}, 数据库={DataBaseConfig.db_database}, 用户名={DataBaseConfig.db_username}')
    
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info('数据库连接成功')
    except Exception as e:
        # 捕获更详细的错误信息
        error_type = type(e).__name__
        error_message = str(e)
        stack_trace = traceback.format_exc()
        
        # 记录详细错误信息到日志
        logger.error(f'数据库连接失败: 类型={error_type}, 消息={error_message}')
        logger.error(f'堆栈跟踪:\n{stack_trace}')
        
        # 重新抛出异常，保持原有异常类型
        raise
