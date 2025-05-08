from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import AsyncSessionLocal
from middlewares.entity.do.logging_do import RequestLog
import time

async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    async with AsyncSessionLocal() as session:
        log = RequestLog(
            client_host=request.client.host if request.client else None,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=process_time,
            user_agent=request.headers.get("user-agent")
        )
        session.add(log)
        await session.commit()
    
    return response