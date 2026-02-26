"""
pytest 配置和共享 fixtures
"""

import asyncio
import os
import sys
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.dependencies import get_db
from app.models import Base


# ============================================================
# 测试配置
# ============================================================

# 测试数据库 URL（使用 SQLite 内存数据库进行快速测试）
TEST_DATABASE_URL = "sqlite:///./test.db"

# 测试配置环境变量
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["DEBUG"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"


# ============================================================
# 数据库 Fixture
# ============================================================


@pytest.fixture(scope="session")
def engine():
    """创建测试数据库引擎"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
        if "sqlite" in TEST_DATABASE_URL
        else {},
    )

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    yield engine

    # 清理
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """为每个测试创建新的数据库会话"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def db_session_with_data(db_session: Session):
    """创建带有测试数据的数据库会话"""
    from app.models import User, Task, Goal

    # 创建测试用户
    user = User(username="testuser", password_hash="hashed_password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 创建测试目标
    goal = Goal(
        user_id=user.id,
        title="测试目标",
        description="这是一个测试目标",
        start_date="2026-02-01",
        end_date="2026-02-28",
        status="active",
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)

    # 创建测试任务
    task = Task(
        user_id=user.id,
        goal_id=goal.id,
        title="测试任务",
        description="这是一个测试任务",
        due_date="2026-02-25",
        priority=1,
        status="pending",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    yield db_session


# ============================================================
# API Client Fixture
# ============================================================


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """创建测试客户端"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def authenticated_client(
    client: TestClient, db_session: Session
) -> tuple[TestClient, str, int]:
    """创建已认证的测试客户端，返回 (client, token, user_id)"""
    from app.dependencies import get_password_hash
    from app.models import User

    # 创建测试用户
    user = User(username="authtest", password_hash=get_password_hash("testpass123"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 登录获取 token
    response = client.post(
        "/api/v1/auth/login", json={"username": "authtest", "password": "testpass123"}
    )
    token = response.json()["access_token"]

    # 设置授权头
    client.headers = {"Authorization": f"Bearer {token}"}

    return client, token, user.id


# ============================================================
# 辅助 Fixture
# ============================================================


@pytest.fixture
def test_user_data() -> dict:
    """测试用户数据"""
    return {"username": "newuser", "password": "NewPass123!"}


@pytest.fixture
def test_task_data() -> dict:
    """测试任务数据"""
    return {
        "title": "测试任务标题",
        "description": "测试任务描述",
        "due_date": "2026-02-28",
        "due_time": "14:00",
        "priority": 1,
    }


@pytest.fixture
def test_goal_data() -> dict:
    """测试目标数据"""
    return {
        "title": "测试目标标题",
        "description": "测试目标描述",
        "start_date": "2026-02-01",
        "end_date": "2026-03-01",
    }


# ============================================================
# 异步支持
# ============================================================


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
