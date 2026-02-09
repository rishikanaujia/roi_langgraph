#!/usr/bin/env python3
"""
Gradio UI Launcher - UI Module Version

Quick launcher script for the Gradio web interface from ui/ directory.

Usage:
    # From project root
    python -m ui.launch
    python ui/launch.py

    # With options
    python -m ui.launch --share
    python -m ui.launch --port 7860
"""

import argparse
import sys
from pathlib import Path

# Add project root to path if not already there
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def main():
    parser = argparse.ArgumentParser(
        description="Launch Gradio UI for Renewable Energy Ranking System"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to run Gradio server (default: 7860)"
    )

    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public share link (default: False)"
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (default: False)"
    )

    args = parser.parse_args()

    # Import and launch
    from ui.gradio_app import create_gradio_interface

    print("=" * 70)
    print("🌍 Renewable Energy Investment Ranking System - Gradio UI")
    print("=" * 70)
    print(f"Server: http://{args.host}:{args.port}")
    if args.share:
        print("Share link will be generated...")
    print("=" * 70)
    print()

    # Create and launch
    demo = create_gradio_interface()

    demo.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        show_error=True,
        debug=args.debug
    )


if __name__ == "__main__":
    main()