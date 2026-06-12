from argparse import ArgumentParser
from pathlib import Path
from typing import Sequence


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Plot Essemtec/UT325F temperature measurement CSV files.")
    parser.add_argument(
        "csv_file",
        nargs="?",
        type=Path,
        help="Optional CSV file path. If omitted, the chart opens without loading data.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    from essemtec.app import run_app

    return run_app(args.csv_file)
