"""
认证 API 接口测试
"""

import pytest


class TestAuthAPI:
    """认证 API 测试"""

    @pytest.mark.api
    def test_register_success(self, client, test_user_data):
        """测试用户注册成功"""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.api
    def test_register_duplicate_username(self, client, test_user_data):
        """测试重复用户名注册"""
        # 第一次注册
        client.post("/api/v1/auth/register", json=test_user_data)

        # 第二次注册相同用户名
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    @pytest.mark.api
    def test_register_invalid_username(self, client):
        """测试无效用户名注册"""
        # 用户名太短
        response = client.post(
            "/api/v1/auth/register", json={"username": "ab", "password": "Test123456"}
        )

        assert response.status_code == 422

    @pytest.mark.api
    def test_register_invalid_password(self, client):
        """测试无效密码注册"""
        # 密码太短
        response = client.post(
            "/api/v1/auth/register", json={"username": "validuser", "password": "123"}
        )

        assert response.status_code == 422

    @pytest.mark.api
    def test_login_success(self, client, test_user_data):
        """测试登录成功"""
        # 先注册用户
        client.post("/api/v1/auth/register", json=test_user_data)

        # 然后登录
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.api
    def test_login_wrong_password(self, client, test_user_data):
        """测试错误密码登录"""
        # 先注册用户
        client.post("/api/v1/auth/register", json=test_user_data)

        # 使用错误密码登录
        response = client.post(
            "/api/v1/auth/login",
            json={"username": test_user_data["username"], "password": "WrongPassword"},
        )

        assert response.status_code == 401

    @pytest.mark.api
    def test_login_nonexistent_user(self, client):
        """测试不存在的用户登录"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "Test123456"},
        )

        assert response.status_code == 401

    @pytest.mark.api
    def test_login_form(self, client, test_user_data):
        """测试表单登录"""
        # 先注册用户
        client.post("/api/v1/auth/register", json=test_user_data)

        # 表单登录
        response = client.post(
            "/api/v1/auth/login/form",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.api
    def test_get_current_user(self, authenticated_client):
        """测试获取当前用户信息"""
        client, token, user_id = authenticated_client

        response = client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert "username" in data

    @pytest.mark.api
    def test_get_current_user_unauthorized(self, client):
        """测试未授权获取用户信息"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.api
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
