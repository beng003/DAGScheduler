import inspect
from fastapi import Form, Query
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from typing import Type

# question: as_query这个装饰器的作用是什么？

def as_query(cls: Type[BaseModel]):
    """
    pydantic模型查询参数装饰器，将pydantic模型用于接收查询参数
    """
    new_parameters = []

    # 遍历模型的所有字段
    #model_fields是BaseModel的一个属性，是一个字典，key是字段名，value是字段信息
    # {'config_id': FieldInfo(annotation=Union[int, NoneType], required=False, 
    #                         default=None, alias='configId', alias_priority=1, 
    #                         description='参数主键'), 
    #  ...
    # }
    for field_name, model_field in cls.model_fields.items():
        model_field: FieldInfo  # 显式声明字段类型信息

        # 判断字段是否是必填项
        if not model_field.is_required():
            # 非必填字段：创建带默认值的查询参数
            new_parameters.append(
                inspect.Parameter(
                    model_field.alias,  # 使用字段别名
                    inspect.Parameter.POSITIONAL_ONLY,  # 参数位置限制
                    default=Query(default=model_field.default, description=model_field.description),
                    annotation=model_field.annotation,  # 保留类型注解
                )
            )
        else:
            # 必填字段：创建必须传递的查询参数
            new_parameters.append(
                inspect.Parameter(
                    model_field.alias,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=Query(..., description=model_field.description),
                    annotation=model_field.annotation,
                )
            )

    async def as_query_func(**data):
        return cls(**data)

    sig = inspect.signature(as_query_func)
    sig = sig.replace(parameters=new_parameters)
    as_query_func.__signature__ = sig  # type: ignore
    # note: setattr函数用于设置对象的属性值
    setattr(cls, 'as_query', as_query_func)
    return cls


def as_form(cls: Type[BaseModel]):
    """
    pydantic模型表单参数装饰器，将pydantic模型用于接收表单参数
    """
    new_parameters = []

    for field_name, model_field in cls.model_fields.items():
        model_field: FieldInfo  # type: ignore

        if not model_field.is_required():
            new_parameters.append(
                inspect.Parameter(
                    model_field.alias,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=Form(default=model_field.default, description=model_field.description),
                    annotation=model_field.annotation,
                )
            )
        else:
            new_parameters.append(
                inspect.Parameter(
                    model_field.alias,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=Form(..., description=model_field.description),
                    annotation=model_field.annotation,
                )
            )

    async def as_form_func(**data):
        return cls(**data)

    sig = inspect.signature(as_form_func)
    sig = sig.replace(parameters=new_parameters)
    as_form_func.__signature__ = sig  # type: ignore
    setattr(cls, 'as_form', as_form_func)
    return cls
