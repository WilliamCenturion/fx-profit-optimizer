import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone

# ---------------------------------------------------------
# FX Profit Optimizer — interface v2
# ---------------------------------------------------------
st.set_page_config(
    page_title="FX Profit Optimizer",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ASSETS = {
    "USDC": {"kind": "Cripto / stablecoin", "coingecko": "usd-coin"},
    "USDT": {"kind": "Cripto / stablecoin", "coingecko": "tether"},
    "BTC": {"kind": "Criptomoeda", "coingecko": "bitcoin"},
    "ETH": {"kind": "Criptomoeda", "coingecko": "ethereum"},
    "USD": {"kind": "Fiduciária", "coingecko": None},
    "BRL": {"kind": "Fiduciária", "coingecko": None},
    "EUR": {"kind": "Fiduciária", "coingecko": None},
    "GBP": {"kind": "Fiduciária", "coingecko": None},
}

DEFAULT_COSTS = pd.DataFrame([
    {"Destino": asset, "Taxa plataforma (%)": 0.0, "Spread (%)": 0.0, "Tarifa fixa (USD)": 0.0}
    for asset in ASSETS
])

# Visual identity: black + yellow
st.markdown("""
<style>
:root { --fx-yellow: #f5c400; --fx-black: #080a0f; }
.stApp { background: #080a0f; color: #f4f4f5; }
[data-testid="stHeader"] { background: rgba(8,10,15,.96); }
.block-container { max-width: 1120px; padding-top: 2.2rem; padding-bottom: 4rem; }
[data-testid="stSidebar"] { background: #10131b; }
h1, h2, h3 { color: #f7f7f7 !important; }
.fx-kicker { color: #f5c400; letter-spacing: .18em; font-size: .76rem; font-weight: 800; }
.fx-subtitle { color: #a1a1aa; font-size: 1rem; }
.fx-panel { background: linear-gradient(145deg,#171a22,#101219); border: 1px solid #292d37;
            border-radius: 20px; padding: 1.4rem; }
.fx-yellow { color: #f5c400; }
div.stButton > button[kind="primary"], div.stFormSubmitButton > button {
    background: #f5c400; color: #080a0f; border: 0; border-radius: 12px;
    min-height: 3.1rem; font-weight: 800; width: 100%;
}
div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button:hover {
    background: #ffda36; color: #080a0f; border: 0;
}
[data-testid="stNumberInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] {
    background: #20232c; color: #fff; border-radius: 10px;
}
[data-testid="stMetric"] { background: #151821; border: 1px solid #2a2e38;
                           border-radius: 14px; padding: 14px; }
[data-testid="stMetricLabel"] { color: #a1a1aa; }
[data-testid="stMetricValue"] { color: #f5c400; }
[data-testid="stDataFrame"] { border: 1px solid #292d37; border-radius: 12px; }
hr { border-color: #292d37; }
small, .stCaption { color: #a1a1aa !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60, show_spinner=False)
def fetch_market_prices():
    """Return USD value for each asset, plus source/date metadata."""
    prices = {"USD": 1.0}
    sources = []
    errors = []

    # Crypto assets: public CoinGecko simple-price endpoint.
    crypto_ids = ",".join(["usd-coin", "tether", "bitcoin", "ethereum"])
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": crypto_ids, "vs_currencies": "usd"},
            timeout=8,
            headers={"accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        for symbol, coin_id in {
            "USDC": "usd-coin", "USDT": "tether", "BTC": "bitcoin", "ETH": "ethereum"
        }.items():
            value = data.get(coin_id, {}).get("usd")
            if value is not None and float(value) > 0:
                prices[symbol] = float(value)
        sources.append("CoinGecko (criptoativos)")
    except Exception as exc:
        errors.append(f"Criptoativos: {exc}")

    # Fiat currencies: Frankfurter publishes reference FX rates against USD.
    try:
        response = requests.get(
            "https://api.frankfurter.app/latest",
            params={"from": "USD", "to": "BRL,EUR,GBP"},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
        rates = data.get("rates", {})
        if rates.get("BRL"):
            prices["BRL"] = 1.0 / float(rates["BRL"])
        if rates.get("EUR"):
            prices["EUR"] = 1.0 / float(rates["EUR"])
        if rates.get("GBP"):
            prices["GBP"] = 1.0 / float(rates["GBP"])
        sources.append(f"Frankfurter (câmbio fiduciário; data {data.get('date', 'não informada')})")
    except Exception as exc:
        errors.append(f"Moedas fiduciárias: {exc}")

    return prices, sources, errors

def money(value, symbol):
    if symbol in ("BTC", "ETH"):
        return f"{value:,.8f} {symbol}"
    return f"{value:,.4f} {symbol}"

def build_ranking(amount, origin, prices, costs):
    origin_price = prices[origin]
    gross_usd = amount * origin_price
    results = []

    for destination in ASSETS:
        if destination not in prices:
            continue

        row = costs.loc[costs["Destino"] == destination]
        if row.empty:
            platform_pct, spread_pct, fixed_usd = 0.0, 0.0, 0.0
        else:
            platform_pct = float(row.iloc[0]["Taxa plataforma (%)"])
            spread_pct = float(row.iloc[0]["Spread (%)"])
            fixed_usd = float(row.iloc[0]["Tarifa fixa (USD)"])

        total_pct = (platform_pct + spread_pct) / 100.0
        if total_pct < 0 or total_pct >= 1 or fixed_usd < 0:
            continue

        net_usd = max(0.0, gross_usd * (1.0 - total_pct) - fixed_usd)
        received = net_usd / prices[destination]
        results.append({
            "Destino": destination,
            "Valor líquido recebido": received,
            "Equivalente líquido (USD)": net_usd,
            "Taxas + spread (%)": platform_pct + spread_pct,
            "Tarifa fixa (USD)": fixed_usd,
            "Variação vs. origem (USD)": net_usd - gross_usd,
        })

    results.sort(key=lambda item: item["Equivalente líquido (USD)"], reverse=True)
    return results, gross_usd

# Header
left, right = st.columns([5, 1])
with left:
    st.markdown('<div class="fx-kicker">CÂMBIO INTELIGENTE · COMPARADOR DE ROTAS</div>', unsafe_allow_html=True)
    st.title("FX Profit Optimizer")
    st.markdown('<div class="fx-subtitle">Descubra onde seu dinheiro entrega o melhor valor líquido.</div>', unsafe_allow_html=True)
with right:
    st.markdown("<div style='text-align:right;font-size:2.3rem;padding-top:.6rem'>💱</div>", unsafe_allow_html=True)

st.write("")
st.markdown('<div class="fx-panel">', unsafe_allow_html=True)
st.markdown("### Qual moeda você tem?")
st.caption("Informe o saldo disponível e selecione o ativo de origem.")
with st.form("conversion_form"):
    amount_col, asset_col = st.columns([4, 1.25], vertical_alignment="bottom")
    with amount_col:
        amount = st.number_input(
            "Valor disponível",
            min_value=0.0,
            value=10.0,
            step=1.0,
            format="%.8f",
        )
    with asset_col:
        origin = st.selectbox("Moeda de origem", list(ASSETS.keys()), index=0)
    submitted = st.form_submit_button("Encontrar melhor conversão  →", type="primary", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.write("")
with st.expander("⚙️ Configurações avançadas — custos e taxas", expanded=False):
    st.caption("Preencha os custos reais cobrados pela plataforma ou rota que você pretende utilizar. Zero significa que nenhum custo foi informado.")
    costs = st.data_editor(
        DEFAULT_COSTS,
        hide_index=True,
        use_container_width=True,
        key="route_costs_v2",
        column_config={
            "Destino": st.column_config.TextColumn("Destino", disabled=True),
            "Taxa plataforma (%)": st.column_config.NumberColumn("Taxa plataforma (%)", min_value=0.0, max_value=99.0, step=0.05, format="%.3f"),
            "Spread (%)": st.column_config.NumberColumn("Spread (%)", min_value=0.0, max_value=99.0, step=0.05, format="%.3f"),
            "Tarifa fixa (USD)": st.column_config.NumberColumn("Tarifa fixa (USD)", min_value=0.0, step=0.01, format="%.4f"),
        },
    )
    network_fee = st.number_input(
        "Custo de rede/saque adicional (USD)",
        min_value=0.0,
        value=0.0,
        step=0.01,
        format="%.4f",
        help="Custo fixo cobrado na origem. Informe em USD equivalente; não inclua aqui uma taxa já cadastrada na tabela.",
    )

st.write("")
st.markdown("### Melhor resultado")
if submitted:
    if amount <= 0:
        st.error("Informe um valor maior que zero.")
    else:
        with st.spinner("Consultando cotações públicas e calculando as rotas..."):
            prices, sources, errors = fetch_market_prices()

        missing = [asset for asset in ASSETS if asset not in prices]
        if origin not in prices:
            st.error(f"Não foi possível obter a cotação de {origin}. Tente novamente mais tarde.")
        else:
            effective_usd = amount * prices[origin] - network_fee
            if effective_usd <= 0:
                st.error("Os custos informados consomem todo o valor de origem.")
            else:
                adjusted_amount = effective_usd / prices[origin]
                ranking, gross_usd = build_ranking(adjusted_amount, origin, prices, costs)
                if not ranking:
                    st.error("Não foi possível calcular rotas com as cotações disponíveis.")
                else:
                    best = ranking[0]
                    st.markdown('<div class="fx-panel">', unsafe_allow_html=True)
                    st.markdown(f'<div class="fx-kicker">MELHOR RESULTADO ESTIMADO</div>', unsafe_allow_html=True)
                    best_col, amount_col2, usd_col = st.columns([1, 2, 1.5])
                    best_col.metric("Destino recomendado", best["Destino"])
                    amount_col2.metric("Valor líquido estimado", money(best["Valor líquido recebido"], best["Destino"]))
                    usd_col.metric("Equivalente líquido", f'US$ {best["Equivalente líquido (USD)"]:,.4f}')
                    st.markdown("</div>", unsafe_allow_html=True)

                    st.write("")
                    st.markdown("#### Ranking de conversões")
                    display_rows = []
                    for index, item in enumerate(ranking, start=1):
                        display_rows.append({
                            "Posição": index,
                            "Destino": item["Destino"],
                            "Valor líquido recebido": money(item["Valor líquido recebido"], item["Destino"]),
                            "Equivalente líquido (USD)": f'US$ {item["Equivalente líquido (USD)"]:,.4f}',
                            "Taxas + spread": f'{item["Taxas + spread (%)"]:.3f}%',
                            "Tarifa fixa": f'US$ {item["Tarifa fixa (USD)"]:,.4f}',
                        })
                    st.dataframe(pd.DataFrame(display_rows), hide_index=True, use_container_width=True)

                    st.caption(
                        f"Origem: {money(amount, origin)} · valor bruto de referência: US$ {gross_usd:,.4f} · "
                        f"custo de rede informado: US$ {network_fee:,.4f}"
                    )
                    st.markdown("#### Cotação e transparência")
                    st.caption(" | ".join(sources) if sources else "Nenhuma fonte de cotação respondeu.")
                    if missing:
                        st.warning("Sem cotação nesta consulta para: " + ", ".join(missing) + ". Essas moedas foram omitidas do ranking.")
                    if errors:
                        with st.expander("Detalhes das fontes indisponíveis"):
                            for error in errors:
                                st.write("• " + error)
                    st.info("O ranking compara o equivalente líquido em USD. Cotações públicas são indicativas e podem diferir do preço executável, da liquidez e das taxas da sua corretora.")
else:
    st.markdown(
        '<div class="fx-panel"><div style="font-size:1.05rem;font-weight:650">Sua próxima conversão começa aqui.</div>'
        '<div style="color:#a1a1aa;margin-top:.4rem">Informe o valor, escolha a moeda e clique em “Encontrar melhor conversão”. '
        'O ranking mostrará quanto você receberia em cada ativo disponível.</div></div>',
        unsafe_allow_html=True,
    )

st.write("")
with st.expander("Como o cálculo funciona"):
    st.markdown("""
    1. O aplicativo consulta preços públicos de criptoativos e taxas de câmbio fiduciárias.
    2. Converte o valor de origem para um equivalente de referência em USD.
    3. Deduz o custo de rede informado e os custos percentuais/fixos cadastrados para cada destino.
    4. Converte o valor líquido para cada ativo e ordena pelo equivalente líquido em USD.

    **Limitações:** CoinGecko e Frankfurter são fontes de referência, não cotações executáveis de corretoras. As taxas da tabela começam em zero e precisam ser preenchidas com os custos reais da rota. O aplicativo não acessa contas, não executa ordens e não movimenta fundos.
    """)

st.divider()
st.caption(
    f"FX Profit Optimizer · Interface v2 · Cotações em cache por 60 segundos · "
    f"Atualizado em {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
)
