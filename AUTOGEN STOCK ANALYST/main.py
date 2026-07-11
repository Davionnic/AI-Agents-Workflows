#!/usr/bin/env python
"""CLI for the free Groq-powered AutoGen stock analyst."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from stock_analyst.team import CODING_DIR, run_analysis

DEFAULT_TASK = (
    "Analyze NVIDIA (NVDA) stock for the past 3 months. "
    "Fetch price history with yfinance, compute daily returns, "
    "20-day and 50-day moving averages, plot closing price with MAs, "
    "and write a short investment-style summary. "
    "This is educational analysis only, not financial advice."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-agent stock analyst powered by AG2 + Groq (free tier).",
    )
    parser.add_argument(
        "task",
        nargs="?",
        default=None,
        help="Analysis request. If omitted, uses an NVDA demo task.",
    )
    parser.add_argument(
        "--ticker",
        "-t",
        default=None,
        help="Shortcut: analyze this ticker for the past 3 months.",
    )
    parser.add_argument(
        "--period",
        "-p",
        default="3mo",
        help="yfinance period when using --ticker (default: 3mo).",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=12,
        help="Max group-chat rounds (default: 12).",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the final report under coding/reports/.",
    )
    return parser.parse_args()


def build_task(args: argparse.Namespace) -> str:
    if args.task:
        return args.task
    if args.ticker:
        ticker = args.ticker.upper().strip()
        return (
            f"Analyze {ticker} stock for the past period '{args.period}'. "
            "Fetch price history with yfinance, compute daily returns, "
            "20-day and 50-day moving averages, plot closing price with MAs, "
            "save the chart under figures/, and write a short Markdown summary. "
            "Educational analysis only — not financial advice."
        )
    return DEFAULT_TASK


def main() -> int:
    args = parse_args()
    task = build_task(args)

    print("=" * 60)
    print("AutoGen Stock Analyst (Groq free tier)")
    print("=" * 60)
    print(f"Task: {task}\n")
    print(f"Working dir: {CODING_DIR}\n")

    try:
        report = run_analysis(task, max_rounds=args.max_rounds)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — surface agent/API failures cleanly
        print(f"Run failed: {exc}", file=sys.stderr)
        return 1

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(report)

    if args.save and report:
        reports_dir = CODING_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = reports_dir / f"report_{stamp}.md"
        out.write_text(report.replace("TERMINATE", "").strip() + "\n", encoding="utf-8")
        print(f"\nSaved report to {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
