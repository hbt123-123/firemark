"""
任务管理 API 接口测试
"""

import pytest
from app.models import Task


class TestTaskAPI:
    """任务 API 测试"""

    @pytest.mark.api
    def test_create_task(self, authenticated_client):
        """测试创建任务"""
        client, token, user_id = authenticated_client
        task_data = {
            "title": "新任务",
            "description": "任务描述",
            "due_date": "2026-02-28",
            "priority": 1,
        }

        response = client.post("/api/v1/tasks", json=task_data)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["priority"] == task_data["priority"]
        assert data["status"] == "pending"

    @pytest.mark.api
    def test_get_tasks(self, authenticated_client):
        """测试获取任务列表"""
        client, token, user_id = authenticated_client

        response = client.get("/api/v1/tasks")

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data

    @pytest.mark.api
    def test_get_today_tasks(self, authenticated_client):
        """测试获取今日任务"""
        client, token, user_id = authenticated_client

        response = client.get("/api/v1/tasks/today")

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

    @pytest.mark.api
    def test_get_task_by_id(self, authenticated_client, db_session_with_data):
        """测试获取单个任务"""
        client, token, user_id = authenticated_client
        db_session = db_session_with_data

        # 创建测试任务
        task = Task(
            user_id=user_id,
            title="测试任务",
            description="描述",
            due_date="2026-02-25",
            priority=1,
            status="pending",
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        response = client.get(f"/api/v1/tasks/{task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "测试任务"

    @pytest.mark.api
    def test_update_task(self, authenticated_client, db_session_with_data):
        """测试更新任务"""
        client, token, user_id = authenticated_client
        db_session = db_session_with_data

        # 创建测试任务
        task = Task(
            user_id=user_id,
            title="原标题",
            due_date="2026-02-25",
            priority=1,
            status="pending",
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        update_data = {"title": "新标题", "priority": 2}
        response = client.put(f"/api/v1/tasks/{task.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新标题"
        assert data["priority"] == 2

    @pytest.mark.api
    def test_complete_task(self, authenticated_client, db_session_with_data):
        """测试完成任务"""
        client, token, user_id = authenticated_client
        db_session = db_session_with_data

        # 创建测试任务
        task = Task(
            user_id=user_id,
            title="待完成任务",
            due_date="2026-02-25",
            priority=1,
            status="pending",
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        response = client.post(f"/api/v1/tasks/{task.id}/complete")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.api
    def test_skip_task(self, authenticated_client, db_session_with_data):
        """测试跳过任务"""
        client, token, user_id = authenticated_client
        db_session = db_session_with_data

        # 创建测试任务
        task = Task(
            user_id=user_id,
            title="待跳过任务",
            due_date="2026-02-25",
            priority=1,
            status="pending",
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        response = client.post(f"/api/v1/tasks/{task.id}/skip")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "skipped"

    @pytest.mark.api
    def test_delete_task(self, authenticated_client, db_session_with_data):
        """测试删除任务"""
        client, token, user_id = authenticated_client
        db_session = db_session_with_data

        # 创建测试任务
        task = Task(
            user_id=user_id,
            title="待删除任务",
            due_date="2026-02-25",
            priority=1,
            status="pending",
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        response = client.delete(f"/api/v1/tasks/{task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.api
    def test_create_task_validation(self, authenticated_client):
        """测试任务创建验证"""
        client, token, user_id = authenticated_client

        # 测试缺少必填字段
        response = client.post("/api/v1/tasks", json={})

        assert response.status_code == 422

    @pytest.mark.api
    def test_task_not_found(self, authenticated_client):
        """测试任务不存在"""
        client, token, user_id = authenticated_client

        response = client.get("/api/v1/tasks/99999")

        assert response.status_code == 404

    @pytest.mark.api
    def test_unauthorized_task_access(self, client):
        """测试未授权访问任务"""
        response = client.get("/api/v1/tasks")

        assert response.status_code == 401
