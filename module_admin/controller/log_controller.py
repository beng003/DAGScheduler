from fastapi import HTTPException, Response, APIRouter, Request
from utils.log_util import log_initializer
import os
from utils.log_util import logger
from fastapi import WebSocket, WebSocketDisconnect
from utils.log_util import manager

# question: LoginService.get_current_user?
logController = APIRouter(prefix="/logs")

@logController.websocket("/ws")
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

@logController.get(
    "/get"
)
async def test_log(
    request: Request,
):
    """测试日志生成"""
    logger.debug("这是一条调试信息 - 通常不会发送到 WebSocket")
    logger.info("🔵 这是一条信息级别的日志")
    logger.success("✅ 操作成功完成！")
    logger.warning("⚠️  这是一个警告信息")
    logger.error("❌ 发生了一个错误")
    logger.critical("🔥 严重错误！需要立即关注")
    
    return {"message": "测试日志已生成，请查看 WebSocket 连接"}

@logController.get(
    "/download"
)
async def download_log_file():
    """下载全量日志文件"""
    # 获取日志文件路径
    log_file_path = log_initializer.log_path_all
    
    # 检查文件是否存在
    if not os.path.exists(log_file_path):
        raise HTTPException(status_code=404, detail="日志文件不存在")
    
    try:
        # 读取日志文件内容
        with open(log_file_path, "rb") as f:
            log_content = f.read()
        
        # 设置响应头，使浏览器能够下载文件
        headers = {
            "Content-Disposition": f"attachment; filename={os.path.basename(log_file_path)}"
        }
        
        # 返回文件内容和响应头
        return Response(content=log_content, media_type="application/octet-stream", headers=headers)
    except Exception as e:
        logger.error(f"读取日志文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"读取日志文件失败: {str(e)}")