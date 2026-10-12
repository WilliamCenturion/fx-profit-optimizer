
import streamlit as st

st.set_page_config(
    page_title="FX Profit Optimizer",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .stApp {
        background: #0b1120;
        color: #e5edf7;
    }
    [data-testid="stHeader"] {
        background: rgba(11,17,32,0.95);
    }
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3, p, label {
        color: #e5edf7;
    }
    .hero {
        background: linear-gradient(135deg, #17243a, #102b32);
        border: 1px solid #294650;
        border-radius: 18px;
        padding: 28px;
        margin-bottom: 22px;
    }
    .hero p {
        color: #a9bacd;
    }
    .eyebrow {
        color: #65dec6;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
    }
    .panel {
        background: #131e30;
        border: 1px solid #27364b;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .muted {
        color: #9aacc2;
        font-size: 13px;
    }
    .result {
        background: #142f32;
        border: 1px solid #28635c;
        border-radius: 15px;
        padding: 22px;
        margin: 16px 0;
    }
    .result-label {
        color: #75e2cb;
        font-size: 13px;
        font-weight: 700;
    }
    div.stButton > button[kind="primary"] {
        background: #61d9bf;
        color: #0b1720;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        min-height: 48px;
        width: 100%;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #8cebd7;
        color: #0b1720;
    }
    [data-testid="stMetric"] {
        background: #131e30;
        border: 1px solid #27364b;
        padding: 15px;
        border-radius: 12px;
    }
    [data-testid="stMetricValue"] {
        color: #75e2cb;
    }
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background: #172338;
        border-color: #35445a;
    }
    hr {
        border-color: #27364b;
    }
</style>
""", unsafe_allow_html=True)

currencies = {
    "BRL": "🇧🇷 Real brasileiro",
    "USD": "🇺🇸 Dólar americano",
    "EUR": "🇪🇺 Euro",
    "USDT": "₮ Tether",
}

st.markdown("""
<div class="hero">
    <div class="eyebrow">SMART CURRENCY EXCHANGE</div>
    <h1 style="font-size:36px; margin-bottom:4px;">
        FX Profit Optimizer
    </h1>
    <p style="font-size:16px;">
        Compare moedas, plataformas e custos.
        Descubra qual rota entrega mais dinheiro.
    </p>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("💰 Sua conversão")

    amount = st.number_input(
        "Quanto você possui?",
        min_value=0.01,
        value=100.00,
        step=10.00,
        format="%.2f",
    )

    source = st.selectbox(
        "Moeda de origem",
        list(currencies.keys()),
        format_func=lambda x: f"{x} — {currencies[x]}",
        index=0,
    )

    target_options = [
        c for c in currencies.keys() if c != source
    ]

    target = st.selectbox(
        "Quero receber",
        target_options,
        format_func=lambda x: f"{x} — {currencies[x]}",
        index=0,
    )

    st.markdown("**Como pretende movimentar o dinheiro?**")

    payment_options = {
        "PIX": "BRL",
        "Transferência bancária": "BRL",
        "Saldo em plataforma": "QUALQUER",
        "Criptomoeda": "CRYPTO",
    }

    payment = st.selectbox(
        "Método de entrada ou origem",
        list(payment_options.keys()),
        index=0 if source == "BRL" else 2,
    )

    st.markdown(
        '<p class="muted">O método selecionado é uma '
        'preferência para a comparação, não uma confirmação '
        'de disponibilidade.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("🌐 Onde comparar")

    providers = st.multiselect(
        "Plataformas de interesse",
        [
            "Wise",
            "Nomad",
            "Binance",
            "Coinbase",
            "Bitso",
            "Outras plataformas",
        ],
        default=["Wise", "Nomad", "Binance", "Bitso"],
    )

    st.markdown("**O que importa para você?**")

    priority = st.radio(
        "Critério de recomendação",
        [
            "Maior valor líquido recebido",
            "Menores custos totais",
        ],
        index=0,
    )

    st.markdown(
        '<p class="muted">A comparação futura incluirá '
        'cotação, spread, taxas e custos de transferência. '
        'Somente rotas compatíveis serão classificadas.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("### 📊 Resultado da comparação")

st.markdown("""
<div class="result">
    <div class="result-label">MOTOR DE RECOMENDAÇÃO</div>
    <h3 style="margin-bottom:6px;">Encontre a melhor rota</h3>
    <p style="color:#b6c9d5; margin-bottom:0;">
        Informe os dados da conversão e compare as alternativas
        quando as cotações e tarifas estiverem disponíveis.
    </p>
</div>
""", unsafe_allow_html=True)

if st.button("🔎 Comparar conversões", type="primary"):
    if source == target:
        st.warning("Escolha moedas diferentes.")
    elif not providers:
        st.warning("Selecione ao menos uma plataforma.")
    else:
        st.info(
            "A interface está pronta para receber o motor "
            "de comparação. Ainda não existem cotações reais "
            "nem tarifas integradas."
        )

        st.markdown("#### Resumo da sua consulta")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Capital informado",
            f"{amount:,.2f} {source}",
        )

        c2.metric("Destino", target)

        c3.metric(
            "Plataformas selecionadas",
            str(len(providers)),
        )

        st.caption(
            f"Método escolhido: {payment} · "
            f"Critério: {priority}"
        )

st.divider()

st.markdown("""
<div style="text-align:center; padding:12px;">
    <p style="color:#9aacc2; font-size:13px;">
        FX Profit Optimizer · Compare antes de converter.
    </p>
    <p style="color:#74869e; font-size:11px;">
        Protótipo demonstrativo. Não executa transações
        financeiras. Cotações reais serão integradas
        em uma próxima etapa.
    </p>
</div>
""", unsafe_allow_html=True)
