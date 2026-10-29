# FX Profit Optimizer

Streamlit MVP to compare estimated net proceeds when moving trading surplus from USDC into USDC, BRL, EUR, or EURI.

## Features
- Editable balance, withdrawal fee, additional network cost, exchange rates, stablecoin prices, platform fees, spreads, and fixed costs.
- Ranking by estimated net USD equivalent.
- Clear distinction between demonstration values and indicative fiat FX rates.
- Optional indicative USD/BRL and EUR/USD rates from Frankfurter.
- No exchange account access, transaction signing, or transfers.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Free deployment
1. Push the files to GitHub.
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Select the repository, branch `main`, and main file `app.py`.
4. Deploy, subject to current Streamlit Community Cloud availability and limits.
5. Demo mode needs no API key. Indicative live FX requires internet access to Frankfurter.

## Calculation notes
- Starting balance is assumed to be USDC.
- Withdrawal fee is deducted in USDC.
- Additional network costs are deducted in USD equivalent, converted using the configured USDC/USD price.
- The remaining value is converted to each destination, then platform fee, spread, and fixed fee are deducted.
- Ranking uses net USD equivalent, not raw currency units.
- Default rates and fees are illustrative only; replace with executable quotes and actual fee schedules before decisions.
- EURI is a token, not a bank euro. Confirm exact token, trading pair, supported venue, and network.
- Stablecoins carry issuer, liquidity, depeg, smart-contract, and chain risks. This tool does not forecast returns or provide individualized investment advice.
