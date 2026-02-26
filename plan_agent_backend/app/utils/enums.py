from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"

    @classmethod
    def valid_values(cls) -> list[str]:
        return [e.value for e in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.valid_values()


class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

    @classmethod
    def valid_values(cls) -> list[str]:
        return [e.value for e in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.valid_values()


class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"

    @classmethod
    def valid_values(cls) -> list[str]:
        return [e.value for e in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.valid_values()


class CommentType(str, Enum):
    COMMENT = "comment"
    LIKE = "like"

    @classmethod
    def valid_values(cls) -> list[str]:
        return [e.value for e in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.valid_values()


class MemoryType(str, Enum):
    PREFERENCE = "preference"
    EVENT = "event"
    ACHIEVEMENT = "achievement"

    @classmethod
    def valid_values(cls) -> list[str]:
        return [e.value for e in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.valid_values()


class TaskPriority(int, Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2

    @classmethod
    def valid_values(cls) -> list[int]:
        return [e.value for e in cls]

    @classmethod
    def is_valid(cls, value: int) -> bool:
        return value in cls.valid_values()
