# Stock Price Scanner

Print the latest reported regular-session prices for BABA, MOMO and AMZN,
including currency, quote timestamp, previous session's close and signed change.
The old Investopedia HTML feed is no longer usable. Quotes now come from Yahoo
Finance's chart metadata through [yfinance](https://github.com/ranaroussi/yfinance).

## Install and run

Use Python 3.11 or newer in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python stock_price_scanner.py
```

Optionally specify Yahoo ticker symbols:

```bash
python stock_price_scanner.py AAPL MSFT
```

Quotes may be delayed, and closed markets retain the last reported quote. The
UTC timestamp is the provider's quote time, not the time the script ran. The
previous close refers to the preceding trading session, which may not be
yesterday. Extended-hours prices are not included.

Unavailable symbols, network errors and incomplete responses are reported on
stderr. Other symbols are still processed; the program exits with status 1 if
any quote failed. Requests use the client's timeouts (15 seconds for the history
request; client setup may make additional requests). No credentials are needed.

Yahoo can change or restrict this public feed. yfinance is an independent client,
not an official Yahoo product; see its documentation and Yahoo's terms for data
usage. This practice project is intended for personal, educational use.

## Test

```bash
python -m unittest discover -s tests -v
```

Tests use fixed responses and never contact the quote provider. CI runs them on
Python 3.11 and 3.13; a live quote check requires network access.
