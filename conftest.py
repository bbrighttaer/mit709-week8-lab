"""pytest set-up for the MIT709 Week 5 lab (unchanged from Week 4). Do not edit.

Provides the store and conn fixtures used by test_booking_store.py.
"""
import importlib
import sqlite3

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--module",
        default="booking_store",
        help="name of the module to test, without .py (default: booking_store)",
    )


@pytest.fixture
def store(request):
    """Import the module named by --module."""
    return importlib.import_module(request.config.getoption("--module"))


@pytest.fixture
def conn(store):
    """An in-memory StudySpace database with four rooms in two buildings."""
    db = sqlite3.connect(":memory:")
    store.create_schema(db)
    store.add_room(db, "Library", "L1.01", 4)
    store.add_room(db, "Library", "L1.02", 8)
    store.add_room(db, "Library", "L2.01", 2)
    store.add_room(db, "Science", "S1.10", 6)
    yield db
    db.close()
