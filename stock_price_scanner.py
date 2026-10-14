"""Print the latest reported regular-session quotes from Yahoo Finance."""

import argparse
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import math
import sys

import yfinance as yf

DEFAULT_SYMBOLS = ("BABA", "MOMO", "AMZN")


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: float
    previous_close: float
    currency: str
    as_of: datetime

    @property
    def change(self):
        return self.price - self.previous_close

    @property
    def percent_change(self):
        return 100 * self.change / self.previous_close


def parse_quote(symbol, metadata):
    """Reject incomplete responses instead of printing misleading prices."""
    if not isinstance(metadata, Mapping) or metadata.get("symbol") != symbol:
        raise ValueError("provider returned no matching quote")

    def price_field(key):
        value = metadata.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"provider returned invalid {key}")
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"provider returned invalid {key}")
        return float(value)

    price = price_field("regularMarketPrice")
    previous_close = price_field("previousClose")
    currency = metadata.get("currency")
    if not isinstance(currency, str) or not currency.isalpha() or len(currency) > 5:
        raise ValueError("provider returned no valid currency")

    # yfinance formats this field as an aware datetime; accept Unix seconds too.
    timestamp = metadata.get("regularMarketTime")
    if not isinstance(timestamp, bool) and isinstance(timestamp, (int, float)):
        try:
            timestamp = datetime.fromtimestamp(timestamp, timezone.utc)
        except (ValueError, OverflowError, OSError):
            raise ValueError("provider returned an invalid quote timestamp") from None
    if not isinstance(timestamp, datetime) or timestamp.utcoffset() is None:
        raise ValueError("provider returned no timezone-aware quote timestamp")

    return Quote(symbol, price, previous_close, currency, timestamp.astimezone(timezone.utc))


def fetch_quote(symbol):
    ticker = yf.Ticker(symbol)
    # Intraday metadata's previousClose is the prior session's close. A multi-day
    # chartPreviousClose can instead refer to the start of the requested range.
    ticker.history(period="1d", interval="1m", auto_adjust=False,
                   actions=False, timeout=15)
    return parse_quote(symbol, ticker.get_history_metadata())


def format_quote(quote):
    return (
        f"{quote.symbol}: {quote.price:.2f} {quote.currency} "
        f"(regular session, as of {quote.as_of:%Y-%m-%d %H:%M:%S UTC})\n"
        f"  Previous close: {quote.previous_close:.2f}; "
        f"change: {quote.change:+.2f} ({quote.percent_change:+.2f}%)"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("symbols", nargs="*", help="Yahoo symbols (default: BABA MOMO AMZN)")
    args = parser.parse_args(argv)
    # Propagate provider failures to our per-symbol handler instead of hiding them.
    yf.config.debug.hide_exceptions = False
    failed = False
    print("Latest reported quotes; data may be delayed. Check each quote's timestamp.")
    for symbol in args.symbols or DEFAULT_SYMBOLS:
        symbol = symbol.strip().upper()
        try:
            print(format_quote(fetch_quote(symbol)))
        except Exception as exc:
            print(f"{symbol}: quote unavailable ({exc})", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
