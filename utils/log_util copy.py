import os
import sys
import time
from loguru import logger as _logger
from typing import Dict
from middlewares.trace_middleware import TraceCtx
from utils.web_socket import WebSocketLogHandler, manager


class LoggerInitializer:
    def __init__(self):
        self.log_path = os.path.join(os.getcwd(), "logs")
        self.__ensure_log_directory_exists()
        self.log_path_error = os.path.join(
            self.log_path, f'{time.strftime("%Y-%m-%d")}_error.log'
        )
        self.log_path_all = os.path.join(self.log_path, "log_all.log")
        # 自定义日志格式
        # 日志格式分解说明：
        self.format_str = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "  # 精确到毫秒的时间戳
            "<cyan>{trace_id}</cyan> | "  # 请求追踪ID（来自中间件）
            "<level>{level: <8}</level> | "  # 对齐的日志级别标签
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "  # 代码位置
            "<level>{message}</level>"  # 日志内容
        )

    def __ensure_log_directory_exists(self):
        """
        确保日志目录存在，如果不存在则创建
        """
        if not os.path.exists(self.log_path):
            os.mkdir(self.log_path)

    @staticmethod
    def _filter(log: Dict):
        """
        自定义日志过滤器，添加trace_id
        """
        log["trace_id"] = TraceCtx.get_id()
        return log

    def init_log(self):
        """
        初始化日志配置
        """
        # note: loguru日志初始化配置
        _logger.remove()

        # 移除后重新添加sys.stderr, 目的: 控制台输出与文件日志内容和结构一致
        # 参数详解：
        # 1. sys.stderr -> 将日志输出到控制台（与print默认的stdout分离，避免日志与程序输出混杂）
        # 2. filter     -> 通过__filter方法注入trace_id（来自中间件的请求追踪ID）
        # 3. format_str -> 彩色日志格式：时间 | trace_id | 日志级别 | 代码位置 | 消息
        # 4. enqueue    -> 解决多线程日志乱序问题（生产环境必须开启）

        # 输出到控制台
        _logger.add(
            sys.stderr, filter=self._filter, format=self.format_str, enqueue=True
        )
        # 输出到文件
        _logger.add(
            self.log_path_error,
            filter=self._filter,
            format=self.format_str,
            rotation="50MB",  # 日志文件达到50MB自动分割
            encoding="utf-8",  # 确保中文日志正常存储
            enqueue=True,  # 线程安全写入
            compression="zip",  # 自动压缩历史日志
        )
        # 新增：输出到全量日志文件 (记录所有级别的日志)
        _logger.add(
            self.log_path_all,
            level="DEBUG",  # 设置为DEBUG级别，捕获所有日志信息[3](@ref)
            filter=self._filter,
            format=self.format_str,
            rotation="50MB",  # 日志文件达到50MB自动分割
            retention="7 days",  # 可选：设置日志保留期限，例如只保留最近7天的日志[5](@ref)
            encoding="utf-8",
            enqueue=True,
            compression="zip",
            colorize=True,  # 新增：确保颜色代码写入文件
        )

        return _logger


def web_socket_log_init():
    # 添加WebSocket日志处理器，只发送INFO级别及以上的日志到前端
    # web_socket_handler = WebSocketLogHandler(manager)
    # _logger.add(
    #     web_socket_handler.write,  # 使用write方法作为日志处理器
    #     level="INFO",  # 只发送INFO级别及以上的日志
    #     filter=LoggerInitializer._filter,
    #     # format=log_initializer.format_str,
    #     enqueue=True,  # 启用异步写入，避免阻塞
    # )
    pass
    
# 初始化日志处理器
log_initializer = LoggerInitializer()
logger = log_initializer.init_log()