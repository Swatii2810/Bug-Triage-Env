"""Entry point for openenv validate — imports the FastAPI app from bug_triage_env."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bug_triage_env"))

from server import app  # noqa: F401 — re-exported for openenv validator
