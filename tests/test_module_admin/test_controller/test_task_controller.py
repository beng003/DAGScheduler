import pytest
from httpx import AsyncClient
from tests.test_data import task_data


@pytest.mark.anyio
async def test_get_task_list(async_client: AsyncClient):
    response = await async_client.get("/scheduler/task/list?page_num=1&page_size=20")
    assert response.status_code == 200
    assert response.json()["success"] is True
    # assert response.json()["total"] > 0
    assert response.json()["page_num"] == 1
    assert response.json()["page_size"] == 20
    assert response.json()["has_next"] is False


@pytest.mark.anyio
async def test_add_task(async_client: AsyncClient):
    # 测试新增任务接口
    response = await async_client.post("/scheduler/task/add", json=task_data)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["task_uid"] == task_data["task_uid"]


# @pytest.mark.anyio
# async def test_execute_task(async_client: AsyncClient):
#     # 测试执行任务接口
#     response = await async_client.post("/scheduler/task/start?task_uid=test_uid")
#     assert response.status_code == 200
#     assert response.json()["code"] == 200
#     assert "执行成功" in response.json()["msg"]
#     assert response.json()["task_uid"] == task_data["task_uid"]


# @pytest.mark.anyio
# async def test_stop_task(async_client: AsyncClient):
#     # 测试停止任务接口
#     response = await async_client.post("/scheduler/task/stop?task_uid=test_uid")
#     assert response.status_code == 200
#     assert response.json()["code"] == 200
#     assert "停止成功" in response.json()["msg"]
#     assert response.json()["task_uid"] == task_data["task_uid"]


# @pytest.mark.anyio
# async def test_get_task_detail(async_client: AsyncClient):
#     # 测试获取任务详情接口
#     response = await async_client.get("/scheduler/task/get?task_uid=test_uid")
#     assert response.status_code == 200
#     assert response.json()["code"] == 200
#     assert "task_uid" in response.json()["data"]
#     assert response.json()["data"]["task_uid"] == task_data["task_uid"]
