from datetime import datetime, date
from sqlalchemy import (
    String,
    Integer,
    Text,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# 使用 timezone 工具获取 UTC 时间
import app.utils.timezone as tz


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    push_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)

    friendships_as_user: Mapped[list["Friendship"]] = relationship(
        "Friendship", foreign_keys="Friendship.user_id", back_populates="user"
    )
    friendships_as_friend: Mapped[list["Friendship"]] = relationship(
        "Friendship", foreign_keys="Friendship.friend_id", back_populates="friend"
    )
    fixed_schedules: Mapped[list["FixedSchedule"]] = relationship(
        "FixedSchedule", back_populates="user", cascade="all, delete-orphan"
    )
    goals: Mapped[list["Goal"]] = relationship(
        "Goal", back_populates="user", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="user", cascade="all, delete-orphan"
    )
    task_comments: Mapped[list["TaskComment"]] = relationship(
        "TaskComment", back_populates="user", cascade="all, delete-orphan"
    )
    memories: Mapped[list["UserMemory"]] = relationship(
        "UserMemory", back_populates="user", cascade="all, delete-orphan"
    )
    ai_sessions: Mapped[list["AISession"]] = relationship(
        "AISession", back_populates="user", cascade="all, delete-orphan"
    )
    execution_logs: Mapped[list["ExecutionLog"]] = relationship(
        "ExecutionLog", back_populates="user", cascade="all, delete-orphan"
    )
    reflection_logs: Mapped[list["ReflectionLog"]] = relationship(
        "ReflectionLog", back_populates="user", cascade="all, delete-orphan"
    )
    word_settings: Mapped["UserWordSettings | None"] = relationship(
        "UserWordSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    daily_word_tasks: Mapped[list["DailyWordTask"]] = relationship(
        "DailyWordTask", back_populates="user", cascade="all, delete-orphan"
    )
    word_feedbacks: Mapped[list["WordFeedback"]] = relationship(
        "WordFeedback", back_populates="user", cascade="all, delete-orphan"
    )


class Friendship(Base):
    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="friendships_as_user"
    )
    friend: Mapped["User"] = relationship(
        "User", foreign_keys=[friend_id], back_populates="friendships_as_friend"
    )

    __table_args__ = (Index("ix_friendships_user_friend", "user_id", "friend_id", unique=True),)


class FixedSchedule(Base):
    __tablename__ = "fixed_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)
    repeat_rule: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)

    user: Mapped["User"] = relationship("User", back_populates="fixed_schedules")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="fixed_schedule")


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    outline: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    current_phase: Mapped[str | None] = mapped_column(String(100), nullable=True)
    objective_topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective_criterion: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective_motivation: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirement_time: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirement_style: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirement_baseline: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_preference: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)

    user: Mapped["User"] = relationship("User", back_populates="goals")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="goal")
    ai_sessions: Mapped[list["AISession"]] = relationship("AISession", back_populates="goal")
    reflection_logs: Mapped[list["ReflectionLog"]] = relationship(
        "ReflectionLog", back_populates="goal"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    goal_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("goals.id"), nullable=True)
    fixed_schedule_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fixed_schedules.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=1)
    dependencies: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)

    user: Mapped["User"] = relationship("User", back_populates="tasks")
    goal: Mapped["Goal | None"] = relationship("Goal", back_populates="tasks")
    fixed_schedule: Mapped["FixedSchedule | None"] = relationship(
        "FixedSchedule", back_populates="tasks"
    )
    comments: Mapped[list["TaskComment"]] = relationship(
        "TaskComment", back_populates="task", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_tasks_user_due_date", "user_id", "due_date"),)


class TaskComment(Base):
    __tablename__ = "task_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="comment")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)

    task: Mapped["Task"] = relationship("Task", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="task_comments")


class UserMemory(Base):
    __tablename__ = "user_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)

    user: Mapped["User"] = relationship("User", back_populates="memories")

    __table_args__ = (Index("ix_user_memories_user_type", "user_id", "memory_type"),)


class AISession(Base):
    __tablename__ = "ai_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    goal_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("goals.id"), nullable=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=tz.get_utc_now, onupdate=tz.get_utc_now
    )

    user: Mapped["User"] = relationship("User", back_populates="ai_sessions")
    goal: Mapped["Goal | None"] = relationship("Goal", back_populates="ai_sessions")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    tasks_total: Mapped[int] = mapped_column(Integer, default=0)
    difficulties: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)

    user: Mapped["User"] = relationship("User", back_populates="execution_logs")

    __table_args__ = (
        Index("ix_execution_logs_user_date", "user_id", "log_date", unique=True),
    )


class ReflectionLog(Base):
    __tablename__ = "reflection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    goal_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("goals.id"), nullable=True)
    reflection_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    adjustment_plan: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)

    user: Mapped["User"] = relationship("User", back_populates="reflection_logs")
    goal: Mapped["Goal | None"] = relationship("Goal", back_populates="reflection_logs")

    __table_args__ = (Index("ix_reflection_logs_user_goal", "user_id", "goal_id"),)


class WordBank(Base):
    """单词库表"""

    __tablename__ = "word_banks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    word: Mapped[str] = mapped_column(String(100), nullable=False)
    pronunciation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    translation: Mapped[str] = mapped_column(Text, nullable=False)
    part_of_speech: Mapped[str | None] = mapped_column(String(50), nullable=True)
    examples: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    audio_url_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_url_zh: Mapped[str | None] = mapped_column(String(255), nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)


class UserWordSettings(Base):
    """用户单词设置"""

    __tablename__ = "user_word_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    selected_tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    daily_count: Mapped[int] = mapped_column(Integer, default=10)
    repeat_en: Mapped[int] = mapped_column(Integer, default=2)
    repeat_zh: Mapped[int] = mapped_column(Integer, default=1)
    enable_notification: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=tz.get_utc_now, onupdate=tz.get_utc_now
    )

    user: Mapped["User"] = relationship("User", back_populates="word_settings")

    __table_args__ = (Index("ix_user_word_settings_user_id", "user_id", unique=True),)


class DailyWordTask(Base):
    """每日单词任务"""

    __tablename__ = "daily_word_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    task_date: Mapped[date] = mapped_column(Date, nullable=False)
    word_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    completed_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)

    user: Mapped["User"] = relationship("User", back_populates="daily_word_tasks")

    __table_args__ = (Index("ix_daily_word_tasks_user_date", "user_id", "task_date", unique=True),)


class WordFeedback(Base):
    """功能反馈"""

    __tablename__ = "word_feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=tz.get_utc_now)

    user: Mapped["User"] = relationship("User", back_populates="word_feedbacks")

    __table_args__ = (Index("ix_word_feedbacks_user_id", "user_id"),)
