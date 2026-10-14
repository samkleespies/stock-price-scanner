from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import unittest
from unittest.mock import patch

import stock_price_scanner as scanner


class ScannerTests(unittest.TestCase):
    def metadata(self, **changes):
        result = dict(symbol="BABA", regularMarketPrice=101.5, previousClose=100.0,
                      currency="USD", regularMarketTime=1729022400)
        result.update(changes)
        return result

    def test_signed_change_for_rising_falling_and_flat_prices(self):
        for price, expected in ((101.5, 1.5), (98.5, -1.5), (100.0, 0.0)):
            with self.subTest(price=price):
                quote = scanner.parse_quote("BABA", self.metadata(regularMarketPrice=price))
                self.assertEqual(quote.previous_close, 100.0)
                self.assertEqual(quote.change, expected)
                self.assertEqual(quote.percent_change, expected)

    def test_percent_change_uses_previous_close(self):
        quote = scanner.parse_quote("BABA", self.metadata(regularMarketPrice=90, previousClose=120))
        self.assertEqual(quote.percent_change, -25)

    def test_invalid_prices_are_rejected(self):
        for key in ("regularMarketPrice", "previousClose"):
            for value in (None, 0, -1, float("nan"), float("inf"), True, "100"):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    scanner.parse_quote("BABA", self.metadata(**{key: value}))

    def test_incomplete_and_wrong_symbol_responses_are_rejected(self):
        for data in (None, {}, self.metadata(symbol="AMZN"), self.metadata(currency=None)):
            with self.subTest(data=data), self.assertRaises(ValueError):
                scanner.parse_quote("BABA", data)

    def test_chart_range_close_is_not_used_as_previous_session_close(self):
        data = self.metadata(chartPreviousClose=80)
        del data["previousClose"]
        with self.assertRaises(ValueError):
            scanner.parse_quote("BABA", data)

    def test_bad_or_ambiguous_timestamps_are_rejected(self):
        for value in (None, True, float("nan"), float("inf"), 10**30,
                      "2024-10-15", datetime(2024, 10, 15)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                scanner.parse_quote("BABA", self.metadata(regularMarketTime=value))

    def test_provider_time_is_displayed_in_utc_even_for_old_quotes(self):
        timestamp = datetime(2024, 10, 15, 16, tzinfo=timezone(timedelta(hours=-4)))
        quote = scanner.parse_quote("BABA", self.metadata(regularMarketTime=timestamp))
        output = scanner.format_quote(quote)
        self.assertIn("as of 2024-10-15 20:00:00 UTC", output)
        self.assertIn("101.50 USD", output)
        self.assertIn("change: +1.50 (+1.50%)", output)

    @patch.object(scanner.yf, "Ticker")
    def test_fetch_uses_intraday_metadata(self, ticker_class):
        ticker = ticker_class.return_value
        ticker.get_history_metadata.return_value = self.metadata()
        quote = scanner.fetch_quote("BABA")
        self.assertEqual(quote.price, 101.5)
        ticker.history.assert_called_once_with(period="1d", interval="1m",
                                              auto_adjust=False, actions=False, timeout=15)

    @patch.object(scanner, "fetch_quote")
    def test_partial_failure_continues_and_returns_failure(self, fetch):
        quote = scanner.parse_quote("BABA", self.metadata())
        fetch.side_effect = [RuntimeError("network timeout"), quote]
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = scanner.main(["bad", "baba"])
        self.assertEqual(result, 1)
        self.assertEqual([call.args[0] for call in fetch.call_args_list], ["BAD", "BABA"])
        self.assertIn("BABA: 101.50 USD", stdout.getvalue())
        self.assertIn("BAD: quote unavailable (network timeout)", stderr.getvalue())

    @patch.object(scanner, "fetch_quote")
    def test_defaults_and_success_exit_status(self, fetch):
        fetch.return_value = scanner.parse_quote("BABA", self.metadata())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(scanner.main([]), 0)
        self.assertEqual([call.args[0] for call in fetch.call_args_list], ["BABA", "MOMO", "AMZN"])


if __name__ == "__main__":
    unittest.main()
