
import streamlit as st

st.set_page_config(
    page_title="FX Profit Optimizer",
    page_icon="💱",
    layout="centered",
)

st.title("💱 FX Profit Optimizer")
st.caption("Compare moedas, custos e rotas de conversão.")

st.info(
    "Protótipo inicial: os resultados abaixo usam "
    "dados fictícios, apenas para demonstrar o cálculo."
)

amount = st.number_input(
    "Quanto você possui?",
    min_value=0.01,
    value=10.00,
    step=1.00,
)

source = st.selectbox(
    "Moeda de origem",
    ["BRL", "USD", "EUR", "USDT"],
)

target = st.selectbox(
    "Moeda de destino",
    ["EUR", "USD", "BRL", "USDT"],
)

st.subheader("Simulador de custos")

fee_percent = st.number_input(
    "Tarifa percentual (%)",
    min_value=0.0,
    max_value=100.0,
    value=0.0,
    step=0.1,
)

fixed_fee = st.number_input(
    "Tarifa fixa na moeda de destino",
    min_value=0.0,
    value=0.0,
    step=0.01,
)

rate = st.number_input(
    "Cotação de demonstração",
    min_value=0.000001,
    value=1.0,
    step=0.01,
    format="%.6f",
)

if st.button("Calcular conversão", type="primary"):
    gross = amount * rate
    net = gross * (1 - fee_percent / 100) - fixed_fee

    st.metric("Valor bruto", f"{gross:,.4f} {target}")
    st.metric("Valor líquido", f"{max(0, net):,.4f} {target}")

    if net < 0:
        st.error("Os custos superam o valor convertido.")
    else:
        st.success(
            "Cálculo concluído. Este resultado não é "
            "uma cotação real nem uma recomendação ao vivo."
        )

st.divider()
st.caption(
    "Projeto independente. Nenhuma operação financeira "
    "é executada pelo site."
)
