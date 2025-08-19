#!/usr/bin/env python
"""
Initialize Alembic for KKUA project and create initial migration.
This script should be run once to set up the database migration system.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ Success: {description}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {description}")
        print(f"Command failed with return code {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """Initialize Alembic for the project."""
    # Ensure we're in the backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)

    print("🚀 Initializing Alembic for KKUA project...")
    print(f"Working directory: {os.getcwd()}")

    # Check if alembic is installed
    if not run_command(
        [
            "python",
            "-c",
            "import alembic; print(f'Alembic version: {alembic.__version__}')",
        ],
        "Checking Alembic installation",
    ):
        print("❌ Alembic is not installed. Please run: pip install alembic")
        return False

    # Check if alembic directory already exists
    if os.path.exists("alembic/versions"):
        print("⚠️  Alembic is already initialized.")
        create_migration = (
            input("Do you want to create a new migration? (y/N): ").lower().strip()
        )

        if create_migration == "y":
            # Create a new migration
            migration_message = input(
                "Enter migration message (or press Enter for 'Update schema'): "
            ).strip()
            if not migration_message:
                migration_message = "Update schema"

            return run_command(
                ["alembic", "revision", "--autogenerate", "-m", migration_message],
                f"Creating migration: {migration_message}",
            )
        else:
            print("ℹ️  No new migration created.")
            return True

    print("📝 Creating initial migration...")

    # Create the initial migration
    if run_command(
        ["alembic", "revision", "--autogenerate", "-m", "Initial database schema"],
        "Creating initial database schema migration",
    ):
        print("\n✅ Alembic initialization complete!")
        print("\n📋 Next steps:")
        print("1. Review the generated migration file in alembic/versions/")
        print("2. To apply migrations: alembic upgrade head")
        print(
            "3. To create new migrations: alembic revision --autogenerate -m 'description'"
        )
        print("4. To rollback: alembic downgrade -1")

        # Show the migration file location
        versions_dir = Path("alembic/versions")
        if versions_dir.exists():
            migration_files = list(versions_dir.glob("*.py"))
            if migration_files:
                latest_migration = max(migration_files, key=os.path.getctime)
                print(f"\n📄 Latest migration file: {latest_migration}")

        return True

    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
