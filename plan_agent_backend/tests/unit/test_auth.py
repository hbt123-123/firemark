"""
认证模块单元测试
"""

import pytest
from app.dependencies import get_password_hash, verify_password, create_access_token
from app.models import User


class TestPasswordHashing:
    """密码哈希功能测试"""

    def test_password_hashing(self):
        """测试密码哈希生成"""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_password_verification_correct(self):
        """测试正确密码验证"""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_incorrect(self):
        """测试错误密码验证"""
        password = "TestPassword123"
        wrong_password = "WrongPassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_password_hash_uniqueness(self):
        """测试哈希唯一性（相同密码生成不同哈希）"""
        password = "TestPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # bcrypt 每次生成不同的盐值
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestTokenGeneration:
    """Token 生成功能测试"""

    def test_create_access_token(self):
        """测试访问令牌生成"""
        user_id = 1
        token = create_access_token(data={"sub": user_id})

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """测试带过期时间的令牌生成"""
        from datetime import timedelta

        user_id = 1
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data={"sub": user_id}, expires_delta=expires_delta)

        assert token is not None


class TestUserModel:
    """用户模型测试"""

    def test_create_user(self, db_session):
        """测试创建用户"""
        user = User(username="testuser", password_hash=get_password_hash("password123"))
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == "testuser"
        assert user.password_hash is not None
        assert user.created_at is not None

    def test_user_unique_username(self, db_session):
        """测试用户名唯一性约束"""
        from sqlalchemy.exc import IntegrityError

        user1 = User(username="duplicate", password_hash="hash1")
        db_session.add(user1)
        db_session.commit()

        user2 = User(username="duplicate", password_hash="hash2")
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()
