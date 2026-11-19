"""Layer 2 — clean raw CVM data into annual fundamentals per bank.

Output: data/processed/fundamentals.parquet
    bank, year, net_income (to controlling shareholders), equity (controlling),
    equity_begin, roe

    python -m src.transform
"""
from __future__ import annotations

import re
import unicodedata

import pandas as pd

from src import config


def _norm(s: pd.Series) -> pd.Series:
    """Upper-case, accent-free text (robust to latin1/utf-8 differences)."""
    return s.astype(str).map(
        lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().upper().strip()
    )


def _last_year_only(df: pd.DataFrame) -> pd.DataFrame:
    """Keep current-year figures (ORDEM_EXERC == 'ÚLTIMO') and scale to R$."""
    df = df[_norm(df["ORDEM_EXERC"]) == "ULTIMO"].copy()
    df["year"] = pd.to_datetime(df["DT_REFER"]).dt.year
    scale = _norm(df["ESCALA_MOEDA"]).map({"MIL": 1_000, "UNIDADE": 1}).fillna(1_000)
    df["value"] = df["VL_CONTA"] * scale
    return df


# Net income attributable to the controlling shareholders.
# Bank DRE layouts change code across years (3.09 / 3.11 / 3.13 ...), so we
# select by description but take ONE row: the attributable-to-parent line.
# Fallback: the consolidated net income line when no split is reported.
_RE_CONTROLLER = re.compile(r"ATRIBUIDO.*(?:SOCIOS|ACIONISTAS).*CONTROLADOR")
_RE_NET_INCOME = re.compile(r"^LUCRO.*(?:LIQUIDO|CONSOLIDADO).*PERIODO")


def extract_net_income(dre: pd.DataFrame) -> pd.DataFrame:
    df = _last_year_only(dre)
    df["desc"] = _norm(df["DS_CONTA"])
    df["level"] = df["CD_CONTA"].str.count(r"\.")

    out = []
    for (cnpj, year), g in df.groupby(["CNPJ_CIA", "year"]):
        ctrl = g[g["desc"].str.contains(_RE_CONTROLLER)]
        pick = ctrl if not ctrl.empty else g[g["desc"].str.contains(_RE_NET_INCOME)]
        if pick.empty:
            continue
        row = pick.sort_values(["level", "CD_CONTA"]).iloc[0]  # top-most matching line
        out.append({"cnpj": cnpj, "year": year, "net_income": row["value"],
                    "ni_account": row["CD_CONTA"], "ni_source": "controller" if not ctrl.empty else "consolidated"})
    return pd.DataFrame(out)


def extract_equity(bpp: pd.DataFrame) -> pd.DataFrame:
    """Controlling equity = total equity (2.08 / 2.07 ...) minus non-controlling interests."""
    df = _last_year_only(bpp)
    df["desc"] = _norm(df["DS_CONTA"])
    df["level"] = df["CD_CONTA"].str.count(r"\.")

    out = []
    for (cnpj, year), g in df.groupby(["CNPJ_CIA", "year"]):
        total = g[(g["level"] == 1) & g["desc"].str.contains("PATRIMONIO LIQUIDO")]
        if total.empty:
            continue
        total = total.iloc[0]
        nci = g[g["CD_CONTA"].str.startswith(total["CD_CONTA"] + ".")
                & g["desc"].str.contains("NAO CONTROLADOR")]
        nci_val = nci.sort_values("level")["value"].iloc[0] if not nci.empty else 0.0
        out.append({"cnpj": cnpj, "year": year, "equity": total["value"] - nci_val,
                    "eq_account": total["CD_CONTA"]})
    return pd.DataFrame(out)


def compute_roe(ni: pd.DataFrame, eq: pd.DataFrame) -> pd.DataFrame:
    """ROE_t = NI_t / Equity_{t-1} (beginning-of-year equity)."""
    df = ni.merge(eq, on=["cnpj", "year"], how="inner").sort_values(["cnpj", "year"])
    prev = eq.assign(year=eq["year"] + 1)[["cnpj", "year", "equity"]].rename(columns={"equity": "equity_begin"})
    df = df.merge(prev, on=["cnpj", "year"], how="left")
    df["roe"] = df["net_income"] / df["equity_begin"]
    return df


def _load(stmt: str) -> pd.DataFrame:
    files = sorted((config.DATA_RAW / "cvm").glob(f"{stmt}_*.parquet"))
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True) if files else pd.DataFrame()


def coverage_report(df: pd.DataFrame) -> pd.DataFrame:
    """Years x banks matrix — flags gaps (e.g. the old 'stops in 2019' bug)."""
    return df.pivot_table(index="year", columns="bank", values="roe", aggfunc="count").fillna(0).astype(int)


def main() -> None:
    names = {b["cnpj"]: b["name"] for b in config.BANKS}
    ni = extract_net_income(_load("DRE"))
    eq = extract_equity(_load("BPP"))
    df = compute_roe(ni, eq)
    df.insert(0, "bank", df["cnpj"].map(names))
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(config.DATA_PROCESSED / "fundamentals.parquet", index=False)
    print(coverage_report(df))
    print(df.pivot_table(index="year", columns="bank", values="roe").map("{:.1%}".format))


if __name__ == "__main__":
    main()
