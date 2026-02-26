"""
App package initialization

Import all models to ensure they are registered with SQLAlchemy.
"""

# Import main models
from app.models import (
    Base,
    User,
    Goal,
    Task,
    TaskComment,
    UserMemory,
    AISession,
    ExecutionLog,
    ReflectionLog,
    FixedSchedule,
)

# Import vector memory models (pgvector)
from app.models_memory import MemoryEmbedding

# This ensures all models are registered with SQLAlchemy's metadata
# when app.models.Base is imported for migration creation
__all__ = [
    "Base",
    "User",
    "Goal",
    "Task",
    "TaskComment",
    "UserMemory",
    "AISession",
    "ExecutionLog",
    "ReflectionLog",
    "FixedSchedule",
    "MemoryEmbedding",
]
