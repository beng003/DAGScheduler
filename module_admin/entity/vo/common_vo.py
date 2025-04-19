from pydantic import BaseModel, Field
from typing import Any, Optional


class CrudResponseModel(BaseModel):
    """
    操作响应模型
    """

    is_success: bool = Field(description='操作是否成功')
    message: str = Field(description='响应信息')
    result: Optional[Any] = Field(default=None, description='响应结果')