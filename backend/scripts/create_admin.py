#!/usr/bin/env python3
"""
Script to create an initial admin user.

Usage:
    python scripts/create_admin.py
    python scripts/create_admin.py --email admin@example.com --password MyPassword123
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from getpass import getpass
import argparse

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.admin_user import AdminUser
from app.utils.security import get_password_hash


async def create_admin_user(email: str, password: str) -> None:
    """
    Create an admin user in the database.

    Args:
        email: Admin email address
        password: Plain text password (will be hashed)

    Raises:
        ValueError: If admin with email already exists
    """
    async with AsyncSessionLocal() as db:
        # Check if admin already exists
        result = await db.execute(
            select(AdminUser).where(AdminUser.email == email)
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print(f"❌ Error: Admin with email '{email}' already exists!")
            sys.exit(1)

        # Create new admin
        hashed_password = get_password_hash(password)
        admin = AdminUser(
            email=email,
            hashed_password=hashed_password,
            role="admin"
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin.email}")
        print(f"   ID: {admin.id}")
        print(f"   Role: {admin.role}")
        print(f"\nYou can now log in at the admin dashboard.")


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Create an admin user for WorkClock"
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Admin email address"
    )
    parser.add_argument(
        "--password",
        type=str,
        help="Admin password (will prompt if not provided)"
    )

    args = parser.parse_args()

    # Get email
    if args.email:
        email = args.email
    else:
        email = input("Enter admin email: ").strip()

    # Validate email
    if not email or "@" not in email:
        print("❌ Error: Invalid email address")
        sys.exit(1)

    # Get password
    if args.password:
        password = args.password
    else:
        password = getpass("Enter admin password: ")
        password_confirm = getpass("Confirm admin password: ")

        if password != password_confirm:
            print("❌ Error: Passwords do not match")
            sys.exit(1)

    # Validate password
    if len(password) < 8:
        print("❌ Error: Password must be at least 8 characters")
        sys.exit(1)

    # Create admin user
    print(f"\nCreating admin user: {email}")
    asyncio.run(create_admin_user(email, password))


if __name__ == "__main__":
    main()
