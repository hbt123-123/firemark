from app.dependencies import init_db, engine
from app.models import Base


def main():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    main()
