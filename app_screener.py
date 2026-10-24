"""Halal Momentum Stock Screener built with Streamlit and yfinance."""

from __future__ import annotations

import io
import math
from typing import Any

import pandas as pd
import streamlit as st
import yfinance as yf

from auth import check_login, render_home_link


DISPLAY_COLUMNS = [
    "Ticker",
    "Current Price ($)",
    "Gap Up (%)",
    "RVOL",
    "Debt to Asset (%)",
    "Interest to Revenue (%)",
    "Status Syariah",
]
NUMERIC_COLUMNS = [
    "Current Price ($)",
    "Gap Up (%)",
    "RVOL",
    "Debt to Asset (%)",
    "Interest to Revenue (%)",
]


def _number(value: Any) -> float | None:
    """Return a finite float for numeric-like values, otherwise None."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _statement_value(
    statement: pd.DataFrame,
    row_names: tuple[str, ...],
) -> float | None:
    """Get the latest value for a matching row in a yfinance statement."""
    if not isinstance(statement, pd.DataFrame) or statement.empty:
        return None

    normalized_rows = {
        str(row).strip().lower(): row
        for row in statement.index
    }
    matched_row = None
    for requested_name in row_names:
        requested = requested_name.strip().lower()
        if requested in normalized_rows:
            matched_row = normalized_rows[requested]
            break

    if matched_row is None:
        for requested_name in row_names:
            requested = requested_name.strip().lower()
            matched_row = next(
                (
                    original
                    for normalized, original in normalized_rows.items()
                    if requested in normalized
                ),
                None,
            )
            if matched_row is not None:
                break

    if matched_row is None:
        return None

    values = statement.loc[matched_row]
    if isinstance(values, pd.Series):
        for value in values:
            number = _number(value)
            if number is not None:
                return number
        return None
    return _number(values)


def _first_number(source: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        number = _number(source.get(key))
        if number is not None:
            return number
    return None


def _fetch_ticker_data(ticker_symbol: str) -> tuple[dict[str, Any], str | None]:
    """Fetch market and fundamental data for one ticker."""
    ticker = yf.Ticker(ticker_symbol)
    info: dict[str, Any] = {}
    fetch_errors: list[str] = []

    try:
        info = ticker.info or {}
    except Exception as exc:
        fetch_errors.append(f"info: {exc}")

    history = pd.DataFrame()
    try:
        history = ticker.history(period="5d", auto_adjust=False)
    except Exception as exc:
        fetch_errors.append(f"history: {exc}")

    current_price = _first_number(
        info,
        ("currentPrice", "regularMarketPrice", "navPrice"),
    )
    previous_close = _first_number(info, ("previousClose", "regularMarketPreviousClose"))
    current_volume = _first_number(info, ("regularMarketVolume", "volume"))
    average_volume = _first_number(info, ("averageVolume", "averageVolume10days"))

    if not history.empty:
        if current_price is None and "Close" in history:
            current_price = _number(history["Close"].iloc[-1])
        if previous_close is None and len(history) >= 2 and "Close" in history:
            previous_close = _number(history["Close"].iloc[-2])
        if current_volume is None and "Volume" in history:
            current_volume = _number(history["Volume"].iloc[-1])

    if average_volume is None and not history.empty and "Volume" in history:
        average_volume = _number(history["Volume"].mean())

    balance_sheet = pd.DataFrame()
    try:
        balance_sheet = ticker.balance_sheet
    except Exception as exc:
        fetch_errors.append(f"balance sheet: {exc}")

    income_statement = pd.DataFrame()
    try:
        income_statement = ticker.income_stmt
    except Exception as exc:
        fetch_errors.append(f"income statement: {exc}")
    if income_statement.empty:
        try:
            income_statement = ticker.financials
        except Exception as exc:
            fetch_errors.append(f"financials: {exc}")

    total_debt = _statement_value(balance_sheet, ("Total Debt",))
    if total_debt is None:
        total_debt = _number(info.get("totalDebt"))
    total_assets = _statement_value(balance_sheet, ("Total Assets",))
    total_revenue = _statement_value(income_statement, ("Total Revenue",))
    interest_income = _statement_value(
        income_statement,
        ("Interest Income", "Interest Income Non Operating"),
    )

    gap_up = None
    if current_price is not None and previous_close not in (None, 0):
        gap_up = ((current_price - previous_close) / previous_close) * 100

    rvol = None
    if current_volume is not None and average_volume not in (None, 0):
        rvol = current_volume / average_volume

    debt_to_asset = None
    if total_debt is not None and total_assets not in (None, 0):
        debt_to_asset = (total_debt / total_assets) * 100

    interest_to_revenue = None
    if interest_income is not None and total_revenue not in (None, 0):
        interest_to_revenue = (interest_income / total_revenue) * 100

    row = {
        "Ticker": ticker_symbol,
        "Current Price ($)": current_price,
        "Gap Up (%)": gap_up,
        "RVOL": rvol,
        "Debt to Asset (%)": debt_to_asset,
        "Interest to Revenue (%)": interest_to_revenue,
    }
    has_any_data = any(value is not None for key, value in row.items() if key != "Ticker")
    warning = None
    if not has_any_data:
        detail = f" Detail: {'; '.join(fetch_errors)}" if fetch_errors else ""
        warning = f"Ticker {ticker_symbol} tidak ditemukan atau datanya tidak tersedia.{detail}"

    return row, warning


def _parse_tickers(raw_tickers: str) -> list[str]:
    """Parse comma-separated tickers and remove duplicates."""
    tickers: list[str] = []
    for part in raw_tickers.split(","):
        ticker = part.strip().upper()
        if ticker and ticker not in tickers:
            tickers.append(ticker)
    return tickers


def _format_missing_values(dataframe: pd.DataFrame) -> pd.DataFrame:
    formatted = dataframe.copy()
    for column in NUMERIC_COLUMNS:
        formatted[column] = formatted[column].map(
            lambda value: "N/A" if pd.isna(value) else value
        )
    return formatted


def main() -> None:
    st.set_page_config(
        page_title="Halal Momentum Stock Screener",
        page_icon="📈",
        layout="wide",
    )
    render_home_link()
    st.title("📈 Halal Momentum Stock Screener")
    st.caption(
        "Saring saham berdasarkan momentum dan rasio fundamental. "
        "Data bersumber dari yfinance dan bukan nasihat investasi."
    )

    with st.sidebar:
        st.header("Filter Screener")
        st.caption("Rentang slider mengikuti data yang berhasil diambil.")

        raw_results = st.session_state.get("screener_results", [])
        data = pd.DataFrame(raw_results)

        def observed_max(column: str, minimum: float) -> float:
            if column not in data:
                return minimum
            values = pd.to_numeric(data[column], errors="coerce").dropna()
            return max(minimum, float(values.max())) if not values.empty else minimum

        max_price = st.slider(
            "Max Price ($)",
            min_value=0.0,
            max_value=max(
                observed_max("Current Price ($)", 15.0),
                float(st.session_state.get("max_price_filter", 15.0)),
            ),
            value=15.0,
            step=0.5,
            key="max_price_filter",
        )
        min_gap = st.slider(
            "Min Gap Up (%)",
            min_value=0.0,
            max_value=max(
                observed_max("Gap Up (%)", 5.0),
                float(st.session_state.get("min_gap_filter", 5.0)),
            ),
            value=5.0,
            step=0.5,
            key="min_gap_filter",
        )
        min_rvol = st.slider(
            "Min RVOL",
            min_value=0.0,
            max_value=max(
                observed_max("RVOL", 2.0),
                float(st.session_state.get("min_rvol_filter", 2.0)),
            ),
            value=2.0,
            step=0.1,
            key="min_rvol_filter",
        )
        max_debt_asset = st.slider(
            "Max Debt/Asset (%)",
            min_value=0.0,
            max_value=max(
                observed_max("Debt to Asset (%)", 30.0),
                float(st.session_state.get("max_debt_asset_filter", 30.0)),
            ),
            value=30.0,
            step=1.0,
            key="max_debt_asset_filter",
        )
        max_interest_revenue = st.slider(
            "Max Interest/Revenue (%)",
            min_value=0.0,
            max_value=max(
                observed_max("Interest to Revenue (%)", 5.0),
                float(st.session_state.get("max_interest_revenue_filter", 5.0)),
            ),
            value=5.0,
            step=0.5,
            key="max_interest_revenue_filter",
        )

    with st.form("screener_form"):
        raw_tickers = st.text_input(
            "Ticker Saham (pisahkan dengan koma)",
            placeholder="Contoh: AAPL, NVDA, MSFT",
        )
        submitted = st.form_submit_button(
            "Jalankan Screener",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        tickers = _parse_tickers(raw_tickers)
        if not tickers:
            st.warning("Masukkan minimal satu ticker saham yang dipisahkan koma.")
        else:
            rows: list[dict[str, Any]] = []
            warnings: list[str] = []
            progress = st.progress(0, text="Mengambil data saham...")
            for index, ticker_symbol in enumerate(tickers, start=1):
                try:
                    row, warning = _fetch_ticker_data(ticker_symbol)
                    rows.append(row)
                    if warning:
                        warnings.append(warning)
                except Exception as exc:
                    warnings.append(
                        f"Gagal mengambil data {ticker_symbol}: {exc}"
                    )
                    rows.append(
                        {
                            "Ticker": ticker_symbol,
                            **{column: None for column in NUMERIC_COLUMNS},
                        }
                    )
                progress.progress(
                    index / len(tickers),
                    text=f"Mengambil data {ticker_symbol} ({index}/{len(tickers)})",
                )
            progress.empty()
            st.session_state["screener_results"] = rows
            st.session_state["screener_warnings"] = warnings

    warnings = st.session_state.get("screener_warnings", [])
    for warning in warnings:
        st.warning(warning)

    raw_results = st.session_state.get("screener_results", [])
    if not raw_results:
        st.info("Masukkan ticker lalu jalankan screener untuk melihat hasil.")
        return

    results = pd.DataFrame(raw_results)
    for column in NUMERIC_COLUMNS:
        results[column] = pd.to_numeric(results[column], errors="coerce")
    results["Status Syariah"] = "N/A"

    has_ratios = results["Debt to Asset (%)"].notna() & results[
        "Interest to Revenue (%)"
    ].notna()
    compliant = (
        (results["Debt to Asset (%)"] < max_debt_asset)
        & (results["Interest to Revenue (%)"] < max_interest_revenue)
    )
    results.loc[has_ratios & compliant, "Status Syariah"] = "Compliant"
    results.loc[has_ratios & ~compliant, "Status Syariah"] = "Non-Compliant"

    filtered = results[
        results["Current Price ($)"].notna()
        & (results["Current Price ($)"] <= max_price)
        & results["Gap Up (%)"].notna()
        & (results["Gap Up (%)"] >= min_gap)
        & results["RVOL"].notna()
        & (results["RVOL"] >= min_rvol)
        & results["Debt to Asset (%)"].notna()
        & (results["Debt to Asset (%)"] < max_debt_asset)
        & results["Interest to Revenue (%)"].notna()
        & (results["Interest to Revenue (%)"] < max_interest_revenue)
    ].copy()

    st.subheader(f"Hasil Screener ({len(filtered)} saham lolos)")
    st.dataframe(
        _format_missing_values(filtered[DISPLAY_COLUMNS]),
        use_container_width=True,
        hide_index=True,
    )

    csv_buffer = io.StringIO()
    filtered[DISPLAY_COLUMNS].to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Unduh hasil sebagai CSV",
        data=csv_buffer.getvalue().encode("utf-8-sig"),
        file_name="halal_momentum_screener.csv",
        mime="text/csv",
        use_container_width=True,
    )


if __name__ == "__main__":
    check_login()
    main()
