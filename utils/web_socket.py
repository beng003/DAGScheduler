from fastapi import WebSocket
from loguru import logger
from typing import List
import asyncio
import weakref

# 存储活跃的 WebSocket 连接
class ConnectionManager:
    def __init__(self):
        # 使用列表存储WebSocket连接的弱引用，避免内存泄漏
        self.active_connections: List[weakref.ref] = []
        # 添加锁以确保线程安全
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            # 存储连接的弱引用
            self.active_connections.append(weakref.ref(websocket))
            logger.info(f"新的 WebSocket 连接建立，当前连接数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        asyncio.create_task(self._disconnect_async(websocket))
    
    async def _disconnect_async(self, websocket: WebSocket):
        async with self._lock:
            # 清理断开的连接
            self.active_connections = [ref for ref in self.active_connections if ref() is not None and ref() != websocket]
            logger.info(f"WebSocket 连接关闭，剩余连接数: {len(self.active_connections)}")
    
    async def broadcast(self, message: str):
        """向所有连接的客户端广播消息"""
        async with self._lock:
            # 创建一个副本，避免在迭代过程中修改列表
            connections_copy = self.active_connections.copy()
        
        for ref in connections_copy:
            connection = ref()
            if connection is not None:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"向客户端发送消息失败: {e}")
                    # 异步断开连接，避免阻塞
                    asyncio.create_task(self._disconnect_async(connection))
    
    async def close_all_connections(self):
        """关闭所有活跃的WebSocket连接"""
        async with self._lock:
            # 创建一个副本，避免在迭代过程中修改列表
            connections_copy = self.active_connections.copy()
            # 清空连接列表
            self.active_connections.clear()
        
        # 逐一关闭连接
        for ref in connections_copy:
            connection = ref()
            if connection is not None:
                try:
                    await connection.close()
                    logger.info("成功关闭WebSocket连接")
                except Exception as e:
                    logger.error(f"关闭WebSocket连接时出错: {e}")

# 自定义 Loguru 处理器，将日志转发到 WebSocket
class WebSocketLogHandler:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
    
    def write(self, message):
        """处理日志消息并广播到所有 WebSocket 客户端"""
        cleaned_message = message.strip()
        try:
            # 检查是否有运行中的事件循环
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，使用 create_task
                asyncio.create_task(self.manager.broadcast(cleaned_message))
            else:
                # 如果事件循环存在但未运行，使用 run_coroutine_threadsafe
                asyncio.run_coroutine_threadsafe(
                    self.manager.broadcast(cleaned_message), loop
                )
        except Exception as e:
            # 如果没有事件循环，记录错误但不影响程序运行
            logger.error(f"没有运行中的事件循环，无法广播日志: {e}")
        # cleaned_message = message.strip()
        # asyncio.create_task(self.manager.broadcast(cleaned_message))

# 全局连接管理器
manager = ConnectionManager()