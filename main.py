"""Login gateway and navigation entrypoint for the Halal Trading Suite."""

import base64
from pathlib import Path

import streamlit as st

from auth import apply_custom_css, change_password, login


TRADING_GUIDE_PATH = Path(__file__).with_name("Trading_Saham_Syariah.pdf")


st.set_page_config(page_title="Halal Trading Suite", layout="wide")
apply_custom_css()
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            min-width: 300px;
            max-width: 300px;
        }
        [data-testid="stSidebar"] > div:first-child {
            width: 300px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

APPLICATIONS = [
    {
        "path": "app.py",
        "title": "Catalyst Analyzer",
        "icon": ":material/analytics:",
        "description": (
            "Analisis katalis berita dan press release saham US untuk membantu "
            "menilai momentum, risiko dilusi, dan kekuatan katalis."
        ),
    },
    {
        "path": "app_screener.py",
        "title": "Halal Momentum Screener",
        "icon": ":material/search:",
        "description": (
            "Saring saham berdasarkan gap, RVOL, harga, dan rasio fundamental "
            "yang digunakan sebagai kriteria syariah."
        ),
    },
    {
        "path": "app_risk_tracker.py",
        "title": "Risk Tracker",
        "icon": ":material/shield:",
        "description": (
            "Hitung position sizing berdasarkan risiko trade dan pantau "
            "jadwal settlement T+2 untuk cash account."
        ),
    },
    {
        "path": "app_journal.py",
        "title": "Trade Journal",
        "icon": ":material/edit_note:",
        "description": (
            "Catat entry, exit, PnL, dan pantau statistik serta performa "
            "kumulatif trading."
        ),
    },
    {
        "path": "app_checklist.py",
        "title": "Pre-Trade Checklist",
        "icon": ":material/checklist:",
        "description": (
            "Periksa filter syariah, tren, area entry, dan manajemen risiko "
            "sebelum mengambil posisi."
        ),
    },
    {
        "path": "app_calendar.py",
        "title": "Kalender Ekonomi",
        "icon": ":material/calendar_month:",
        "description": (
            "Pantau agenda ekonomi makro dan rilis data penting pasar saham."
        ),
    },
]


def _render_home() -> None:
    if not login():
        return

    st.title("🧭 Trading Assistant")
    st.caption(
        "Pengingat sistem Momentum Pullback. Gunakan sebagai panduan disiplin, "
        "bukan jaminan hasil atau rekomendasi investasi."
    )

    overview_tab, sop_tab, hours_tab, checklist_tab = st.tabs(
        [
            "Evaluasi Indikator",
            "SOP Momentum Pullback",
            "Jam Operasional",
            "Checklist Pre-Trade",
        ]
    )

    with overview_tab:
        st.subheader("Evaluasi Indikator")
        st.write(
            "VWAP, EMA 9/20, Fibonacci Retracement, dan Volume membentuk sistem "
            "yang saling melengkapi tanpa fungsi yang bertabrakan."
        )
        indicator_columns = st.columns(2)
        indicator_cards = [
            (
                "VWAP",
                "Penentu arah tren utama harian dan batas area institusional.",
            ),
            (
                "EMA 9 & EMA 20",
                "Penentu momentum jangka pendek dan support dinamis.",
            ),
            (
                "Fibonacci Retracement",
                "Pengukur titik jenuh koreksi (pullback) untuk area entry.",
            ),
            (
                "Volume Bar",
                "Validasi pergerakan untuk membedakan breakout asli dan fakeout.",
            ),
        ]
        for index, (indicator, description) in enumerate(indicator_cards):
            with indicator_columns[index % 2]:
                with st.container(border=True):
                    st.markdown(f"**{indicator}**")
                    st.write(description)

        st.warning(
            "Tidak perlu menambah RSI, MACD, atau Stochastic. Empat alat ini "
            "sudah mencakup Tren, Struktur Harga, dan Validasi Volume. "
            "Oscillator tambahan berisiko membingungkan keputusan "
            "(analysis paralysis)."
        )
        st.info(
            "**Parameter sistem:** timeframe 5 menit untuk menganalisis struktur "
            "dan 1 menit untuk presisi entry; instrumen saham momentum/uptrend; "
            "Cash Account 1:1 tanpa margin."
        )

    with sop_tab:
        st.subheader("SOP Baku: Momentum Pullback System")
        with st.container(border=True):
            st.markdown("**Phase 1 — Filter Tren (wajib sebelum analisis)**")
            st.markdown(
                "- Harga harus berada di atas VWAP.\n"
                "- EMA 9 harus di atas EMA 20 (bullish alignment), dan keduanya "
                "miring ke atas.\n"
                "- Saham berada dalam fase impulse: kenaikan tajam dengan volume "
                "tinggi di awal sesi."
            )
            st.error(
                "Jika harga di bawah VWAP atau EMA 9 menyilang ke bawah EMA 20, "
                "dilarang mencari posisi BUY."
            )

        with st.container(border=True):
            st.markdown("**Phase 2 — Identifikasi Area (Setup Fibonacci)**")
            st.markdown(
                "- Tunggu kenaikan tajam berhenti dan membentuk puncak tertinggi "
                "sementara (High of Day/HOD).\n"
                "- Tarik Fibonacci dari Swing Low (0.0%, titik terendah awal "
                "dorongan naik) ke Swing High (100.0%, puncak HOD sementara).\n"
                "- Tandai Golden Zone pada level 0.382, 0.500, hingga 0.618.\n"
                "- Golden Zone wajib berdekatan dengan EMA 9, EMA 20, atau VWAP "
                "sebagai confluence support."
            )

        with st.container(border=True):
            st.markdown(
                "**Phase 3 — Pemicu Eksekusi & Validasi Volume (Entry Trigger)**"
            )
            st.markdown(
                "- Saat harga pullback menuju Fibo 0.382–0.618, volume harus "
                "mengecil/mengering untuk menunjukkan tekanan jual melemah.\n"
                "- Tunggu candle pembalikan di Golden Zone, misalnya Hammer, "
                "Bullish Engulfing, atau Pinbar.\n"
                "- Volume candle pembalikan harus meningkat, minimal lebih tinggi "
                "dari 2–3 bar volume pullback sebelumnya.\n"
                "- Entry BUY saat candle pembalikan ditutup di atas EMA 9 pada "
                "timeframe 1M/5M."
            )

        with st.container(border=True):
            st.markdown("**Phase 4 — Manajemen Risiko & Pengambilan Keuntungan**")
            st.markdown(
                "| Parameter | Letak level / target |\n"
                "|---|---|\n"
                "| Stop Loss (SL) | 1–2 tick di bawah Fibo 0.618 atau tepat di "
                "bawah EMA 20/VWAP (pilih yang paling dekat). Toleransi risiko "
                "maksimal 3%–5% dari harga entry. |\n"
                "| Take Profit 1 (TP1) | Area HOD sebelumnya; jual 50%–70% posisi "
                "untuk mengamankan profit. |\n"
                "| Take Profit 2 (TP2) | Fibonacci Extension 1.272–1.618; biarkan "
                "sisa posisi berjalan (run the trend) hingga tersentuh. |"
            )

        with st.container(border=True):
            st.markdown("**Aturan Pembatalan Perdagangan (Invalidation Rules)**")
            st.markdown(
                "Batalkan rencana trade atau segera cut loss jika salah satu "
                "kondisi terjadi:\n"
                "- Harga ditutup di bawah VWAP.\n"
                "- Pullback terjadi dengan volume sangat tinggi, menandakan "
                "distribusi/penjualan masif.\n"
                "- Fibo 0.618 ditembus agresif oleh candle Marubozu merah."
            )

    with hours_tab:
        st.subheader("Jam Operasional Bursa Saham AS (WIB / GMT+7)")
        st.caption(
            "Jam mengikuti Daylight Saving Time (DST) AS dan dapat berubah "
            "sesuai tanggal pergantian waktu."
        )
        dst_column, standard_column = st.columns(2)
        with dst_column:
            with st.container(border=True):
                st.markdown("**Musim Panas / Daylight Saving Time**")
                st.caption("Maret – awal November · status saat ini")
                st.markdown(
                    "- Pre-Market (screening & cek berita): **18.00–20.30 WIB**\n"
                    "- Open Market (bel pembukaan): **20.30 WIB**\n"
                    "- Golden Trading Window: **20.30–22.30 WIB**\n"
                    "- Batas waktu exit (wajib tutup posisi): **maksimal 02.30 WIB**\n"
                    "- Closing Market: **03.00 WIB**"
                )
        with standard_column:
            with st.container(border=True):
                st.markdown("**Musim Dingin / Standard Time**")
                st.caption("Awal November – Maret")
                st.markdown(
                    "- Pre-Market (screening & cek berita): **19.00–21.30 WIB**\n"
                    "- Open Market (bel pembukaan): **21.30 WIB**\n"
                    "- Golden Trading Window: **21.30–23.30 WIB**\n"
                    "- Batas waktu exit (wajib tutup posisi): **maksimal 03.30 WIB**\n"
                    "- Closing Market: **04.00 WIB**"
                )
        st.warning(
            "Disiplin no overnight: tutup seluruh posisi paling lambat 30 menit "
            "sebelum pasar reguler tutup."
        )

    with checklist_tab:
        st.subheader("Checklist Pre-Trade (SOP Eksekusi)")
        with st.expander("Phase 1 — Filter Syariah & Kelayakan Saham", expanded=True):
            st.markdown(
                "- [ ] Status syariah terverifikasi Compliant di Zoya / Musaffa.\n"
                "- [ ] Ada katalis berita nyata (FDA Approval, Earnings Beat, "
                "kontrak baru, dan sejenisnya).\n"
                "- [ ] RVOL > 2.0.\n"
                "- [ ] Float < 20 juta lembar.\n"
                "- [ ] Rentang harga saham $2.00–$15.00."
            )
        with st.expander("Phase 2 — Kondisi Tren & Struktur Grafik"):
            st.markdown(
                "- [ ] Harga berada murni di atas VWAP.\n"
                "- [ ] EMA 9 di atas EMA 20 dan keduanya miring ke atas.\n"
                "- [ ] Saham membentuk lonjakan kenaikan awal (HOD pertama)."
            )
        with st.expander("Phase 3 — Area Fibonacci & Pullback Volume"):
            st.markdown(
                "- [ ] Fibo ditarik dari Swing Low awal dorongan naik ke Swing "
                "High/HOD sementara.\n"
                "- [ ] Harga sedang pullback ke Golden Zone Fibo 0.382–0.618.\n"
                "- [ ] Area Fibo berdekatan dengan EMA 9, EMA 20, atau VWAP.\n"
                "- [ ] Volume mengecil/mengering saat pullback."
            )
        with st.expander("Phase 4 — Sinyal & Eksekusi Entry"):
            st.markdown(
                "- [ ] Trigger candle (Hammer, Bullish Engulfing, atau Pinbar) "
                "muncul di Golden Zone.\n"
                "- [ ] Volume trigger candle lebih besar daripada rata-rata "
                "volume pullback.\n"
                "- [ ] Candle ditutup di atas EMA 9 pada timeframe 1M/5M."
            )
        with st.expander("Manajemen Risiko & Take Profit"):
            st.markdown(
                "- [ ] Position sizing maksimal 1/3 modal Cash Account harian "
                "(mencegah Good Faith Violation).\n"
                "- [ ] SL 1–2 tick di bawah Fibo 0.618 / EMA 20 / VWAP; "
                "toleransi rugi maksimal 3%–5%.\n"
                "- [ ] TP1: jual 50%–70% posisi di HOD sebelumnya.\n"
                "- [ ] TP2: biarkan sisa posisi berjalan hingga Fibonacci "
                "Extension 1.272–1.618.\n"
                "- [ ] No Overnight: tutup seluruh sisa posisi sebelum sesi "
                "reguler berakhir (maksimal 30 menit sebelum pasar tutup)."
            )


def _render_password_page() -> None:
    if not login():
        return
    st.title("Ubah Password")
    st.caption("Perbarui password akun Anda.")
    change_password()


def _render_trading_guide() -> None:
    if not login():
        return

    st.title("📖 Panduan Trading")
    st.caption("Dokumen panduan strategi trading.")

    try:
        pdf_bytes = TRADING_GUIDE_PATH.read_bytes()
    except OSError as exc:
        st.error(f"Tidak dapat membuka dokumen panduan: {exc}")
        return

    encoded_pdf = base64.b64encode(pdf_bytes).decode("ascii")
    st.markdown(
        f"""
        <iframe
            src="data:application/pdf;base64,{encoded_pdf}"
            width="100%"
            height="850"
            style="border: 1px solid #252D39; border-radius: 8px;"
            title="Panduan Trading PDF">
        </iframe>
        """,
        unsafe_allow_html=True,
    )
    st.download_button(
        "⬇️ Unduh Panduan Trading",
        data=pdf_bytes,
        file_name=TRADING_GUIDE_PATH.name,
        mime="application/pdf",
        use_container_width=True,
    )


def _render_stock_evaluator() -> None:
    if not login():
        return

    st.markdown(
        """
        <style>
            .evaluator-subtitle {
                color: #9BA8B7;
                font-family: monospace;
                margin-top: -.6rem;
                margin-bottom: 1.2rem;
            }
            .evaluator-value {
                color: #F1F5F9;
                font-family: monospace;
                font-size: 1.15rem;
                font-weight: 700;
                text-align: right;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Stock Setup Evaluator")
    st.markdown(
        '<div class="evaluator-subtitle">'
        "AAOIFI Shariah Compliance & Day Trading Momentum Simulator"
        "</div>",
        unsafe_allow_html=True,
    )

    debt_ratio = st.session_state.get("evaluator_debt_ratio", 15.0)
    interest_ratio = st.session_state.get("evaluator_interest_ratio", 2.0)
    rvol = st.session_state.get("evaluator_rvol", 4.0)
    share_float = st.session_state.get("evaluator_share_float", 10)
    price_above_vwap = st.session_state.get(
        "evaluator_price_above_vwap",
        True,
    )

    shariah_compliant = debt_ratio <= 30 and interest_ratio <= 5
    momentum_valid = rvol >= 2 and share_float <= 20 and price_above_vwap
    approved = shariah_compliant and momentum_valid

    shariah_column, momentum_column = st.columns(2, gap="small")
    with shariah_column:
        with st.container(border=True):
            status = "COMPLIANT" if shariah_compliant else "NOT COMPLIANT"
            st.markdown(f"**1. Shariah Screen** · `{status}`")
            st.markdown(f"Debt / Assets (≤30%) · **{debt_ratio:.1f}%**")
            st.markdown(f"Interest Rev (≤5%) · **{interest_ratio:.1f}%**")
    with momentum_column:
        with st.container(border=True):
            status = "VALID" if momentum_valid else "INVALID"
            st.markdown(f"**2. Momentum Screen** · `{status}`")
            st.markdown(f"RVOL (≥2.0x) · **{rvol:.1f}x**")
            st.markdown(f"Float (≤20M) · **{share_float}M**")
            st.markdown(
                "Price Above VWAP · **"
                + ("YES" if price_above_vwap else "NO")
                + "**"
            )

    if approved:
        st.success("GATE OUTPUT DECISION · APPROVED FOR CASH TRADE")
    else:
        failed_filters = []
        if not shariah_compliant:
            failed_filters.append("Shariah")
        if not momentum_valid:
            failed_filters.append("Momentum")
        st.error(
            "GATE OUTPUT DECISION · REJECTED — "
            f"filter tidak lolos: {', '.join(failed_filters)}"
        )

    with st.container(border=True):
        debt_column, interest_column = st.columns(2, gap="large")
        with debt_column:
            st.markdown(
                f"Debt / Total Assets "
                f"<span class='evaluator-value'>{debt_ratio:.1f}%</span>",
                unsafe_allow_html=True,
            )
            st.slider(
                "Debt to Assets",
                min_value=0.0,
                max_value=60.0,
                value=15.0,
                step=0.5,
                format="%.1f%%",
                key="evaluator_debt_ratio",
                label_visibility="collapsed",
            )
        with interest_column:
            st.markdown(
                f"Interest Revenue "
                f"<span class='evaluator-value'>{interest_ratio:.1f}%</span>",
                unsafe_allow_html=True,
            )
            st.slider(
                "Interest Revenue",
                min_value=0.0,
                max_value=15.0,
                value=2.0,
                step=0.1,
                format="%.1f%%",
                key="evaluator_interest_ratio",
                label_visibility="collapsed",
            )

        rvol_column, float_column = st.columns(2, gap="large")
        with rvol_column:
            st.markdown(
                f"Relative Vol (RVOL) "
                f"<span class='evaluator-value'>{rvol:.1f}x</span>",
                unsafe_allow_html=True,
            )
            st.slider(
                "Relative Volume",
                min_value=0.0,
                max_value=10.0,
                value=4.0,
                step=0.1,
                format="%.1fx",
                key="evaluator_rvol",
                label_visibility="collapsed",
            )
        with float_column:
            st.markdown(
                f"Share Float "
                f"<span class='evaluator-value'>{share_float}M</span>",
                unsafe_allow_html=True,
            )
            st.slider(
                "Share Float (millions)",
                min_value=1,
                max_value=100,
                value=10,
                step=1,
                format="%dM",
                key="evaluator_share_float",
                label_visibility="collapsed",
            )

        st.toggle(
            "Price Above VWAP",
            key="evaluator_price_above_vwap",
            value=True,
        )

    st.button(
        "Simulasikan Keputusan Beli",
        type="primary",
        use_container_width=True,
        disabled=not approved,
        help=(
            "Simulasi hanya tersedia saat filter Syariah dan Momentum sama-sama "
            "lolos. Tombol ini tidak mengirim order."
        ),
    )
    if not approved:
        st.caption(
            "Simulasi keputusan beli terkunci sampai kedua filter berstatus lolos."
        )
    else:
        st.caption(
            "Semua filter lolos. Tombol di atas hanya simulasi edukasi dan "
            "tidak mengirim order ke broker."
        )


application_pages = {
    application["path"]: st.Page(
        application["path"],
        title=application["title"],
        icon=application["icon"],
    )
    for application in APPLICATIONS
}


home_page = st.Page(
    _render_home,
    title="Beranda",
    icon=":material/dashboard:",
    default=True,
)
password_page = st.Page(
    _render_password_page,
    title="Ubah Password",
    icon=":material/lock_reset:",
)
trading_guide_page = st.Page(
    _render_trading_guide,
    title="Panduan Trading",
    icon=":material/menu_book:",
)
stock_evaluator_page = st.Page(
    _render_stock_evaluator,
    title="Stock Evaluator",
    icon=":material/monitor_heart:",
)
st.session_state["_home_page"] = home_page

navigation = st.navigation(
    [
        home_page,
        *application_pages.values(),
        trading_guide_page,
        stock_evaluator_page,
        password_page,
    ],
    position="sidebar",
)
navigation.run()
