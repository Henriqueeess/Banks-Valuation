# Brazilian Banks Valuation — Excess Return Model (v2, work in progress)

> **Not investment advice.** Academic and portfolio project.

Valuation of Brazil's four largest listed banks — Itaú Unibanco (ITUB4), Bradesco (BBDC4), Banco do Brasil (BBAS3) and Santander Brasil (SANB11) — over 2010–2025.

## Problem
A high ROE doesn't make a bank cheap or expensive — the spread over its cost of equity does. Version 1 measured the historical ROE − Ke spread. Version 2 turns it into a full valuation: intrinsic value per share vs. market price, justified vs. market P/B, scenarios and sensitivity.

## Why not DCF?
For banks, debt is an operating input, regulatory capital constrains reinvestment and free cash flow is hard to define. Equity-based models (Excess Return / Residual Income) are the standard for financial institutions.

## Data
| Data | Source |
|---|---|
| Net income, equity (DFP) | CVM Open Data |
| Selic, IPCA | BCB SGS (series 432, 433) |
| Prices, IBOV | Yahoo Finance (`yfinance`) |
| ERP, country risk, sector betas | Damodaran *(week 3)* |
| NII, provisions, loan book | BCB IF.data *(week 6)* |

## Method
- **ROE** = net income attributable to controlling shareholders / beginning-of-year controlling equity.
- **Ke (CAPM, ex-ante)** = Rf + β × ERP. β from weekly returns vs. IBOV (5-year window, Blume-adjusted). Inputs in `src/config.py` are **provisional** until week 3.
- **Excess Return model, justified P/B, scenarios, ROE decomposition** — coming (see roadmap).

## Project structure
```
src/
  config.py      banks, period, paths, assumptions
  fetch.py       raw data  -> data/raw/*.parquet
  transform.py   CVM cleaning -> data/processed/fundamentals.parquet
  model.py       beta, Ke, spread -> data/processed/ke_spread.parquet
  report.py      figures and tables -> outputs/
  diagnose.py    data-coverage diagnostics
tests/           pytest
legacy/          v1 script (kept for reference)
```

## How to run
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py              # fetch -> transform -> model -> report
python -m src.diagnose     # check year x bank coverage
pytest
```

## Roadmap
- [x] Repository restructure, Parquet layers, tests
- [x] Fix: net income double counting; Ke from realized index returns
- [ ] Fix: Bradesco/BB/Santander data gap after 2019 (diagnose with `src.diagnose`)
- [ ] Sourced Ke (NTN-B / Damodaran), beta comparison
- [ ] Excess Return valuation, value per share, upside/downside
- [ ] Justified vs. market P/B, scenarios, Ke × g sensitivity
- [ ] DuPont ROE decomposition (IF.data)

## Limitations
Bank betas are unstable (state ownership at BB, Bradesco's 2023 downturn); valuation is highly sensitive to Ke − g; COSIF vs. IFRS and recurring vs. reported ROE differences.
