import app.db.models

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.domain.member.model import Member

TEST_MEMBER_EMAIL = "test@example.com"

def create_tables() -> None:
    Base.metadata.create_all(bind=engine)

def create_test_member() -> None:
    db = SessionLocal()

    try:
        member = (
            db.query(Member)
            .filter(Member.email == TEST_MEMBER_EMAIL)
            .first()
        )

        if member is not None:
            print(
                f"Test member already exists: "
                f"id={member.id}, email={member.email}"
            )
            return

        member = Member(
            email=TEST_MEMBER_EMAIL,
            name="Test User",
            password_hash="test-password-hash",
            status="ACTIVE",
        )

        db.add(member)
        db.commit()
        db.refresh(member)

        print(
            f"Test member created: "
            f"id={member.id}, email={member.email}"
        )

    finally:
        db.close()


def main() -> None:
    print("Creating database tables...")
    create_tables()

    print("Creating test member...")
    create_test_member()

    print("Database initialization completed.")


if __name__ == "__main__":
    main()