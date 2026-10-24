"""Halal pre-trade checklist with local auto-save and JSON backup support."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from auth import check_login, render_home_link


CACHE_PATH = Path(__file__).with_name(".checklist_cache.json")
UPLOADER_KEY = "checklist_import_file"
INITIALIZED_KEY = "_checklist_initialized"
LAST_IMPORT_KEY = "_checklist_last_import_digest"
CACHE_ERROR_KEY = "_checklist_cache_error"
RESET_MESSAGE_KEY = "_checklist_reset_message"

CHECKLIST_SECTIONS = {
    "Section 1: Filter Syariah": {
        "zoya_compliant": "Zoya Compliant",
        "clear_news_catalyst": "Katalis Berita Jelas",
        "rvol_above_2": "RVOL > 2.0",
        "float_below_20m": "Float < 20M",
    },
    "Section 2: Tren & Struktur": {
        "price_above_vwap": "Harga di atas VWAP",
        "ema_9_above_20": "EMA 9 > EMA 20",
        "impulse_wave_hod": "Impulse Wave / HOD terbentuk",
    },
    "Section 3: Area Fibo & Volume": {
        "pullback_fibo_zone": "Harga pullback ke Fibo 0.382-0.618",
        "volume_drying_on_drop": "Volume mengering saat turun",
    },
    "Section 4: Trigger Entry": {
        "reversal_in_golden_zone": "Candle reversal di Golden Zone",
        "reversal_volume_spike": "Volume spike pada candle pembalikan",
        "close_above_ema_9": "Close > EMA 9",
    },
    "Section 5: Risk Management": {
        "cash_account_sizing": "Sizing sesuai cash account",
        "stop_below_fibo_vwap": "SL di bawah Fibo 0.618 / VWAP",
        "take_profit_planned": "TP disiapkan",
    },
}

CHECKLIST_KEYS = [
    key
    for section in CHECKLIST_SECTIONS.values()
    for key in section
]


def _default_data() -> dict[str, Any]:
    return {
        "ticker": "",
        "notes": "",
        "checklist": {key: False for key in CHECKLIST_KEYS},
    }


def _validate_data(data: Any) -> dict[str, Any]:
    """Validate imported or cached JSON and fill in missing checklist fields."""
    if not isinstance(data, dict):
        raise ValueError("Isi JSON harus berupa objek.")

    defaults = _default_data()
    ticker = data.get("ticker", defaults["ticker"])
    notes = data.get("notes", defaults["notes"])
    checklist = data.get("checklist", defaults["checklist"])
    if not isinstance(ticker, str) or not isinstance(notes, str):
        raise ValueError("Field ticker dan notes harus berupa teks.")
    if not isinstance(checklist, dict):
        raise ValueError("Field checklist harus berupa objek JSON.")

    normalized_checklist = defaults["checklist"].copy()
    for key in CHECKLIST_KEYS:
        value = checklist.get(key, False)
        if not isinstance(value, bool):
            raise ValueError(f"Nilai checklist '{key}' harus true atau false.")
        normalized_checklist[key] = value

    return {
        "ticker": ticker,
        "notes": notes,
        "checklist": normalized_checklist,
    }


def _session_data() -> dict[str, Any]:
    """Return the serializable application data from Streamlit state."""
    return {
        "ticker": st.session_state.get("ticker", ""),
        "notes": st.session_state.get("notes", ""),
        "checklist": {
            key: st.session_state.get(key, False)
            for key in CHECKLIST_KEYS
        },
    }


def load_cache() -> None:
    """Restore cached checklist values once at the start of the session."""
    if st.session_state.get(INITIALIZED_KEY):
        return

    data = _default_data()
    if CACHE_PATH.exists():
        try:
            with CACHE_PATH.open("r", encoding="utf-8") as cache_file:
                data = _validate_data(json.load(cache_file))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            st.session_state[CACHE_ERROR_KEY] = f"Gagal membaca cache: {exc}"

    st.session_state["ticker"] = data["ticker"]
    st.session_state["notes"] = data["notes"]
    for key, value in data["checklist"].items():
        st.session_state[key] = value
    st.session_state[INITIALIZED_KEY] = True


def save_cache() -> None:
    """Persist current form and checklist values after widget interactions."""
    try:
        with CACHE_PATH.open("w", encoding="utf-8") as cache_file:
            json.dump(_session_data(), cache_file, indent=2, ensure_ascii=False)
        st.session_state.pop(CACHE_ERROR_KEY, None)
    except OSError as exc:
        st.session_state[CACHE_ERROR_KEY] = f"Gagal menyimpan cache: {exc}"


def _import_uploaded_file(uploaded_file: Any) -> bool:
    """Import uploaded JSON once; return whether the data was applied."""
    if uploaded_file is None:
        return False

    contents = uploaded_file.getvalue()
    digest = hashlib.sha256(contents).hexdigest()
    if digest == st.session_state.get(LAST_IMPORT_KEY):
        return False

    try:
        data = _validate_data(json.loads(contents.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        st.error(f"File JSON tidak valid: {exc}")
        st.session_state[LAST_IMPORT_KEY] = digest
        return False

    st.session_state["ticker"] = data["ticker"]
    st.session_state["notes"] = data["notes"]
    for key, value in data["checklist"].items():
        st.session_state[key] = value
    st.session_state[LAST_IMPORT_KEY] = digest
    save_cache()
    return True


def reset_checklist() -> None:
    """Remove local cache and clear checklist values before the next rerun."""
    try:
        CACHE_PATH.unlink(missing_ok=True)
    except OSError as exc:
        st.session_state[CACHE_ERROR_KEY] = f"Gagal menghapus file cache: {exc}"
        return

    uploaded_digest = None
    uploaded_file = st.session_state.get(UPLOADER_KEY)
    if uploaded_file is not None:
        uploaded_digest = hashlib.sha256(uploaded_file.getvalue()).hexdigest()

    defaults = _default_data()
    st.session_state["ticker"] = defaults["ticker"]
    st.session_state["notes"] = defaults["notes"]
    for key, value in defaults["checklist"].items():
        st.session_state[key] = value
    if uploaded_digest is not None:
        st.session_state[LAST_IMPORT_KEY] = uploaded_digest
    else:
        st.session_state.pop(LAST_IMPORT_KEY, None)
    st.session_state[INITIALIZED_KEY] = True
    st.session_state.pop(CACHE_ERROR_KEY, None)
    st.session_state[RESET_MESSAGE_KEY] = "Checklist berhasil direset."


def main() -> None:
    st.set_page_config(
        page_title="Halal Pre-Trade Checklist",
        page_icon="✅",
        layout="wide",
    )
    render_home_link()
    load_cache()

    st.title("✅ Halal Pre-Trade Checklist")
    st.caption("Periksa kriteria sebelum mengambil posisi.")

    header_left, header_right = st.columns(2)
    with header_left:
        uploaded_file = st.file_uploader(
            "Import backup JSON",
            type=["json"],
            key=UPLOADER_KEY,
            help="Unggah file backup untuk mengganti checklist saat ini.",
        )
    with header_right:
        export_json = json.dumps(
            _session_data(),
            indent=2,
            ensure_ascii=False,
        )
        export_name = datetime.now().strftime("HalalChecklist_%Y%m%d_%H%M%S.json")
        st.download_button(
            "⬇️ Export JSON",
            data=export_json.encode("utf-8"),
            file_name=export_name,
            mime="application/json",
            use_container_width=True,
        )

    if _import_uploaded_file(uploaded_file):
        st.rerun()

    cache_error = st.session_state.get(CACHE_ERROR_KEY)
    if cache_error:
        st.warning(cache_error)
    reset_message = st.session_state.pop(RESET_MESSAGE_KEY, None)
    if reset_message:
        st.success(reset_message)

    st.text_input(
        "Ticker Saham",
        key="ticker",
        placeholder="Contoh: AAPL",
        on_change=save_cache,
    )

    total_items = len(CHECKLIST_KEYS)
    checked_items = 0
    section_columns = st.columns(5, gap="small")
    for column, (section_title, items) in zip(
        section_columns,
        CHECKLIST_SECTIONS.items(),
    ):
        with column:
            with st.container(border=True):
                st.markdown(f"**{section_title}**")
                for key, label in items.items():
                    checked = st.checkbox(
                        label,
                        key=key,
                        on_change=save_cache,
                    )
                    checked_items += int(checked)

    st.text_area(
        "Catatan Trading",
        key="notes",
        placeholder="Tulis rencana atau catatan trading...",
        on_change=save_cache,
    )

    completion = checked_items / total_items if total_items else 0.0
    st.subheader("Kelengkapan Checklist")
    st.progress(completion, text=f"{checked_items} dari {total_items} kriteria terpenuhi")
    if completion == 1.0:
        st.success("Semua kriteria terpenuhi! Siap eksekusi.")

    st.button(
        "Reset Checklist",
        type="secondary",
        on_click=reset_checklist,
    )


if __name__ == "__main__":
    check_login()
    main()
