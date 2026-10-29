
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="FX Profit Optimizer",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- ESTILO ----------
st.markdown("""
<style>
.stApp {
    background: #0b1120;
    color: #e5edf7;
}
.block-container {
    max-width: 1120px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}
.hero {
    background: linear-gradient(120deg, #17243a, #103331);
    border: 1px solid #294650;
    border-radius: 18px;
    padding: 28px;
    margin-bottom: 26px;
}
.eyebrow {
    color: #70e0c7;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
}
.panel {
    background: #131e30;
    border: 1px solid #293950;
    border-radius: 15px;
    padding: 22px;
    margin-bottom: 18px;
}
.result-panel {
    background: #12302f;
    border: 1px solid #28635c;
    border-radius: 15px;
    padding: 22px;
    margin: 12px 0 20px 0;
}
.small-muted {
    color: #9aacc2;
    font-size: 13px;
}
div.stButton > button[kind="primary"] {
    background: #61d9bf;
    color: #0b1720;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    min-height: 46px;
}
div.stButton > button[kind="primary"]:hover {
    background: #8cebd7;
    color: #0b1720;
}
[data-testid="stMetric"] {
    background: #131e30;
    border: 1px solid #293950;
    border-radius: 12px;
    padding: 16px;
}
[data-testid="stMetricValue"] {
    color: #70e0c7;
}
hr {
    border-color: #293950;
}
</style>
""", unsafe_allow_html=True)

CURRENCIES = {
    "BRL": "🇧🇷 Real brasileiro",
    "USD": "🇺🇸 Dólar americano",
    "EUR": "🇪🇺 Euro",
    "USDT": "₮ Tether",
}

PROVIDERS = [
    "Wise",
    "Nomad",
    "Binance",
    "Coinbase",
    "Bitso",
    "Outras plataformas",
]

# ---------- CABEÇALHO ----------
st.markdown("""
<div class="hero">
    <div class="eyebrow">SMART CURRENCY EXCHANGE</div>
    <h1 style="font-size:36px; margin:10px 0;">
        FX Profit Optimizer
    </h1>
    <p style="font-size:16px; margin-bottom:0;">
        Compare cotações, taxas e rotas para descobrir
        onde seu dinheiro rende mais na conversão.
    </p>
</div>
""", unsafe_allow_html=True)

# ---------- FORMULÁRIO ----------
left, right = st.columns(2, gap="large")

with left:
    st.markdown("### 💰 Sua conversão")

    amount = st.number_input(
        "Quanto você possui?",
        min_value=0.01,
        value=100.00,
        step=10.00,
        format="%.2f",
    )

    source = st.selectbox(
        "Moeda de origem",
        list(CURRENCIES.keys()),
        format_func=lambda c: f"{c} — {CURRENCIES[c]}",
        index=0,
    )

    destinations = [
        c for c in CURRENCIES if c != source
    ]

    target = st.selectbox(
        "Quero receber",
        destinations,
        format_func=lambda c: f"{c} — {CURRENCIES[c]}",
    )

    st.markdown("**Meio de movimentação**")

    if source == "BRL":
        payment_options = [
            "PIX",
            "Transferência bancária",
            "Saldo em plataforma",
        ]
    elif source == "USDT":
        payment_options = [
            "Saldo em exchange",
            "Rede de criptomoedas",
        ]
    else:
        payment_options = [
            "Saldo em plataforma",
            "Transferência bancária",
        ]

    payment = st.selectbox(
        "Como pretende movimentar o dinheiro?",
        payment_options,
    )

    st.caption(
        "O método selecionado é uma preferência. "
        "A disponibilidade será verificada por provedor."
    )

with right:
    st.markdown("### 🌐 Plataformas para comparar")

    providers = st.multiselect(
        "Selecione as plataformas de interesse",
        PROVIDERS,
        default=["Wise", "Nomad", "Binance", "Bitso"],
    )

    priority = st.radio(
        "Qual é sua prioridade?",
        [
            "Maior valor líquido recebido",
            "Menores custos totais",
        ],
    )

    st.markdown("**O que será considerado**")

    st.markdown("""
    - Cotação efetiva oferecida.
    - Tarifas e spread cambial.
    - Custos de entrada, saída e transferência.
    - Compatibilidade da rota com a moeda escolhida.
    """)

    st.caption(
        "Só serão classificadas rotas com dados suficientes."
    )

st.divider()

# ---------- RESULTADO ----------
st.markdown("### 📊 Comparação de conversões")

st.markdown("""
<div class="result-panel">
    <div class="eyebrow">MOTOR DE RECOMENDAÇÃO</div>
    <h3 style="margin:10px 0;">
        Compare antes de converter
    </h3>
    <p style="margin-bottom:0;">
        O objetivo é encontrar o maior saldo líquido
        na moeda de destino, considerando todos os custos.
    </p>
</div>
""", unsafe_allow_html=True)

compare = st.button(
    "🔎 Preparar comparação",
    type="primary",
    use_container_width=True,
)

if compare:
    if not providers:
        st.warning("Selecione pelo menos uma plataforma.")
    else:
        st.info(
            "A interface está preparada. As integrações de "
            "cotações e tarifas reais ainda não foram conectadas."
        )

        rows = []

        for provider in providers:
            rows.append({
                "Plataforma": provider,
                "Rota": f"{source} → {target}",
                "Cotação": "Pendente",
                "Custos": "Pendente",
                "Valor líquido": "Indisponível",
                "Situação": "Aguardando dados reais",
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            f"Valor informado: {amount:.2f} {source} · "
            f"Método: {payment} · Prioridade: {priority}"
        )

        st.warning(
            "Ainda não há uma recomendação vencedora. "
            "Não seria confiável escolher uma plataforma "
            "sem consultar suas cotações, tarifas e condições."
        )
else:
    st.markdown("""
    <div class="panel">
        <p style="margin-bottom:5px;">
            <strong>O que você verá aqui</strong>
        </p>
        <p class="small-muted" style="margin-bottom:0;">
            Ranking de provedores, cotação, custo total,
            valor líquido e indicação da melhor rota elegível.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ---------- RODAPÉ ----------
st.divider()

st.caption(
    "FX Profit Optimizer · Protótipo em desenvolvimento. "
    "Não executa transações financeiras. "
    "As cotações reais serão integradas posteriormente."
)
