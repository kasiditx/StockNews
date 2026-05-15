from __future__ import annotations

from pathlib import Path

from stock_alerts.cli import _build_parser


def test_watchlist_argument_is_supported_before_command() -> None:
    parser = _build_parser()

    args = parser.parse_args(["--watchlist", "config/custom.json", "watch"])

    assert args.command == "watch"
    assert args.watchlist == Path("config/custom.json")


def test_watchlist_argument_is_supported_after_command() -> None:
    parser = _build_parser()

    args = parser.parse_args(["watch", "--watchlist", "config/custom.json"])

    assert args.command == "watch"
    assert args.watchlist == Path("config/custom.json")


def test_watchlist_argument_is_optional() -> None:
    parser = _build_parser()

    args = parser.parse_args(["watch"])

    assert args.command == "watch"
    assert args.watchlist is None
