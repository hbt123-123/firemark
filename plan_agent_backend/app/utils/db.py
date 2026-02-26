from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies import SessionLocal
from app.exceptions import DatabaseException


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseException(
            message="Database operation failed",
            details={"error": str(e)},
        )
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_session_no_commit() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseException(
            message="Database operation failed",
            details={"error": str(e)},
        )
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
