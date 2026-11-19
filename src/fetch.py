"""Layer 1 — raw data collection. Everything lands in data/raw/ as Parquet.

    python -m src.fetch
"""
from __future__ import annotations

import io
import zipfile

import pandas as pd
import requests

from src import config

CVM_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{year}.zip"
SGS_URL = ("https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
           "?formato=json&dataInicial=01/01/{ini}&dataFinal=31/12/{fim}")
STATEMENTS = ["DRE", "BPP", "DFC_MI", "DMPL"]  # income, liabilities+equity, cash flow, equity changes


def _cvm_zip(year: int) -> zipfile.ZipFile | None:
    try:
        r = requests.get(CVM_URL.format(year=year), timeout=120)
        r.raise_for_status()
        return zipfile.ZipFile(io.BytesIO(r.content))
    except Exception as exc:  # noqa: BLE001
        print(f"  [WARN] DFP {year} unavailable: {exc}")
        return None


def _read_statement(zf: zipfile.ZipFile, stmt: str) -> pd.DataFrame:
    """Consolidated file for a statement (e.g. dfp_cia_aberta_DRE_con_2023.csv)."""
    names = [n for n in zf.namelist() if f"_{stmt}_con_" in n]
    if not names:
        return pd.DataFrame()
    return pd.read_csv(zf.open(names[0]), sep=";", encoding="latin1", dtype={"CD_CONTA": str})


def fetch_cvm(years=None) -> None:
    years = years or range(config.START_YEAR, config.END_YEAR + 1)
    cnpjs = {b["cnpj"] for b in config.BANKS}
    out = config.DATA_RAW / "cvm"
    out.mkdir(parents=True, exist_ok=True)
    for year in years:
        print(f"[CVM] DFP {year}")
        zf = _cvm_zip(year)
        if zf is None:
            continue
        for stmt in STATEMENTS:
            df = _read_statement(zf, stmt)
            if df.empty:
                print(f"  [WARN] {stmt} {year}: file not found")
                continue
            df = df[df["CNPJ_CIA"].isin(cnpjs)]
            df.to_parquet(out / f"{stmt}_{year}.parquet", index=False)
            print(f"  {stmt}: {len(df):>6} rows | banks: {df['CNPJ_CIA'].nunique()}")


def fetch_sgs(serie: int, name: str) -> None:
    rows = []
    for ini in range(config.START_YEAR, config.END_YEAR + 1, 10):  # API limit ~10y/request
        fim = min(ini + 9, config.END_YEAR)
        r = requests.get(SGS_URL.format(serie=serie, ini=ini, fim=fim), timeout=60)
        r.raise_for_status()
        rows.extend(r.json())
    df = pd.DataFrame(rows)
    df["data"] = pd.to_datetime(df["data"], dayfirst=True)
    df["valor"] = pd.to_numeric(df["valor"])
    (config.DATA_RAW / "bcb").mkdir(parents=True, exist_ok=True)
    df.to_parquet(config.DATA_RAW / "bcb" / f"{name}.parquet", index=False)
    print(f"[BCB] {name}: {len(df)} obs")


def fetch_prices() -> None:
    import yfinance as yf

    tickers = [b["ticker"] for b in config.BANKS] + [config.MARKET_INDEX]
    px = yf.download(tickers, start=f"{config.START_YEAR - 5}-01-01",
                     end=f"{config.END_YEAR + 1}-01-01", auto_adjust=False, progress=False)
    (config.DATA_RAW / "market").mkdir(parents=True, exist_ok=True)
    for field in ["Close", "Adj Close"]:
        px[field].to_parquet(config.DATA_RAW / "market" / f"{field.lower().replace(' ', '_')}.parquet")
    print(f"[YF] prices: {px.shape[0]} days, {len(tickers)} tickers")


def main() -> None:
    fetch_cvm()
    fetch_sgs(432, "selic_meta")
    fetch_sgs(433, "ipca_mensal")
    fetch_prices()


if __name__ == "__main__":
    main()
