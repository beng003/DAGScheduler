from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
# from loguru import logger
from utils.log_util import logger, log_initializer
from utils.web_socket import manager
import sys
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List

# # 存储活跃的 WebSocket 连接
# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: List[WebSocket] = []
    
#     async def connect(self, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections.append(websocket)
#         logger.info(f"新的 WebSocket 连接建立，当前连接数: {len(self.active_connections)}")
    
#     def disconnect(self, websocket: WebSocket):
#         self.active_connections.remove(websocket)
#         logger.info(f"WebSocket 连接关闭，剩余连接数: {len(self.active_connections)}")
    
#     async def broadcast(self, message: str):
#         """向所有连接的客户端广播消息"""
#         for connection in self.active_connections:
#             try:
#                 await connection.send_text(message)
#             except Exception as e:
#                 logger.error(f"向客户端发送消息失败: {e}")
#                 self.disconnect(connection)

# # 全局连接管理器
# manager = ConnectionManager()

# # 自定义 Loguru 处理器，将日志转发到 WebSocket
# class WebSocketLogHandler:
#     def __init__(self, manager: ConnectionManager):
#         self.manager = manager
    
#     def write(self, message):
#         """处理日志消息并广播到所有 WebSocket 客户端"""
#         # 移除 Loguru 默认的时间戳和级别前缀（因为 Loguru 已经格式化了）
#         cleaned_message = message.strip()
#         asyncio.create_task(self.manager.broadcast(cleaned_message))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时配置 Loguru
    log_initializer.init_log()
    logger.info("FastAPI 应用启动完成")
    yield
    # 关闭时清理
    await manager.close_all_connections()
    logger.info("FastAPI 应用正在关闭")

# def setup_loguru():
#     """配置 Loguru 日志系统"""
#     # 移除默认处理器
#     logger.remove()
    
#     # 配置控制台输出（带颜色）
#     logger.add(
#         sys.stdout,
#         colorize=True,
#         format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
#                "<level>{level: <8}</level> | "
#                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
#                "<level>{message}</level>",
#         level="INFO"
#     )
    
#     # 配置 WebSocket 输出处理器
#     ws_handler = WebSocketLogHandler(manager)
#     logger.add(
#         ws_handler.write,
#         format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
#                "<level>{level: <8}</level> | "
#                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
#                "<level>{message}</level>",
#         level="INFO",
#         colorize=True  # 保持 ANSI 颜色代码
#     )
    
#     # 可选：添加文件日志
#     logger.add(
#         "app.log",
#         rotation="500 MB",
#         retention="10 days",
#         format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
#         level="INFO"
#     )

# 创建 FastAPI 应用
app = FastAPI(
    title="WebSocket 日志服务",
    description="通过 WebSocket 实时传输彩色日志信息",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/logs/ws")
async def websocket_log_endpoint(websocket: WebSocket):
    """WebSocket 端点，用于实时传输日志"""
    await manager.connect(websocket)
    try:
        # 发送欢迎消息
        welcome_msg = "\033[32m🚀 已连接到实时日志服务\033[0m"
        await websocket.send_text(welcome_msg)
        
        # 保持连接活跃
        while True:
            # 心跳检测，防止连接超时
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 连接异常: {e}")
        manager.disconnect(websocket)

@app.get("/")
async def root():
    """根端点"""
    # 发送欢迎消息
    logger.info("访问root")
    
    return {
        "message": "WebSocket 日志服务已启动",
        "websocket_endpoint": "ws://localhost:9099/logs/ws",
        "documentation": "/docs"
    }

@app.get("/test/log")
async def test_log():
    """测试日志生成"""
    logger.debug("这是一条调试信息 - 通常不会发送到 WebSocket")
    logger.info("🔵 这是一条信息级别的日志")
    logger.success("✅ 操作成功完成！")
    logger.warning("⚠️  这是一个警告信息")
    logger.error("❌ 发生了一个错误")
    logger.critical("🔥 严重错误！需要立即关注")
    
    return {"message": "测试日志已生成，请查看 WebSocket 连接"}

@app.get("/test/colors")
async def test_colors():
    """测试 ANSI 颜色输出"""
    # 生成带有不同颜色的测试消息
    colors_test = [
        "\033[31m红色文本\033[0m",
        "\033[32m绿色文本\033[0m", 
        "\033[33m黄色文本\033[0m",
        "\033[34m蓝色文本\033[0m",
        "\033[35m紫色文本\033[0m",
        "\033[36m青色文本\033[0m",
        "\033[41m红色背景\033[0m",
        "\033[42m绿色背景\033[0m",
        "\033[1m粗体文本\033[0m",
        "\033[4m下划线文本\033[0m"
    ]
    
    for color_msg in colors_test:
        logger.info(f"颜色测试: {color_msg}")
    
    return {"message": "ANSI 颜色测试已完成"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=9099,
        log_config=None  # 禁用 Uvicorn 的默认日志配置，使用 Loguru
    )