from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date
import re


class HealthResponse(BaseModel):
    status: str
    message: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=80, description="Username")
    password: str = Field(..., min_length=6, description="Password")


class UserLogin(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[int] = None
    exp: Optional[int] = None


class AgentRequest(BaseModel):
    query: str = Field(..., description="User query for the agent")
    context: Optional[dict] = Field(default=None, description="Additional context for the agent")


class AgentResponse(BaseModel):
    response: str = Field(..., description="Agent response")
    actions: List[dict] = Field(default_factory=list, description="Actions taken by the agent")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class TaskBase(BaseModel):
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    priority: Optional[int] = Field(default=1, description="Task priority (0/1/2)")


class TaskCreate(TaskBase):
    goal_id: Optional[int] = Field(default=None, description="Associated goal ID")
    fixed_schedule_id: Optional[int] = Field(default=None, description="Associated fixed schedule ID")
    due_date: date = Field(..., description="Due date")
    due_time: Optional[str] = Field(default=None, description="Due time (HH:MM)")
    dependencies: Optional[List[int]] = Field(default=None, description="Predecessor task IDs")


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[str] = None


class TaskInDB(TaskBase):
    id: int
    user_id: int
    goal_id: Optional[int]
    fixed_schedule_id: Optional[int]
    due_date: date
    due_time: Optional[str]
    status: str = "pending"
    dependencies: Optional[List[int]]
    created_at: datetime

    class Config:
        from_attributes = True


class GoalBase(BaseModel):
    title: str = Field(..., description="Goal title")
    description: Optional[str] = Field(default=None, description="Goal description")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")


class GoalCreate(GoalBase):
    objective_topic: Optional[str] = None
    objective_criterion: Optional[str] = None
    objective_motivation: Optional[str] = None
    requirement_time: Optional[str] = None
    requirement_style: Optional[str] = None
    requirement_baseline: Optional[str] = None
    resource_preference: Optional[str] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    current_phase: Optional[str] = None


class GoalInDB(GoalBase):
    id: int
    user_id: int
    status: str = "active"
    current_phase: Optional[str]
    outline: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class FixedScheduleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Schedule title")
    description: Optional[str] = Field(default=None, description="Schedule description")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    start_time: str = Field(..., description="Start time (HH:MM format)")
    end_time: str = Field(..., description="End time (HH:MM format)")

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if not re.match(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$', v):
            raise ValueError('Time must be in HH:MM format')
        return v


class FixedScheduleCreate(FixedScheduleBase):
    repeat_rule: Optional[dict] = Field(default=None, description="Repeat rule configuration")
    is_active: Optional[bool] = Field(default=True, description="Whether the schedule is active")


class FixedScheduleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    repeat_rule: Optional[dict] = None
    is_active: Optional[bool] = None

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$', v):
            raise ValueError('Time must be in HH:MM format')
        return v


class FixedScheduleResponse(FixedScheduleBase):
    id: int
    user_id: int
    repeat_rule: Optional[dict]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class FixedScheduleListResponse(BaseModel):
    schedules: List[FixedScheduleResponse]
    total: int


# ============== Word Settings ==============


class WordSettingsBase(BaseModel):
    """单词设置基础模型"""

    selected_tags: Optional[List[str]] = Field(default=None, description="选择的词库标签")
    daily_count: Optional[int] = Field(default=None, ge=1, le=100, description="每日学习数量")
    repeat_en: Optional[int] = Field(default=None, ge=1, le=10, description="英文重复次数")
    repeat_zh: Optional[int] = Field(default=None, ge=1, le=10, description="中文重复次数")
    enable_notification: Optional[bool] = Field(default=None, description="是否启用通知")


class WordSettingsCreate(WordSettingsBase):
    """创建单词设置"""
    pass


class WordSettingsUpdate(WordSettingsBase):
    """更新单词设置 - 所有字段可选但至少提供一个"""
    pass


class WordSettingsResponse(BaseModel):
    """单词设置响应"""

    id: int
    user_id: int
    selected_tags: List[str]
    daily_count: int
    repeat_en: int
    repeat_zh: int
    enable_notification: bool
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Daily Words ==============


class WordDetail(BaseModel):
    """单词详情"""

    id: int
    word: str
    translation: str
    phonetic_us: Optional[str] = None
    phonetic_uk: Optional[str] = None
    part_of_speech: Optional[str] = None
    audio_url_en: Optional[str] = None
    audio_url_zh: Optional[str] = None
    examples: Optional[List[dict]] = None

    class Config:
        from_attributes = True


class DailyWordsResponse(BaseModel):
    """每日单词任务响应"""

    task_id: int
    task_date: date
    total_count: int
    completed_count: int
    status: str
    words: List[WordDetail]

    class Config:
        from_attributes = True


# ============== Word Complete ==============


class WordCompleteRequest(BaseModel):
    """单词完成请求"""

    word_id: int = Field(..., description="完成的单词ID")
    date: Optional[date] = Field(default=None, description="日期，格式YYYY-MM-DD，默认当天")


class WordCompleteResponse(BaseModel):
    """单词完成响应"""

    completed: int
    total: int
    status: str


# ============== Word Stats ==============


class DailyStat(BaseModel):
    """每日统计详情"""

    date: date
    total_words: int
    completed_words: int
    status: str


class WordStatsResponse(BaseModel):
    """单词学习统计响应"""

    total_days: int
    total_words_assigned: int
    total_words_completed: int
    completion_rate: float
    daily_average: float
    daily_details: Optional[List[DailyStat]] = None


# ============== Feedback ==============


class FeedbackCreate(BaseModel):
    """反馈创建请求"""

    feature_name: str = Field(..., min_length=1, max_length=100, description="功能名称")
    feedback_type: str = Field(..., description="反馈类型: suggestion, bug, praise")
    content: str = Field(..., min_length=1, description="反馈内容")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="评分1-5")

    @field_validator('feedback_type')
    @classmethod
    def validate_feedback_type(cls, v: str) -> str:
        valid_types = ['suggestion', 'bug', 'praise']
        if v not in valid_types:
            raise ValueError(f'feedback_type must be one of: {valid_types}')
        return v



class FeedbackResponse(BaseModel):
    """反馈响应"""

    success: bool
    id: int
