"""Layer 3 — cost of equity and value-creation spread.

Week 1 scope: ex-ante CAPM with PROVISIONAL inputs (src/config.py) and
weekly-return betas with Blume adjustment. Excess Return valuation,
justified P/B and scenarios are added in weeks 4–5.

    python -m src.model
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import config


def weekly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.resample("W-FRI").last().pct_change(fill_method=None).dropna(how="all")


def ols_beta(stock: pd.Series, market: pd.Series) -> float:
    df = pd.concat([stock, market], axis=1).dropna()
    if len(df) < 52:
        return np.nan
    x, y = df.iloc[:, 1].to_numpy(), df.iloc[:, 0].to_numpy()
    return float(np.cov(y, x, ddof=1)[0, 1] / np.var(x, ddof=1))


def blume(beta: float) -> float:
    """Blume (1971) adjustment toward 1."""
    return 0.67 * beta + 0.33


def betas_by_year(rets: pd.DataFrame, window_years: int, adjust: bool) -> pd.DataFrame:
    """Beta at each year-end using the trailing `window_years` of weekly returns."""
    rows = []
    for bank in config.BANKS:
        for year in range(config.START_YEAR, config.END_YEAR + 1):
            end = pd.Timestamp(f"{year}-12-31")
            win = rets.loc[end - pd.DateOffset(years=window_years):end]
            raw = ols_beta(win.get(bank["ticker"], pd.Series(dtype=float)), win[config.MARKET_INDEX])
            rows.append({"bank": bank["name"], "year": year, "beta_raw": raw,
                         "beta": blume(raw) if adjust else raw})
    return pd.DataFrame(rows)


def capm(beta: float | pd.Series, rf: float, erp: float):
    """Ke = Rf + beta * ERP  (ex-ante; never realized index returns)."""
    return rf + beta * erp


def main() -> None:
    a = config.KE_ASSUMPTIONS
    prices = pd.read_parquet(config.DATA_RAW / "market" / "adj_close.parquet")
    betas = betas_by_year(weekly_returns(prices), a["beta_window_years"], a["blume_adjust"])
    betas["ke"] = capm(betas["beta"], a["rf_nominal_brl"], a["erp"])

    fund = pd.read_parquet(config.DATA_PROCESSED / "fundamentals.parquet")
    df = fund.merge(betas, on=["bank", "year"], how="left")
    df["spread"] = df["roe"] - df["ke"]
    df.to_parquet(config.DATA_PROCESSED / "ke_spread.parquet", index=False)
    print(df.pivot_table(index="year", columns="bank", values="spread").map("{:.1%}".format))


if __name__ == "__main__":
    main()
