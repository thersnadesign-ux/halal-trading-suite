"""TradingView macroeconomic events calendar."""

import streamlit as st
import streamlit.components.v1 as components

from auth import check_login, apply_custom_css

check_login()
apply_custom_css()

st.title("📅 Kalender Ekonomi Makro")
st.caption(
    "Pantau agenda ekonomi dan rilis data makro yang dapat memengaruhi "
    "pergerakan pasar saham."
)

tradingview_calendar = """
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
  {
  "colorTheme": "dark",
  "isTransparent": true,
  "width": "100%",
  "height": "600",
  "locale": "id",
  "importanceFilter": "-1,0,1",
  "currencyFilter": "USD"
  }
  </script>
</div>
<!-- TradingView Widget END -->
"""

components.html(tradingview_calendar, height=600)
