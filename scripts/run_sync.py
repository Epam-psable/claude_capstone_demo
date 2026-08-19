#!/usr/bin/env python3
"""CLI entry point for the Automated Documentation Sync engine."""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load project .env before importing sync_engine
_repo_root = Path(__file__).resolve().parent.parent
load_dotenv(_repo_root / ".env")

from sync_engine import Orchestrator  # noqa: E402  (after dotenv load)


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync Markdown documentation with Python source changes."
    )
    parser.add_argument(
        "--mode",
        choices=["manual", "pr"],
        required=True,
        help="'pr' uses git diff between two refs; 'manual' uses explicit file list or HEAD~1..HEAD",
    )
    parser.add_argument("--base-ref", default="HEAD~1", help="Base git ref for diff (pr mode)")
    parser.add_argument("--head-ref", default="HEAD", help="Head git ref for diff (pr mode)")
    parser.add_argument(
        "--changed-files",
        nargs="+",
        metavar="STATUS:PATH",
        help="Explicit changed files in 'status:path' format (manual mode)",
    )
    parser.add_argument(
        "--config",
        default=str(_repo_root / "config" / "sync_rules.yaml"),
        help="Path to sync_rules.yaml",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)

    orchestrator = Orchestrator(
        repo_root=_repo_root,
        config_path=Path(args.config),
        env_path=_repo_root / ".env",
    )

    if args.mode == "pr":
        return orchestrator.run(base_ref=args.base_ref, head_ref=args.head_ref)
    else:
        if args.changed_files:
            return orchestrator.run(changed_files=args.changed_files)
        else:
            return orchestrator.run(base_ref=args.base_ref, head_ref=args.head_ref)


if __name__ == "__main__":
    sys.exit(main())
