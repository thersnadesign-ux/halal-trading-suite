"""Streamlit app for analyzing US stock momentum catalysts."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import streamlit as st
import yfinance as yf

from auth import apply_custom_css, check_login, render_home_link
from ai_engine import analyze_catalyst


API_KEY_FILE = Path(__file__).parent / ".streamlit" / "groq_api_key.json"


def _load_saved_api_key() -> str:
    """Read the optional Groq API key saved on this device."""
    if not API_KEY_FILE.exists():
        return ""

    with API_KEY_FILE.open("r", encoding="utf-8") as key_file:
        saved_data = json.load(key_file)
    if not isinstance(saved_data, dict) or not isinstance(
        saved_data.get("api_key"), str
    ):
        raise ValueError("Format file API Key tidak valid.")
    return saved_data["api_key"]


def _save_api_key(api_key: str) -> None:
    """Persist the Groq API key in a local JSON file."""
    API_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = API_KEY_FILE.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as key_file:
        json.dump({"api_key": api_key}, key_file, ensure_ascii=False)
    temporary_path.replace(API_KEY_FILE)


def _delete_saved_api_key() -> None:
    """Remove the locally saved Groq API key."""
    API_KEY_FILE.unlink(missing_ok=True)


@st.cache_data(ttl=900, show_spinner=False)
def _fetch_yahoo_news(ticker_symbol: str) -> list[dict[str, str]]:
    """Fetch and normalize recent Yahoo Finance news for one ticker."""
    articles: list[dict[str, str]] = []
    for item in yf.Ticker(ticker_symbol).news:
        content = item.get("content", item)
        if not isinstance(content, dict):
            continue

        title = content.get("title")
        if not isinstance(title, str) or not title.strip():
            continue

        provider = content.get("provider", {})
        publisher = (
            provider.get("displayName") or content.get("publisher", "")
            if isinstance(provider, dict)
            else content.get("publisher", "")
        )
        publish_date = content.get("pubDate", "")
        if isinstance(publish_date, str) and publish_date:
            try:
                parsed_date = datetime.fromisoformat(
                    publish_date.replace("Z", "+00:00")
                )
                if parsed_date.tzinfo is None:
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                publish_date = parsed_date.astimezone(timezone.utc).strftime(
                    "%d %b %Y, %H:%M UTC"
                )
            except ValueError:
                pass
        elif isinstance(content.get("providerPublishTime"), (int, float)):
            try:
                publish_date = datetime.fromtimestamp(
                    content["providerPublishTime"],
                    tz=timezone.utc,
                ).strftime("%d %b %Y, %H:%M UTC")
            except (OSError, OverflowError, ValueError):
                publish_date = ""
        else:
            publish_date = ""

        link_data = content.get("canonicalUrl") or content.get("clickThroughUrl")
        url = (
            link_data.get("url", "")
            if isinstance(link_data, dict)
            else content.get("link", "")
        )
        summary = content.get("summary", "")
        articles.append(
            {
                "title": title.strip(),
                "publisher": publisher if isinstance(publisher, str) else "",
                "published": publish_date if isinstance(publish_date, str) else "",
                "summary": summary.strip() if isinstance(summary, str) else "",
                "url": url if isinstance(url, str) else "",
            }
        )
    return articles


def _render_yahoo_news(ticker_symbol: str) -> None:
    st.subheader("📰 Berita Saham & Press Release")
    st.caption(
        f"Berita terbaru untuk {ticker_symbol} dari Yahoo Finance. "
        "Data dapat tertunda atau tidak tersedia."
    )
    if st.button("Muat ulang berita", key="refresh_yahoo_news"):
        _fetch_yahoo_news.clear()

    try:
        with st.spinner("Memuat berita dari Yahoo Finance..."):
            articles = _fetch_yahoo_news(ticker_symbol)
    except Exception as exc:
        st.error(f"Tidak dapat mengambil berita dari Yahoo Finance: {exc}")
        return

    if not articles:
        st.info(
            f"Belum ada berita atau press release yang tersedia untuk "
            f"{ticker_symbol} di Yahoo Finance."
        )
        return

    for article in articles[:8]:
        with st.container(border=True):
            if article["url"]:
                st.link_button(
                    article["title"],
                    article["url"],
                    use_container_width=True,
                )
            else:
                st.markdown(f"**{article['title']}**")
            metadata = " · ".join(
                value
                for value in (article["publisher"], article["published"])
                if value
            )
            if metadata:
                st.caption(metadata)
            if article["summary"]:
                st.write(article["summary"])


check_login()

st.set_page_config(
    page_title="Momentum Catalyst Analyzer",
    page_icon="📈",
    layout="wide",
)
apply_custom_css()
render_home_link()

if not st.session_state.get("_groq_api_key_initialized"):
    try:
        st.session_state["groq_api_key"] = _load_saved_api_key()
        st.session_state["save_groq_api_key"] = bool(
            st.session_state["groq_api_key"]
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        st.session_state["groq_api_key"] = ""
        st.session_state["save_groq_api_key"] = False
        st.session_state["_groq_api_key_load_error"] = (
            f"Tidak dapat membaca API Key tersimpan: {exc}"
        )
    st.session_state["_groq_api_key_initialized"] = True

st.markdown(
    """
    <style>
        .main .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .hero-caption { color: #9BA8B7; font-size: 1.05rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("⚙️ Pengaturan")
    st.caption("Masukkan API Key Groq untuk mengakses model analisis.")
    with st.form("groq_api_key_settings"):
        st.text_input(
            "Groq API Key",
            type="password",
            placeholder="Masukkan API Key",
            key="groq_api_key",
            help="API Key akan disimpan di perangkat ini jika opsi penyimpanan dipilih.",
        )
        save_api_key = st.checkbox(
            "Simpan API Key di perangkat ini",
            key="save_groq_api_key",
        )
        save_api_key_submitted = st.form_submit_button(
            "Simpan Pengaturan API Key",
            use_container_width=True,
        )

    load_error = st.session_state.pop("_groq_api_key_load_error", None)
    if load_error:
        st.error(load_error)

    if save_api_key_submitted:
        api_key_value = st.session_state["groq_api_key"].strip()
        if save_api_key:
            if not api_key_value:
                st.error("Masukkan API Key sebelum menyimpannya.")
            else:
                try:
                    _save_api_key(api_key_value)
                except OSError as exc:
                    st.error(f"Tidak dapat menyimpan API Key: {exc}")
                else:
                    st.success("API Key berhasil disimpan di perangkat ini.")
        else:
            try:
                _delete_saved_api_key()
            except OSError as exc:
                st.error(f"Tidak dapat menghapus API Key tersimpan: {exc}")
            else:
                st.success("Penyimpanan API Key di perangkat ini dinonaktifkan.")

    st.caption(
        "API Key tersimpan sebagai teks di file lokal aplikasi. "
        "Jangan bagikan atau unggah file tersebut."
    )
    st.divider()
    st.caption("Analisis bersifat informasional, bukan rekomendasi investasi.")

api_key = st.session_state.get("groq_api_key", "")

st.title("📈 Momentum Catalyst Analyzer")
st.markdown(
    '<p class="hero-caption">Analisis katalis berita saham US dengan Groq AI.</p>',
    unsafe_allow_html=True,
)

analysis_column, news_column = st.columns([1.2, 1], gap="large")
with analysis_column:
    st.subheader("Analisis Katalis")
    with st.form("catalyst_analysis_form"):
        ticker = st.text_input(
            "Ticker Saham",
            placeholder="Contoh: NVDA",
            max_chars=12,
            key="catalyst_ticker",
        )
        news_text = st.text_area(
            "Teks Berita / Press Release",
            placeholder="Tempel berita atau press release di sini...",
            height=240,
            key="catalyst_news_text",
        )
        submitted = st.form_submit_button(
            "🔍 Analisis Katalis",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not api_key.strip():
            st.error("Masukkan Groq API Key di sidebar terlebih dahulu.")
        elif not ticker.strip():
            st.error("Masukkan ticker saham yang ingin dianalisis.")
        elif not news_text.strip():
            st.error("Tempel teks berita atau press release terlebih dahulu.")
        else:
            try:
                with st.spinner("Groq sedang menganalisis katalis berita..."):
                    st.session_state["catalyst_analysis"] = analyze_catalyst(
                        ticker,
                        news_text,
                        api_key,
                    )
                st.session_state["catalyst_analysis_input"] = (
                    ticker.strip().upper(),
                    news_text.strip(),
                )
            except ValueError as exc:
                st.error(f"Analisis gagal: {exc}")
            except Exception as exc:
                st.error(
                    "Permintaan ke Groq gagal. Periksa API Key, koneksi internet, "
                    f"dan akses model, lalu coba lagi. Detail: {exc}"
                )

    previous_analysis = st.session_state.get("catalyst_analysis")
    previous_input = st.session_state.get("catalyst_analysis_input")
    current_input = (ticker.strip().upper(), news_text.strip())
    if previous_analysis and previous_input == current_input:
        st.subheader(f"Hasil Analisis — {previous_analysis['ticker']}")
        metrics = st.columns(3)
        metrics[0].metric("Verdict", previous_analysis["verdict"])
        metrics[1].metric(
            "Kekuatan Katalis",
            f"{previous_analysis['catalyst_strength_score']}/10",
        )
        metrics[2].metric("Risiko Dilusi", previous_analysis["dilution_risk"])
        st.metric("Jenis Katalis", previous_analysis["catalyst_type"])
        st.info(previous_analysis["summary"], icon="📰")

with news_column:
    ticker_for_news = st.session_state.get("catalyst_ticker", "").strip().upper()
    if ticker_for_news:
        _render_yahoo_news(ticker_for_news)
    else:
        st.subheader("📰 Berita Saham & Press Release")
        st.info("Masukkan ticker saham untuk melihat berita dari Yahoo Finance.")
