"""Central configuration: banks, period, paths and (provisional) Ke assumptions."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"

START_YEAR = 2010
END_YEAR = 2025
VALUATION_DATE = "2025-12-31"

BANKS = [
    {"name": "Itaú Unibanco",   "ticker": "ITUB4.SA",  "cnpj": "60.872.504/0001-23"},
    {"name": "Bradesco",        "ticker": "BBDC4.SA",  "cnpj": "60.746.948/0001-12"},
    {"name": "Banco do Brasil", "ticker": "BBAS3.SA",  "cnpj": "00.000.000/0001-91"},
    {"name": "Santander BR",    "ticker": "SANB11.SA", "cnpj": "90.400.888/0001-42"},
]
MARKET_INDEX = "^BVSP"

# ── Cost of equity (CAPM) ─────────────────────────────────────────────
# PROVISIONAL values (week 1). To be replaced in week 3 by sourced and
# dated inputs: NTN-B long real yield + Focus inflation (Option B) or
# UST 10y + country risk (Option A); Damodaran ERP. See README/Method.
# Country risk must be counted ONCE (either in Rf or in ERP, never both).
KE_ASSUMPTIONS = {
    "rf_nominal_brl": 0.130,   # PLACEHOLDER: long nominal BRL risk-free
    "erp": 0.055,              # PLACEHOLDER: equity risk premium (BRL)
    "beta_window_years": 5,    # weekly returns, rolling window
    "blume_adjust": True,      # beta_adj = 0.67*beta + 0.33*1
}
