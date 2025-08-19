#!/usr/bin/env python
"""
Database migration management script for KKUA project.
Provides easy commands for common migration operations.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, text=True)
        print(f"✅ Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {description}")
        print(f"Command failed with return code {e.returncode}")
        return False


def upgrade(revision="head"):
    """Apply migrations up to a specific revision."""
    return run_command(
        ["alembic", "upgrade", revision], f"Upgrading database to {revision}"
    )


def downgrade(revision="-1"):
    """Downgrade database to a specific revision."""
    if revision == "-1":
        description = "Downgrading database by 1 revision"
    else:
        description = f"Downgrading database to {revision}"

    return run_command(["alembic", "downgrade", revision], description)


def create_migration(message, autogenerate=True):
    """Create a new migration."""
    command = ["alembic", "revision"]
    if autogenerate:
        command.append("--autogenerate")
    command.extend(["-m", message])

    return run_command(command, f"Creating migration: {message}")


def show_history():
    """Show migration history."""
    return run_command(["alembic", "history", "--verbose"], "Showing migration history")


def show_current():
    """Show current database revision."""
    return run_command(
        ["alembic", "current", "--verbose"], "Showing current database revision"
    )


def show_heads():
    """Show head revisions."""
    return run_command(["alembic", "heads", "--verbose"], "Showing head revisions")


def stamp(revision):
    """Stamp database with a specific revision without running migrations."""
    return run_command(
        ["alembic", "stamp", revision], f"Stamping database with revision {revision}"
    )


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="KKUA Database Migration Manager")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Apply migrations")
    upgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="head",
        help="Revision to upgrade to (default: head)",
    )

    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Revert migrations")
    downgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="-1",
        help="Revision to downgrade to (default: -1)",
    )

    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument("message", help="Migration description")
    create_parser.add_argument(
        "--manual", action="store_true", help="Create empty migration (no autogenerate)"
    )

    # History command
    subparsers.add_parser("history", help="Show migration history")

    # Current command
    subparsers.add_parser("current", help="Show current database revision")

    # Heads command
    subparsers.add_parser("heads", help="Show head revisions")

    # Stamp command
    stamp_parser = subparsers.add_parser("stamp", help="Stamp database with revision")
    stamp_parser.add_argument("revision", help="Revision to stamp")

    # Parse arguments
    args = parser.parse_args()

    # Ensure we're in the backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)

    # Check if alembic is set up
    if not os.path.exists("alembic/env.py") and args.command != "init":
        print(
            "❌ Alembic is not initialized. Please run the init_alembic.py script first."
        )
        return False

    # Execute commands
    if args.command == "upgrade":
        return upgrade(args.revision)
    elif args.command == "downgrade":
        return downgrade(args.revision)
    elif args.command == "create":
        return create_migration(args.message, not args.manual)
    elif args.command == "history":
        return show_history()
    elif args.command == "current":
        return show_current()
    elif args.command == "heads":
        return show_heads()
    elif args.command == "stamp":
        return stamp(args.revision)
    else:
        parser.print_help()
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
