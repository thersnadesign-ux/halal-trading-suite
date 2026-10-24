"""Cash-account position sizing and T+2 settlement tracker."""

from __future__ import annotations

import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from auth import check_login, render_home_link


TRACKER_FILE = Path(__file__).with_name("settlement_tracker.json")
TRACKER_COLUMNS = [
    "Ticker",
    "Modal Dipakai ($)",
    "Tanggal Transaksi",
    "Tanggal Settle (T+2)",
]


def calculate_settlement_date(transaction_date: date) -> date:
    """Return the date two weekdays after the transaction date."""
    return (pd.Timestamp(transaction_date) + pd.offsets.BusinessDay(2)).date()


def load_settlement_records() -> list[dict[str, Any]]:
    """Load and validate settlement records from the local JSON file."""
    if not TRACKER_FILE.exists():
        return []

    with TRACKER_FILE.open("r", encoding="utf-8") as tracker_file:
        records = json.load(tracker_file)

    if not isinstance(records, list):
        raise ValueError("Format settlement_tracker.json harus berupa daftar.")

    required_keys = {
        "ticker",
        "amount_used",
        "transaction_date",
        "settlement_date",
    }
    for record in records:
        if not isinstance(record, dict) or not required_keys.issubset(record):
            raise ValueError("Ada record yang formatnya tidak valid di file tracker.")
        date.fromisoformat(record["transaction_date"])
        date.fromisoformat(record["settlement_date"])
        try:
            amount = float(record["amount_used"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Modal dipakai pada file tracker harus berupa angka.") from exc
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("Modal dipakai pada file tracker tidak valid.")

    return records


def save_settlement_records(records: list[dict[str, Any]]) -> None:
    """Persist settlement records to the local JSON file."""
    with TRACKER_FILE.open("w", encoding="utf-8") as tracker_file:
        json.dump(records, tracker_file, indent=2, ensure_ascii=False)


def _render_position_sizing() -> None:
    st.subheader("Kalkulator Position Sizing")
    st.caption(
        "Hitung ukuran posisi berdasarkan risiko per trade dan batas penggunaan "
        "modal untuk cash account."
    )

    inputs = st.columns(2)
    account_capital = inputs[0].number_input(
        "Total Modal Akun ($)",
        min_value=0.0,
        value=10000.0,
        step=100.0,
        format="%.2f",
    )
    entry_price = inputs[1].number_input(
        "Harga Entry ($)",
        min_value=0.0,
        value=10.0,
        step=0.1,
        format="%.2f",
    )
    stop_loss = inputs[0].number_input(
        "Harga Stop Loss ($)",
        min_value=0.0,
        value=9.5,
        step=0.1,
        format="%.2f",
    )
    max_risk = inputs[1].number_input(
        "Maksimal Risiko per Trade ($)",
        min_value=0.0,
        value=100.0,
        step=10.0,
        format="%.2f",
    )

    if stop_loss >= entry_price:
        st.error("Harga Stop Loss harus lebih rendah dari Harga Entry.")
        return

    stop_distance = entry_price - stop_loss
    shares = math.floor(max_risk / stop_distance) if stop_distance > 0 else 0
    required_capital = shares * entry_price
    safe_daily_limit = account_capital / 3

    if required_capital > safe_daily_limit:
        st.warning(
            "Modal Dibutuhkan melebihi Batas Aman Harian (sepertiga modal akun). "
            "Menggunakan dana yang belum settle dapat meningkatkan risiko GFV "
            "pada cash account."
        )

    metrics = st.columns(3)
    metrics[0].metric("Jumlah Lembar (Shares)", f"{shares:,}")
    metrics[1].metric("Modal Dibutuhkan", f"${required_capital:,.2f}")
    metrics[2].metric("Jarak SL", f"${stop_distance:,.2f}")
    st.caption(f"Batas Aman Harian: ${safe_daily_limit:,.2f}")


def _render_settlement_tracker() -> None:
    st.subheader("Tracker T+2 Settlement")
    st.caption(
        "Tanggal settle dihitung sebagai dua hari kerja setelah transaksi "
        "(tidak termasuk Sabtu dan Minggu)."
    )

    try:
        records = load_settlement_records()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        st.error(f"Tidak dapat membaca data settlement: {exc}")
        st.stop()

    with st.form("new_settlement_trade"):
        columns = st.columns(3)
        ticker = columns[0].text_input("Ticker", placeholder="Contoh: AAPL")
        amount_used = columns[1].number_input(
            "Total Modal Dipakai ($)",
            min_value=0.01,
            value=100.0,
            step=10.0,
            format="%.2f",
        )
        transaction_date = columns[2].date_input(
            "Tanggal Transaksi",
            value=date.today(),
        )
        submitted = st.form_submit_button(
            "Catat Trade Baru",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not ticker.strip():
            st.warning("Ticker wajib diisi sebelum trade dicatat.")
        else:
            records.append(
                {
                    "ticker": ticker.strip().upper(),
                    "amount_used": round(amount_used, 2),
                    "transaction_date": transaction_date.isoformat(),
                    "settlement_date": calculate_settlement_date(
                        transaction_date
                    ).isoformat(),
                }
            )
            try:
                save_settlement_records(records)
            except OSError as exc:
                st.error(f"Tidak dapat menyimpan data settlement: {exc}")
                st.stop()
            st.success(f"Trade {ticker.strip().upper()} berhasil dicatat.")

    if st.button("Bersihkan Data yang Sudah Settle"):
        today = date.today()
        active_records = [
            record
            for record in records
            if date.fromisoformat(record["settlement_date"]) > today
        ]
        removed_count = len(records) - len(active_records)
        try:
            save_settlement_records(active_records)
        except OSError as exc:
            st.error(f"Tidak dapat memperbarui data settlement: {exc}")
            st.stop()
        records = active_records
        st.success(f"{removed_count} trade yang sudah settle dihapus.")

    table_rows = [
        {
            "Ticker": record["ticker"],
            "Modal Dipakai ($)": float(record["amount_used"]),
            "Tanggal Transaksi": record["transaction_date"],
            "Tanggal Settle (T+2)": record["settlement_date"],
        }
        for record in records
    ]
    table = pd.DataFrame(table_rows, columns=TRACKER_COLUMNS)
    st.dataframe(table, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="T+2 Cash Settlement & Risk Tracker",
        page_icon="📊",
        layout="wide",
    )
    render_home_link()
    st.title("📊 T+2 Cash Settlement & Risk Tracker")
    st.caption(
        "Position sizing dan pemantauan settlement untuk cash account "
        "(tanpa margin)."
    )

    position_tab, settlement_tab = st.tabs(
        ["Kalkulator Position Sizing", "Tracker T+2 Settlement"]
    )
    with position_tab:
        _render_position_sizing()
    with settlement_tab:
        _render_settlement_tracker()


if __name__ == "__main__":
    check_login()
    main()
