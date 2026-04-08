"""OpenEnv validator entry point — exposes app and a callable main()."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bug_triage_env"))

from server import app  # noqa: F401


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
