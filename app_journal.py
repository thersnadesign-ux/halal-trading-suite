"""Halal Trade Journal & Dashboard using Streamlit and SQLite."""

from contextlib import closing
from datetime import date
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

from auth import check_login, render_home_link


DB_PATH = Path(__file__).with_name("journal.db")
TRADE_COLUMNS = [
    "id",
    "date",
    "ticker",
    "entry_price",
    "exit_price",
    "shares",
    "pnl",
    "notes",
]


def get_connection() -> sqlite3.Connection:
    """Create a SQLite connection to the local journal database."""
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Create the trades table if it does not already exist."""
    with closing(get_connection()) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    shares INTEGER NOT NULL,
                    pnl REAL NOT NULL,
                    notes TEXT NOT NULL DEFAULT ''
                )
                """
            )


def insert_trade(
    trade_date: date,
    ticker: str,
    entry_price: float,
    exit_price: float,
    shares: int,
    notes: str,
) -> None:
    """Calculate and insert one trade, returning via the database transaction."""
    pnl = (exit_price - entry_price) * shares
    with closing(get_connection()) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO trades
                    (date, ticker, entry_price, exit_price, shares, pnl, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade_date.isoformat(),
                    ticker.strip().upper(),
                    entry_price,
                    exit_price,
                    shares,
                    pnl,
                    notes.strip(),
                ),
            )


def load_trades() -> pd.DataFrame:
    """Read all trades from SQLite into a DataFrame."""
    with closing(get_connection()) as connection:
        return pd.read_sql_query(
            """
            SELECT id, date, ticker, entry_price, exit_price, shares, pnl, notes
            FROM trades
            ORDER BY date ASC, id ASC
            """,
            connection,
        )


def delete_trade(trade_id: int) -> int:
    """Delete one trade by ID and return the number of deleted rows."""
    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM trades WHERE id = ?",
                (trade_id,),
            )
            return cursor.rowcount


def _show_flash_message() -> None:
    message = st.session_state.pop("journal_flash_message", None)
    if message:
        st.success(message)


def _render_trade_form() -> None:
    st.subheader("Form Input Jurnal")

    with st.form("trade_journal_form", clear_on_submit=True):
        trade_date = st.date_input("Tanggal", value=date.today())
        ticker = st.text_input("Ticker", placeholder="Contoh: AAPL")
        entry_price = st.number_input(
            "Harga Entry ($)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
        )
        exit_price = st.number_input(
            "Harga Exit ($)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
        )
        shares = st.number_input(
            "Jumlah Lembar / Shares",
            min_value=1,
            value=1,
            step=1,
        )
        notes = st.text_area("Catatan / Notes", placeholder="Catatan trade...")
        submitted = st.form_submit_button(
            "Simpan Trade",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return
    if not ticker.strip():
        st.error("Ticker wajib diisi.")
        return
    if entry_price <= 0 or exit_price <= 0:
        st.error("Harga entry dan exit harus lebih besar dari nol.")
        return

    try:
        insert_trade(
            trade_date,
            ticker,
            entry_price,
            exit_price,
            int(shares),
            notes,
        )
    except sqlite3.Error as exc:
        st.error(f"Gagal menyimpan trade ke database: {exc}")
        return

    st.session_state["journal_flash_message"] = (
        f"Trade {ticker.strip().upper()} berhasil disimpan."
    )
    st.rerun()


def _render_performance_dashboard(trades: pd.DataFrame) -> None:
    st.subheader("Dashboard Performa")
    if trades.empty:
        st.info("Belum ada data trading")
        return

    total_trades = len(trades)
    win_rate = (int((trades["pnl"] > 0).sum()) / total_trades) * 100
    total_pnl = float(trades["pnl"].sum())

    metrics = st.columns(3)
    metrics[0].metric("Total Trades", f"{total_trades}")
    metrics[1].metric("Win Rate", f"{win_rate:.1f}%")
    metrics[2].metric("Total PnL", f"${total_pnl:,.2f}")

    chart_data = trades.copy()
    chart_data["date"] = pd.to_datetime(chart_data["date"], errors="coerce")
    chart_data = chart_data.dropna(subset=["date"]).sort_values(
        ["date", "id"],
        kind="stable",
    )
    chart_data["Cumulative PnL ($)"] = chart_data["pnl"].cumsum()
    if not chart_data.empty:
        chart_data = chart_data.set_index("date")
        st.line_chart(chart_data["Cumulative PnL ($)"])


def _render_trade_history(trades: pd.DataFrame) -> None:
    st.subheader("Riwayat Transaksi")
    if trades.empty:
        st.info("Belum ada riwayat transaksi untuk ditampilkan.")
        return

    st.dataframe(
        trades[TRADE_COLUMNS],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Hapus Trade")
    delete_columns = st.columns([1, 1])
    trade_id = delete_columns[0].number_input(
        "ID Trade yang ingin dihapus",
        min_value=1,
        value=1,
        step=1,
    )
    if delete_columns[1].button(
        "Hapus Trade",
        type="secondary",
        use_container_width=True,
    ):
        try:
            deleted_rows = delete_trade(int(trade_id))
        except sqlite3.Error as exc:
            st.error(f"Gagal menghapus trade: {exc}")
            return

        if deleted_rows == 0:
            st.warning(f"Tidak ditemukan trade dengan ID {int(trade_id)}.")
            return
        st.session_state["journal_flash_message"] = (
            f"Trade dengan ID {int(trade_id)} berhasil dihapus."
        )
        st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="Halal Trade Journal & Dashboard",
        page_icon="📔",
        layout="wide",
    )
    render_home_link()
    st.title("📔 Halal Trade Journal & Dashboard")
    st.caption("Catat performa trade dan pantau ringkasan PnL Anda.")

    try:
        init_db()
        trades = load_trades()
    except (sqlite3.Error, pd.errors.DatabaseError) as exc:
        st.error(f"Gagal mengakses journal.db: {exc}")
        st.stop()

    _show_flash_message()
    left_column, right_column = st.columns([1, 2])
    with left_column:
        _render_trade_form()
    with right_column:
        _render_performance_dashboard(trades)

    st.divider()
    _render_trade_history(trades)


if __name__ == "__main__":
    check_login()
    main()
