import argparse
import asyncio
import secrets
import string
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.domain.entities.user import User
from src.domain.value_objects.email import EmailAddress
from src.domain.value_objects.user_role import UserRole
from src.infrastructure.crypto.hasher import PasswordHasherEngine
from src.infrastructure.db.repositories.user import SqlAlchemyUserRepository
from src.infrastructure.db.session import async_session_factory


def generate_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%^&*" for c in password)
        ):
            return password


async def create_admin(username: str, email_str: str) -> None:
    async with async_session_factory() as session:
        user_repo = SqlAlchemyUserRepository(session)
        hasher = PasswordHasherEngine()

        email = EmailAddress(email_str)

        existing_user = await user_repo.find_by_username(username)
        if existing_user:
            print(f"Error: User with username '{username}' already exists.", file=sys.stderr)
            sys.exit(1)

        existing_email = await user_repo.find_by_email(email)
        if existing_email:
            print(f"Error: User with email '{email_str}' already exists.", file=sys.stderr)
            sys.exit(1)

        password = generate_password(24)
        hashed_password = hasher.hash_password(password)

        admin = User.create_new(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
        )

        await user_repo.save(admin)
        await session.commit()

        print("=== ADMINISTRATIVE ACCOUNT CREATED SUCCESSFULLY ===")
        print(f" Username : {username}")
        print(f" Email    : {email_str}")
        print(f" Role     : {admin.role.value}")
        print(f" Password : {password}")
        print(" IMPORTANT: Store these credentials securely.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an initial administrative account.")
    parser.add_argument("--username", default="admin", help="Admin username (default: admin)")
    parser.add_argument(
        "--email",
        default="admin@provenance.vault",
        help="Admin email (default: admin@provenance.vault)",
    )
    args = parser.parse_args()

    asyncio.run(create_admin(args.username, args.email))


if __name__ == "__main__":
    main()
