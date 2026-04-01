"""
server/app.py — Entry point for openenv multi-mode deployment.
"""
import sys
import os

# Add parent dir to path so root-level modules are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: F401
import uvicorn


def main():
    """Server entry point called by openenv multi-mode deployment."""
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
