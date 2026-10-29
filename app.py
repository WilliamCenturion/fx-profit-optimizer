import streamlit as st
import pandas as pd
from datetime import datetime, timezone

st.set_page_config(page_title="FX Profit Optimizer", page_icon="💱", layout="wide")
st.markdown("""
<style>
.stApp { background: #0b1120; color: #e5edf7; }
[data-testid="stSidebar"] { background: #111a2b; }
.block-container { max-width: 1240px; padding-top: 1.6rem; }
</style>
""", unsafe_allow_html=True)

st.title("💱 FX Profit Optimizer")
st.caption("Compare o valor líquido estimado do excedente de trading. O app não executa transações.")

with st.sidebar:
    st.header("Capital de origem")
    amount = st.number_input("Saldo disponível (USDC)", min_value=0.0, value=200.0, step=10.0, format="%.4f")
    withdrawal_fee = st.number_input("Taxa de retirada (USDC)", min_value=0.0, value=0.20, step=0.05, format="%.4f")
    network_fee_usd = st.number_input("Custo adicional de rede (USD)", min_value=0.0, value=0.05, step=0.01, format="%.4f")
    st.divider()
    st.header("Cotações de referência")
    mode = st.radio("Fonte de câmbio", ["Demonstração/editável", "Buscar câmbio fiduciário indicativo"])
    usd_brl_default, eur_usd_default = 5.50, 1.08
    quote_source = "SIMULADO — substitua pelos valores atuais"
    if mode == "Buscar câmbio fiduciário indicativo":
        try:
            import requests
            response = requests.get("https://api.frankfurter.app/latest?from=USD&to=BRL,EUR", timeout=5)
            response.raise_for_status()
            quote = response.json()
            usd_brl_default = float(quote["rates"]["BRL"])
            eur_usd_default = 1.0 / float(quote["rates"]["EUR"])
            quote_source = f"Frankfurter API — taxa indicativa com data {quote.get('date', 'não informada')}"
        except Exception:
            st.warning("Não foi possível consultar a API; confira e preencha as taxas manualmente.")
            quote_source = "Consulta indisponível — valores editáveis abaixo"
    usd_brl = st.number_input("1 USD = BRL", min_value=0.0001, value=float(usd_brl_default), step=0.01, format="%.5f")
    eur_usd = st.number_input("1 EUR = USD", min_value=0.0001, value=float(eur_usd_default), step=0.01, format="%.5f")
    usdc_usd = st.number_input("Preço de 1 USDC em USD", min_value=0.0001, value=1.0, step=0.001, format="%.5f")
    euri_eur = st.number_input("Preço de 1 EURI em EUR", min_value=0.0001, value=1.0, step=0.001, format="%.5f")
    st.caption(quote_source)

st.subheader("Custos por rota")
st.write("Edite as tarifas da plataforma, o spread e a tarifa fixa de cada destino. Percentuais são aplicados ao valor convertido.")
fee_defaults = pd.DataFrame([
    {"Destino": "USDC", "Taxa plataforma (%)": 0.10, "Spread (%)": 0.05, "Tarifa fixa (USD)": 0.00},
    {"Destino": "BRL", "Taxa plataforma (%)": 0.50, "Spread (%)": 0.40, "Tarifa fixa (USD)": 0.00},
    {"Destino": "EUR", "Taxa plataforma (%)": 0.30, "Spread (%)": 0.20, "Tarifa fixa (USD)": 0.00},
    {"Destino": "EURI", "Taxa plataforma (%)": 0.20, "Spread (%)": 0.20, "Tarifa fixa (USD)": 0.00},
])
fees = st.data_editor(
    fee_defaults, hide_index=True, use_container_width=True, disabled=["Destino"], key="route_costs",
    column_config={
        "Taxa plataforma (%)": st.column_config.NumberColumn(min_value=0.0, max_value=99.0, step=0.05, format="%.3f"),
        "Spread (%)": st.column_config.NumberColumn(min_value=0.0, max_value=99.0, step=0.05, format="%.3f"),
        "Tarifa fixa (USD)": st.column_config.NumberColumn(min_value=0.0, max_value=10000.0, step=0.01, format="%.4f"),
    },
)

st.subheader("Ranking por valor líquido")
if amount <= 0:
    st.info("Informe um saldo maior que zero.")
elif withdrawal_fee >= amount:
    st.error("A taxa de retirada precisa ser menor que o saldo disponível.")
else:
    usdc_remaining = amount - withdrawal_fee - network_fee_usd / usdc_usd
    if usdc_remaining <= 0:
        st.error("Os custos de origem consomem todo o saldo. Ajuste as taxas.")
    else:
        usd_remaining = usdc_remaining * usdc_usd
        gross_units = {
            "USDC": usd_remaining / usdc_usd,
            "BRL": usd_remaining * usd_brl,
            "EUR": usd_remaining / eur_usd,
            "EURI": usd_remaining / (eur_usd * euri_eur),
        }
        usd_per_unit = {
            "USDC": usdc_usd,
            "BRL": 1.0 / usd_brl,
            "EUR": eur_usd,
            "EURI": eur_usd * euri_eur,
        }
        results = []
        for _, row in fees.iterrows():
            asset = row["Destino"]
            platform_rate = float(row["Taxa plataforma (%)"]) / 100.0
            spread_rate = float(row["Spread (%)"]) / 100.0
            fixed_usd = float(row["Tarifa fixa (USD)"])
            if platform_rate < 0 or spread_rate < 0 or platform_rate + spread_rate >= 1 or fixed_usd < 0:
                continue
            net_usd = max(0.0, usd_remaining * (1.0 - platform_rate - spread_rate) - fixed_usd)
            results.append({
                "Destino": asset,
                "Valor líquido recebido": net_usd / usd_per_unit[asset],
                "Equivalente líquido (USD)": net_usd,
                "Taxas + spread (%)": (platform_rate + spread_rate) * 100,
                "Tarifa fixa (USD)": fixed_usd,
                "Valor bruto estimado": gross_units[asset],
            })
        if not results:
            st.error("Revise as tarifas: taxa da plataforma + spread precisam somar menos de 100%.")
        else:
            ranking = pd.DataFrame(results).sort_values("Equivalente líquido (USD)", ascending=False).reset_index(drop=True)
            ranking.insert(0, "Ranking", range(1, len(ranking) + 1))
            best = ranking.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Melhor resultado pelos custos informados", best["Destino"])
            c2.metric("Valor líquido", f'{best["Valor líquido recebido"]:,.4f} {best["Destino"]}')
            c3.metric("Equivalente líquido", f'US$ {best["Equivalente líquido (USD)"]:,.4f}')
            st.dataframe(ranking.style.format({
                "Valor líquido recebido": "{:,.4f}",
                "Equivalente líquido (USD)": "US$ {:,.4f}",
                "Taxas + spread (%)": "{:.3f}%",
                "Tarifa fixa (USD)": "US$ {:.4f}",
                "Valor bruto estimado": "{:,.4f}",
            }), use_container_width=True, hide_index=True)
            st.caption(f"Saldo inicial: {amount:.4f} USDC · após custos de origem: {usdc_remaining:.4f} USDC equivalentes · antes dos custos do destino: US$ {usd_remaining:.4f}")

st.warning("Valores de demonstração por padrão. Câmbio fiduciário indicativo não é preço executável de corretora; USDC/EURI e as taxas devem ser conferidos no destino. O ranking compara o valor líquido estimado em USD e não prevê valorização futura.")
with st.expander("Metodologia e limitações"):
    st.markdown("""
    1. Deduz a taxa de retirada em USDC e custos de rede expressos em USD equivalente.
    2. Converte o saldo restante para o ativo de destino usando as cotações configuradas.
    3. Deduz taxa percentual da plataforma, spread e tarifa fixa.
    4. Ordena pelo equivalente líquido em USD para comparar unidades diferentes.

    As tarifas são editáveis e não são obtidas automaticamente. A API opcional fornece câmbio fiduciário indicativo, não cotação executável.
    Confirme o ticker exato (EURI e EURC são tokens diferentes), par, liquidez, rede e tarifas na corretora.
    Stablecoins têm riscos de emissor, liquidez, perda de paridade, contrato inteligente e rede. O app não acessa contas nem movimenta fundos.
    """)
st.divider()
st.caption(f"FX Profit Optimizer · MVP · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · Não executa transações.")
