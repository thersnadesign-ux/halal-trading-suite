"""Local JSON-backed authentication and shared Streamlit styling."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import streamlit as st


USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
PASSWORD_ITERATIONS = 310_000


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_ITERATIONS,
    ).hex()


def _write_users(users: dict[str, dict[str, str]]) -> None:
    temporary_path = f"{USERS_FILE}.tmp"
    with open(temporary_path, "w", encoding="utf-8") as users_file:
        json.dump(users, users_file, indent=2, ensure_ascii=False)
    os.replace(temporary_path, USERS_FILE)


def _default_users() -> dict[str, dict[str, str]]:
    salt = secrets.token_bytes(16).hex()
    return {
        "admin": {
            "salt": salt,
            "password_hash": _hash_password("Bismillah", salt),
        }
    }


def load_users() -> dict[str, dict[str, str]]:
    """Load local users, creating the default admin account on first run."""
    if not os.path.exists(USERS_FILE):
        users = _default_users()
        try:
            _write_users(users)
        except OSError as exc:
            raise ValueError(f"Gagal membuat users.json: {exc}") from exc
        return users

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as users_file:
            users = json.load(users_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"File users.json tidak dapat dibaca: {exc}") from exc

    if not isinstance(users, dict):
        raise ValueError("Format users.json tidak valid.")
    for username, record in users.items():
        if (
            not isinstance(username, str)
            or not isinstance(record, dict)
            or not isinstance(record.get("salt"), str)
            or not isinstance(record.get("password_hash"), str)
        ):
            raise ValueError("Data pengguna di users.json tidak valid.")
    return users


def save_users(users: dict[str, dict[str, str]]) -> None:
    """Save the users file atomically to avoid partial writes."""
    try:
        _write_users(users)
    except OSError as exc:
        raise ValueError(f"Gagal menyimpan users.json: {exc}") from exc


def apply_custom_css() -> None:
    """Apply the shared centered indigo and turquoise application theme."""
    st.markdown(
        """
        <style>
            :root {
                --suite-bg: #211F46;
                --suite-panel: #29274F;
                --suite-panel-soft: #302D5A;
                --suite-border: #3A3768;
                --suite-text: #F4F3FF;
                --suite-muted: #A8A5CC;
                --suite-turquoise: #00D6B5;
                --suite-blue: #2764F5;
            }
            .stApp {
                background:
                    radial-gradient(ellipse at 50% 0%, #302D5A 0%, transparent 48%),
                    var(--suite-bg);
                color: var(--suite-text);
            }
            [data-testid="stAppViewContainer"] .main .block-container {
                width: min(100% - 3rem, 1040px);
                max-width: 1040px;
                margin-left: auto;
                margin-right: auto;
                padding: 2rem 0 3rem;
            }
            [data-testid="stSidebar"] {
                background: #1C1A3D;
                border-right: 1px solid var(--suite-border);
            }
            [data-testid="stSidebarNav"] a {
                border-radius: 12px;
                margin: .18rem .55rem;
                transition: background .18s ease, color .18s ease;
            }
            [data-testid="stSidebarNav"] a:hover {
                background: #34315F;
                color: var(--suite-text);
            }
            [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: linear-gradient(105deg, #00CDAE, #2865F5);
                color: #FFFFFF;
            }
            [data-testid="stSidebarNav"] a [data-testid="stIconMaterial"] {
                color: var(--suite-turquoise);
            }
            [data-testid="stSidebarNav"] a[aria-current="page"] [data-testid="stIconMaterial"] {
                color: #FFFFFF;
            }
            [data-testid="stMetric"],
            [data-testid="stDataFrame"],
            [data-testid="stTable"],
            div[data-testid="stVerticalBlockBorderWrapper"] {
                border: 1px solid var(--suite-border);
                border-radius: 16px;
            }
            [data-testid="stMetric"] {
                background: var(--suite-panel);
                padding: 1rem;
            }
            [data-testid="stVerticalBlockBorderWrapper"] {
                background: rgba(41, 39, 79, .72);
            }
            label, [data-testid="stWidgetLabel"] p,
            [data-testid="stCaptionContainer"] {
                color: var(--suite-muted) !important;
            }
            .negative-value,
            [data-testid="stMetricDelta"]:has(svg[fill="red"]) {
                color: #FF4D65 !important;
            }
            [data-testid="stMetricDelta"]:has(svg[fill="red"]) svg {
                fill: #FF4D65 !important;
            }
            .app-card-title {
                color: var(--suite-turquoise);
                font-weight: 700;
                font-size: 1.08rem;
                margin-bottom: .35rem;
            }
            .app-card-description {
                color: var(--suite-muted);
                min-height: 3.2rem;
            }
            button[kind="primary"],
            [data-testid="stFormSubmitButton"] button[kind="primary"] {
                border: 0;
                border-radius: 12px;
                background: linear-gradient(105deg, #00CDAE, #2865F5);
                color: #FFFFFF;
                font-weight: 700;
            }
            button[kind="primary"]:hover {
                border: 0;
                filter: brightness(1.08);
                color: #FFFFFF;
            }
            [data-testid="stTextInput"] input,
            [data-testid="stTextArea"] textarea {
                border-radius: 10px;
                background: #211F46;
            }
            .login-card-heading {
                text-align: center;
                margin: .25rem 0 .5rem;
            }
            .login-card-heading span {
                color: var(--suite-turquoise);
                font-family: monospace;
                font-size: .75rem;
                font-weight: 700;
                letter-spacing: .18em;
            }
            .st-key-login-card {
                width: 300px;
                height: 300px;
                min-height: 300px;
                max-width: 100%;
                aspect-ratio: 1 / 1;
                box-sizing: border-box;
                display: flex;
                justify-content: center;
                margin: 0 auto;
                padding: .6rem;
                flex: 0 0 300px;
            }
            .st-key-login-card [data-testid="stForm"] {
                border: 0 !important;
                padding: 0 !important;
                background: transparent !important;
            }
            .st-key-login-layout {
                min-height: calc(100vh - 9rem);
            }
            .st-key-login-layout [data-testid="stHorizontalBlock"] {
                min-height: calc(100vh - 9rem);
                align-items: center;
            }
            @media (max-width: 700px) {
                [data-testid="stAppViewContainer"] .main .block-container {
                    width: calc(100% - 1.5rem);
                    padding-top: 1.25rem;
                }
                .st-key-login-layout {
                    min-height: auto;
                }
                .st-key-login-layout [data-testid="stHorizontalBlock"] {
                    min-height: auto;
                }
                .st-key-login-card {
                    width: min(300px, 100%);
                    height: 300px;
                    min-height: 300px;
                    flex-basis: min(300px, 100%);
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def login() -> bool:
    """Render the login form and report whether a user is authenticated."""
    if st.session_state.get("logged_in") is True:
        return True

    try:
        users = load_users()
    except ValueError as exc:
        st.error(str(exc))
        return False

    with st.container(key="login-layout"):
        _, login_column, _ = st.columns(
            [1, 12, 1],
            gap="large",
        )
        with login_column:
            with st.container(border=True, key="login-card"):
                st.markdown(
                    """
                    <div class="login-card-heading">
                        <span>HALAL TRADING SUITE</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submitted = st.form_submit_button(
                        "Login",
                        type="primary",
                        use_container_width=True,
                    )

    if submitted:
        user = users.get(username.strip())
        if user is not None:
            try:
                candidate_hash = _hash_password(password, user["salt"])
            except (ValueError, TypeError):
                candidate_hash = ""
            if hmac.compare_digest(candidate_hash, user["password_hash"]):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username.strip()
                st.rerun()
        st.error("Username atau password tidak cocok.")
    return False


def check_login() -> None:
    """Stop a page from rendering unless the user has logged in."""
    if st.session_state.get("logged_in") is not True:
        st.warning("Silakan login dari halaman utama untuk melanjutkan.")
        st.stop()


def render_home_link() -> None:
    """Render a link to the home Page registered by the navigation entrypoint."""
    home_page = st.session_state.get("_home_page")
    if home_page is None:
        st.error("Halaman Home tidak terdaftar. Jalankan aplikasi melalui main.py.")
        return
    st.page_link(home_page, label="Kembali ke Home", icon=":material/dashboard:")


def change_password() -> None:
    """Render a form that changes the current user's password."""
    username = st.session_state.get("username")
    if not username:
        st.warning("Sesi login tidak memiliki username yang valid.")
        return

    st.subheader("Ubah Password")
    with st.form("change_password_form"):
        current_password = st.text_input(
            "Password saat ini",
            type="password",
        )
        new_password = st.text_input(
            "Password baru",
            type="password",
        )
        confirm_password = st.text_input(
            "Konfirmasi password baru",
            type="password",
        )
        submitted = st.form_submit_button("Simpan Password Baru")

    if not submitted:
        return
    if len(new_password) < 8:
        st.error("Password baru harus memiliki minimal 8 karakter.")
        return
    if new_password != confirm_password:
        st.error("Konfirmasi password baru tidak cocok.")
        return

    try:
        users = load_users()
    except ValueError as exc:
        st.error(str(exc))
        return

    user = users.get(username)
    if user is None:
        st.error("Akun pengguna tidak ditemukan.")
        return
    current_hash = _hash_password(current_password, user["salt"])
    if not hmac.compare_digest(current_hash, user["password_hash"]):
        st.error("Password saat ini tidak cocok.")
        return

    salt = secrets.token_bytes(16).hex()
    users[username] = {
        "salt": salt,
        "password_hash": _hash_password(new_password, salt),
    }
    try:
        save_users(users)
    except ValueError as exc:
        st.error(str(exc))
        return
    st.success("Password berhasil diperbarui.")
