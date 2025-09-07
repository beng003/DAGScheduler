from typing import Dict, Set
from fastapi import WebSocket
import asyncio

class LogWebSocketManager:
    """
    管理日志WebSocket连接，处理日志实时推送
    """
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.pubsub = asyncio.Queue()
        self.running = True
        asyncio.create_task(self.broadcast_logs())
    
    async def connect(self, websocket: WebSocket, log_type: str = "all"):
        """连接WebSocket并添加到指定日志类型的连接集合"""
        await websocket.accept()
        if log_type not in self.active_connections:
            self.active_connections[log_type] = set()
        self.active_connections[log_type].add(websocket)
        
        try:
            # 保持连接活动状态
            while True:
                await websocket.receive_text()
        except Exception:
            # 连接关闭时从集合中移除
            self.active_connections[log_type].remove(websocket)
            if not self.active_connections[log_type]:
                del self.active_connections[log_type]
    
    async def broadcast_logs(self):
        """从队列接收日志并广播到所有连接"""
        while self.running:
            try:
                log_message = await self.pubsub.get()
                # 广播到所有连接
                for log_type, connections in list(self.active_connections.items()):
                    if log_type == "all" or log_type in log_message:
                        for connection in list(connections):
                            try:
                                await connection.send_text(log_message)
                            except Exception:
                                # 处理发送失败的连接
                                connections.remove(connection)
                                if not connections:
                                    del self.active_connections[log_type]
            except Exception as e:
                print(f"Error broadcasting logs: {e}")
    
    async def push_log(self, log_message: str):
        """推送日志消息到队列"""
        await self.pubsub.put(log_message)
    
    def shutdown(self):
        """关闭WebSocket管理器"""
        self.running = False

# 创建全局日志WebSocket管理器实例
log_websocket_manager = LogWebSocketManager()