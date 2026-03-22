"""
Shared pytest fixtures for Insight-Engine test suite.
"""

import os

import pytest

# Set required env vars before any project module is imported.
# These are test-only values — never real credentials.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-32chars!!")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("NEO4J_PASSWORD", "test-password")
