import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone

# ---------------------------------------------------------
# VEXA — comparador de conversões | interface v3
# ---------------------------------------------------------
st.set_page_config(
    page_title="VEXA | Câmbio inteligente",
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
    {
        "Destino": asset,
        "Taxa plataforma (%)": 0.0,
        "Spread (%)": 0.0,
        "Tarifa fixa (USD)": 0.0,
    }
    for asset in ASSETS
])

# ---------------------------------------------------------
# Visual system — black / graphite / yellow + navy ranking
# ---------------------------------------------------------
st.markdown("""
<style>
:root {
    --vexa-black: #090a0c;
    --vexa-graphite: #17191d;
    --vexa-graphite-2: #202329;
    --vexa-border: #30343c;
    --vexa-yellow: #f2c400;
    --vexa-muted: #a4a8b0;
    --vexa-navy: #101d35;
    --vexa-navy-alt: #142541;
}
.stApp {
    background: var(--vexa-black);
    color: #f3f4f6;
}
[data-testid="stHeader"] {
    background: rgba(9, 10, 12, .96);
}
.block-container {
    max-width: 1080px;
    padding-top: 1.35rem;
    padding-bottom: 1.5rem;
}
[data-testid="stSidebar"] {
    background: var(--vexa-graphite);
}
h1, h2, h3, h4, p, label {
    color: #f3f4f6;
}
h1 {
    letter-spacing: -.045em;
    font-weight: 800 !important;
}
.fx-kicker {
    color: var(--vexa-yellow);
    letter-spacing: .19em;
    font-size: .70rem;
    font-weight: 800;
    text-transform: uppercase;
}
.fx-subtitle {
    color: var(--vexa-muted);
    font-size: .94rem;
    margin-top: -.35rem;
}
.fx-brand {
    color: #f5f5f5;
    font-size: 2.5rem;
    line-height: 1.05;
    font-weight: 850;
    letter-spacing: -.06em;
    margin: .25rem 0 .45rem 0;
}
.fx-brand span {
    color: var(--vexa-yellow);
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(145deg, #17191d, #111317);
    border: 1px solid var(--vexa-border);
    border-radius: 16px;
}
[data-testid="stMetric"] {
    background: #171a20;
    border: 1px solid #30343c;
    border-radius: 12px;
    padding: 12px 14px;
}
[data-testid="stMetricLabel"] {
    color: var(--vexa-muted);
}
[data-testid="stMetricValue"] {
    color: var(--vexa-yellow);
    font-weight: 750;
}
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] {
    background: var(--vexa-graphite-2);
    color: #fff;
    border-radius: 9px;
}
[data-testid="stNumberInput"] button {
    background: #292d34;
    color: #f3f4f6;
    border: 0;
}
div.stButton > button[kind="primary"],
div.stFormSubmitButton > button {
    background: var(--vexa-yellow);
    color: #101114;
    border: 0;
    border-radius: 10px;
    min-height: 2.9rem;
    font-weight: 850;
    width: 100%;
    transition: background .15s ease;
}
div.stButton > button[kind="primary"]:hover,
div.stFormSubmitButton > button:hover {
    background: #ffda35;
    color: #101114;
    border: 0;
}
[data-testid="stExpander"] {
    border: 1px solid var(--vexa-border);
    border-radius: 12px;
    background: #111317;
}
[data-testid="stDataFrame"] {
    border: 1px solid #263957;
    border-radius: 10px;
    overflow: hidden;
}
[data-testid="stDataFrame"] [role="grid"] {
    background: var(--vexa-navy);
}
[data-testid="stCaptionContainer"] {
    color: var(--vexa-muted);
}
hr {
    border-color: var(--vexa-border);
}
small, .stCaption {
    color: var(--vexa-muted) !important;
}
.stAlert {
    border-radius: 10px;
}
@media (max-width: 700px) {
    .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .fx-brand {
        font-size: 2.1rem;
    }
}
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
            "USDC": "usd-coin",
            "USDT": "tether",
            "BTC": "bitcoin",
            "ETH": "ethereum",
        }.items():
            value = data.get(coin_id, {}).get("usd")
            if value is not None and float(value) > 0:
                prices[symbol] = float(value)
        sources.append("CoinGecko (criptoativos)")
    except Exception as exc:
        errors.append(f"Criptoativos: {exc}")

    # Fiat currencies: Frankfurter reference FX rates against USD.
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
        sources.append(
            f"Frankfurter (câmbio fiduciário; data {data.get('date', 'não informada')})"
        )
    except Exception as exc:
        errors.append(f"Moedas fiduciárias: {exc}")

    return prices, sources, errors


def money(value, symbol):
    if symbol in ("BTC", "ETH"):
        return f"{value:,.8f} {symbol}"
    return f"{value:,.4f} {symbol}"


def build_ranking(amount, origin, prices, costs):
    """Calculate net destination values and rank by USD equivalent."""
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
            "Variação vs. base (USD)": net_usd - gross_usd,
        })

    results.sort(
        key=lambda item: item["Equivalente líquido (USD)"],
        reverse=True,
    )
    return results, gross_usd


def style_ranking(frame):
    """Apply a compact navy table with a clear first-place highlight."""
    def row_style(row):
        position = row.name
        if position == 0:
            return [
                "background-color: #263b5c; color: #f5d34f; font-weight: 700;"
            ] * len(row)
        shade = "#101d35" if position % 2 else "#142541"
        return [f"background-color: {shade}; color: #f2f4f8;"] * len(row)

    return (
        frame.style
        .apply(row_style, axis=1)
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("background-color", "#0b1425"),
                    ("color", "#d9e1ef"),
                    ("font-weight", "700"),
                    ("border-bottom", "1px solid #344765"),
                    ("padding", "8px 10px"),
                    ("font-size", "12px"),
                ],
            },
            {
                "selector": "td",
                "props": [
                    ("border-bottom", "1px solid #263957"),
                    ("padding", "7px 10px"),
                    ("font-size", "12px"),
                    ("white-space", "nowrap"),
                ],
            },
            {
                "selector": "table",
                "props": [
                    ("border-collapse", "collapse"),
                    ("width", "100%"),
                ],
            },
        ])
        .hide(axis="index")
    )


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.markdown(
    '<div class="fx-kicker">CÂMBIO INTELIGENTE · COMPARADOR DE ROTAS</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="fx-brand">VE<span>XA</span></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fx-subtitle">Compare o valor líquido estimado antes de converter seu dinheiro.</div>',
    unsafe_allow_html=True,
)

st.write("")

# ---------------------------------------------------------
# Input panel — native Streamlit container, no open HTML div
# ---------------------------------------------------------
with st.container(border=True):
    st.markdown("### Qual moeda você tem?")
    st.caption("Informe o saldo disponível e selecione o ativo de origem.")

    with st.form("conversion_form"):
        amount_col, asset_col = st.columns([3.5, 1.3], vertical_alignment="bottom")
        with amount_col:
            amount = st.number_input(
                "Valor disponível",
                min_value=0.0,
                value=10.0,
                step=1.0,
                format="%.8f",
            )
        with asset_col:
            origin = st.selectbox(
                "Moeda de origem",
                list(ASSETS.keys()),
                index=0,
            )
        submitted = st.form_submit_button(
            "Encontrar melhor conversão  →",
            type="primary",
            use_container_width=True,
        )

# ---------------------------------------------------------
# Advanced costs
# ---------------------------------------------------------
with st.expander("⚙️ Configurações avançadas — custos e taxas", expanded=False):
    st.caption(
        "Informe os custos reais cobrados pela plataforma ou rota. "
        "Zero significa que nenhum custo foi informado."
    )
    costs = st.data_editor(
        DEFAULT_COSTS,
        hide_index=True,
        use_container_width=True,
        key="route_costs_v3",
        column_config={
            "Destino": st.column_config.TextColumn(
                "Destino",
                disabled=True,
            ),
            "Taxa plataforma (%)": st.column_config.NumberColumn(
                "Taxa plataforma (%)",
                min_value=0.0,
                max_value=99.0,
                step=0.05,
                format="%.3f",
            ),
            "Spread (%)": st.column_config.NumberColumn(
                "Spread (%)",
                min_value=0.0,
                max_value=99.0,
                step=0.05,
                format="%.3f",
            ),
            "Tarifa fixa (USD)": st.column_config.NumberColumn(
                "Tarifa fixa (USD)",
                min_value=0.0,
                step=0.01,
                format="%.4f",
            ),
        },
    )
    network_fee = st.number_input(
        "Custo de rede/saque adicional (USD)",
        min_value=0.0,
        value=0.0,
        step=0.01,
        format="%.4f",
        help=(
            "Custo fixo cobrado na origem. Informe em USD equivalente; "
            "não inclua uma taxa já cadastrada na tabela."
        ),
        key="network_fee_v3",
    )

# ---------------------------------------------------------
# Results
# ---------------------------------------------------------
st.markdown("### Resultado da comparação")

if submitted:
    if amount <= 0:
        st.error("Informe um valor maior que zero.")
    else:
        with st.spinner("Consultando cotações públicas e calculando as rotas..."):
            prices, sources, errors = fetch_market_prices()

        missing = [asset for asset in ASSETS if asset not in prices]

        if origin not in prices:
            st.error(
                f"Não foi possível obter a cotação de {origin}. "
                "Tente novamente mais tarde."
            )
        else:
            original_gross_usd = amount * prices[origin]
            effective_usd = original_gross_usd - network_fee

            if effective_usd <= 0:
                st.error("Os custos informados consomem todo o valor de origem.")
            else:
                adjusted_amount = effective_usd / prices[origin]
                ranking, comparison_base_usd = build_ranking(
                    adjusted_amount,
                    origin,
                    prices,
                    costs,
                )

                if not ranking:
                    st.error(
                        "Não foi possível calcular rotas com as cotações disponíveis."
                    )
                else:
                    best = ranking[0]

                    with st.container(border=True):
                        st.markdown(
                            '<div class="fx-kicker">MELHOR RESULTADO ESTIMADO</div>',
                            unsafe_allow_html=True,
                        )
                        best_col, amount_col2, usd_col = st.columns([1, 2, 1.5])
                        best_col.metric(
                            "Destino recomendado",
                            best["Destino"],
                        )
                        amount_col2.metric(
                            "Valor líquido estimado",
                            money(
                                best["Valor líquido recebido"],
                                best["Destino"],
                            ),
                        )
                        usd_col.metric(
                            "Equivalente líquido",
                            f'US$ {best["Equivalente líquido (USD)"]:,.4f}',
                        )

                    st.write("")
                    st.markdown("#### Ranking de conversões")
                    st.caption(
                        "A primeira linha representa o maior equivalente líquido estimado em USD."
                    )

                    display_rows = []
                    for index, item in enumerate(ranking, start=1):
                        variation = item["Variação vs. base (USD)"]
                        display_rows.append({
                            " # ": f"{index:02d}",
                            "Destino": item["Destino"],
                            "Você recebe": money(
                                item["Valor líquido recebido"],
                                item["Destino"],
                            ),
                            "Líquido (USD)": (
                                f'US$ {item["Equivalente líquido (USD)"]:,.4f}'
                            ),
                            "Taxas + spread": (
                                f'{item["Taxas + spread (%)"]:.3f}%'
                            ),
                            "Tarifa fixa": (
                                f'US$ {item["Tarifa fixa (USD)"]:,.4f}'
                            ),
                            "Variação": (
                                f'{"+" if variation >= 0 else ""}US$ {variation:,.4f}'
                            ),
                        })

                    ranking_frame = pd.DataFrame(display_rows)
                    styled_ranking = style_ranking(ranking_frame)
                    st.dataframe(
                        styled_ranking,
                        hide_index=True,
                        use_container_width=True,
                        height=min(390, 46 + (len(display_rows) + 1) * 36),
                    )

                    st.caption(
                        f"Origem: {money(amount, origin)} · "
                        f"valor bruto de referência: US$ {original_gross_usd:,.4f} · "
                        f"custo de rede informado: US$ {network_fee:,.4f} · "
                        f"base comparável após rede: US$ {comparison_base_usd:,.4f}"
                    )

                    st.markdown("#### Cotação e transparência")
                    if sources:
                        st.caption("Fontes: " + " | ".join(sources))
                    else:
                        st.caption("Nenhuma fonte de cotação respondeu.")

                    if missing:
                        st.warning(
                            "Sem cotação nesta consulta para: "
                            + ", ".join(missing)
                            + ". Essas moedas foram omitidas do ranking."
                        )

                    if errors:
                        with st.expander("Detalhes das fontes indisponíveis"):
                            for error in errors:
                                st.write("• " + error)

                    st.info(
                        "O ranking compara equivalentes líquidos em USD usando "
                        "cotações públicas indicativas. Elas podem diferir do preço "
                        "executável, da liquidez e das taxas efetivas da corretora. "
                        "As taxas da tabela começam em zero e devem ser preenchidas "
                        "com os custos reais da rota."
                    )
else:
    with st.container(border=True):
        st.markdown("**Sua próxima conversão começa aqui.**")
        st.caption(
            "Informe o valor, escolha a moeda e clique em “Encontrar melhor conversão”. "
            "O VEXA calculará o valor líquido estimado para cada ativo disponível."
        )

# ---------------------------------------------------------
# Methodology and footer
# ---------------------------------------------------------
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
    f"VEXA · Interface v3 · Cotações em cache por 60 segundos · "
    f"Atualizado em {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
)
