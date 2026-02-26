"""
数据库迁移 - 添加 pgvector 支持

使用方法:
    python -m app.migrations.vector_migration

或使用 Alembic:
    alembic revision --autogenerate -m "add pgvector extension and memory_embeddings table"
    alembic upgrade head
"""

import logging

from sqlalchemy import text

from app.dependencies import engine

logger = logging.getLogger(__name__)


def check_pgvector_installed() -> bool:
    """检查 pgvector 扩展是否已安装"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            return result.scalar() is not None
    except Exception as e:
        logger.error(f"Failed to check pgvector: {e}")
        return False


def enable_pgvector_extension() -> bool:
    """启用 pgvector 扩展"""
    try:
        with engine.connect() as conn:
            # 创建扩展 (IF NOT EXISTS 确保不会出错)
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("pgvector extension enabled successfully")
            return True
    except Exception as e:
        logger.error(f"Failed to enable pgvector: {e}")
        logger.warning("Make sure pgvector is installed in your PostgreSQL:")
        logger.warning("  CREATE EXTENSION vector;")
        return False


def create_memory_embeddings_table() -> bool:
    """创建 memory_embeddings 表"""
    try:
        # 导入所有模型以确保它们已注册
        from app import MemoryEmbedding

        # 创建表
        MemoryEmbedding.__table__.create(engine)
        logger.info("memory_embeddings table created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create memory_embeddings table: {e}")
        return False


def run_migration() -> dict:
    """运行完整的向量迁移"""
    logger.info("Starting vector migration...")

    results = {
        "pgvector_check": False,
        "pgvector_enabled": False,
        "table_created": False,
    }

    # 1. 检查 pgvector 是否已安装
    results["pgvector_check"] = check_pgvector_installed()
    if results["pgvector_check"]:
        logger.info("pgvector extension is already installed")

    # 2. 启用 pgvector 扩展
    results["pgvector_enabled"] = enable_pgvector_extension()
    if not results["pgvector_enabled"]:
        logger.error("Failed to enable pgvector extension")
        return results

    # 3. 创建 memory_embeddings 表
    results["table_created"] = create_memory_embeddings_table()
    if not results["table_created"]:
        logger.error("Failed to create memory_embeddings table")
        return results

    # 4. 验证表已创建
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM memory_embeddings"))
            logger.info(f"memory_embeddings table verified: {result.scalar()} rows")
    except Exception as e:
        logger.warning(f"Could not verify table: {e}")

    logger.info("Vector migration completed successfully!")
    return results


if __name__ == "__main__":
    import sys

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    results = run_migration()

    print("\n" + "=" * 50)
    print("Migration Results:")
    print("=" * 50)
    print(f"pgvector installed: {results['pgvector_check']}")
    print(f"pgvector enabled: {results['pgvector_enabled']}")
    print(f"Table created: {results['table_created']}")
    print("=" * 50)

    if all([results["pgvector_enabled"], results["table_created"]]):
        print("SUCCESS: Vector storage is ready!")
        sys.exit(0)
    else:
        print("ERROR: Migration incomplete. Check logs above.")
        sys.exit(1)
