import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text
from src.database import engine

st.set_page_config(
    page_title="Crypto Market Tracker",
    page_icon="📈",
    layout="wide",
)

# ── CSS customizado ──────────────────────────────────────────────────────────
st.markdown("""
<style>
  .metric-card {
    background: #1e1e2e;
    border-radius: 10px;
    padding: 16px;
    border: 1px solid #313244;
  }
  .alert-high { color: #a6e3a1; font-weight: 600; }
  .alert-low  { color: #f38ba8; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Funções de dados ──────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_latest_snapshot() -> pd.DataFrame:
    query = """
        SELECT DISTINCT ON (coin_id)
            coin_id, symbol, name, price_usd,
            change_24h_pct, market_cap, total_volume,
            high_24h, low_24h, collected_at
        FROM price_snapshots
        ORDER BY coin_id, collected_at DESC
    """
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


@st.cache_data(ttl=300)
def get_price_history(coin_id: str, hours: int = 168) -> pd.DataFrame:
    query = text("""
        SELECT collected_at, price_usd, total_volume, change_24h_pct
        FROM price_snapshots
        WHERE coin_id = :coin_id
          AND collected_at >= NOW() - INTERVAL ':hours hours'
        ORDER BY collected_at ASC
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"coin_id": coin_id, "hours": hours})


@st.cache_data(ttl=300)
def get_alerts(limit: int = 50) -> pd.DataFrame:
    query = f"""
        SELECT coin_id, symbol, alert_type, change_pct, price_usd, created_at
        FROM alerts
        ORDER BY created_at DESC
        LIMIT {limit}
    """
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


# ── Header ────────────────────────────────────────────────────────────────────
st.title("📈 Crypto Market Tracker")
st.caption("Pipeline de dados em tempo real — CoinGecko → PostgreSQL → Streamlit")

# ── Snapshot atual ────────────────────────────────────────────────────────────
try:
    df_latest = get_latest_snapshot()
except Exception as e:
    st.error(f"Erro ao conectar ao banco: {e}")
    st.info("Certifique-se de que o pipeline está rodando e o banco foi populado.")
    st.stop()

if df_latest.empty:
    st.warning("Nenhum dado ainda. Execute o pipeline pelo menos uma vez.")
    st.stop()

# ── KPIs globais ──────────────────────────────────────────────────────────────
st.subheader("Visão Geral do Mercado")
col1, col2, col3, col4 = st.columns(4)

total_mcap = df_latest["market_cap"].sum()
total_vol  = df_latest["total_volume"].sum()
avg_change = df_latest["change_24h_pct"].mean()
gainers    = (df_latest["change_24h_pct"] > 0).sum()

col1.metric("Market Cap Total", f"${total_mcap/1e12:.2f}T")
col2.metric("Volume 24h Total", f"${total_vol/1e9:.1f}B")
col3.metric("Variação Média 24h", f"{avg_change:+.2f}%",
            delta_color="normal" if avg_change >= 0 else "inverse")
col4.metric("Em alta / Em queda", f"{gainers} / {len(df_latest) - gainers}")

st.divider()

# ── Tabela principal ──────────────────────────────────────────────────────────
st.subheader("Top Coins por Market Cap")

df_display = df_latest[[
    "name", "symbol", "price_usd", "change_24h_pct",
    "market_cap", "total_volume", "high_24h", "low_24h"
]].copy()
df_display.columns = ["Nome", "Símbolo", "Preço (USD)", "Var. 24h (%)",
                      "Market Cap", "Volume 24h", "Máx. 24h", "Mín. 24h"]
df_display["Símbolo"] = df_display["Símbolo"].str.upper()

def color_change(val):
    color = "#a6e3a1" if val > 0 else "#f38ba8"
    return f"color: {color}; font-weight: 600"

st.dataframe(
    df_display.style
        .format({
            "Preço (USD)": "${:,.4f}",
            "Var. 24h (%)": "{:+.2f}%",
            "Market Cap": "${:,.0f}",
            "Volume 24h": "${:,.0f}",
            "Máx. 24h": "${:,.4f}",
            "Mín. 24h": "${:,.4f}",
        })
        .applymap(color_change, subset=["Var. 24h (%)"]),
    use_container_width=True,
    height=420,
)

st.divider()

# ── Gráficos de ranking ───────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🟢 Maiores Altas (24h)")
    top_gainers = df_latest.nlargest(10, "change_24h_pct")
    fig_g = px.bar(
        top_gainers, x="change_24h_pct", y="symbol",
        orientation="h", color="change_24h_pct",
        color_continuous_scale=["#1e6639", "#a6e3a1"],
        labels={"change_24h_pct": "Variação (%)", "symbol": ""},
    )
    fig_g.update_layout(showlegend=False, coloraxis_showscale=False,
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_g, use_container_width=True)

with col_b:
    st.subheader("🔴 Maiores Quedas (24h)")
    top_losers = df_latest.nsmallest(10, "change_24h_pct")
    fig_l = px.bar(
        top_losers, x="change_24h_pct", y="symbol",
        orientation="h", color="change_24h_pct",
        color_continuous_scale=["#f38ba8", "#6e1a1a"],
        labels={"change_24h_pct": "Variação (%)", "symbol": ""},
    )
    fig_l.update_layout(showlegend=False, coloraxis_showscale=False,
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_l, use_container_width=True)

st.divider()

# ── Histórico por moeda ───────────────────────────────────────────────────────
st.subheader("📊 Histórico de Preço")

coins = sorted(df_latest["coin_id"].tolist())
col_sel1, col_sel2 = st.columns([2, 1])

with col_sel1:
    selected_coin = st.selectbox("Selecione a moeda", coins,
                                  index=coins.index("bitcoin") if "bitcoin" in coins else 0)
with col_sel2:
    hours = st.select_slider("Período", options=[24, 48, 72, 168, 336, 720],
                              value=168, format_func=lambda h: f"{h}h")

df_hist = get_price_history(selected_coin, hours)

if df_hist.empty:
    st.info("Histórico insuficiente. Aguarde mais coletas.")
else:
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=df_hist["collected_at"],
        y=df_hist["price_usd"],
        mode="lines",
        name="Preço",
        line=dict(color="#89b4fa", width=2),
        fill="tozeroy",
        fillcolor="rgba(137, 180, 250, 0.08)",
    ))
    fig_hist.update_layout(
        xaxis_title="Data/hora",
        yaxis_title="Preço (USD)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # Volume
    fig_vol = px.bar(df_hist, x="collected_at", y="total_volume",
                     labels={"total_volume": "Volume (USD)", "collected_at": ""},
                     color_discrete_sequence=["#cba6f7"])
    fig_vol.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_vol, use_container_width=True)

st.divider()

# ── Alertas ───────────────────────────────────────────────────────────────────
st.subheader("⚠️ Alertas de Variação Extrema")

try:
    df_alerts = get_alerts()
    if df_alerts.empty:
        st.success("Nenhum alerta registrado ainda.")
    else:
        df_alerts["change_pct"] = df_alerts["change_pct"].apply(lambda x: f"{x:+.2f}%")
        df_alerts["price_usd"]  = df_alerts["price_usd"].apply(lambda x: f"${x:,.4f}")
        df_alerts["symbol"]     = df_alerts["symbol"].str.upper()
        st.dataframe(df_alerts, use_container_width=True)
except Exception:
    st.info("Tabela de alertas ainda não criada. Aguarde a primeira coleta.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.caption("Dados: CoinGecko API (gratuita) · Atualiza a cada hora · Projeto de portfólio")
