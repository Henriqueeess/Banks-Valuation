"""Diagnostic for the legacy bug: Bradesco, BB and Santander stopped in 2019.

Run AFTER `python -m src.fetch`. For each year and bank it prints how many
DRE/BPP rows exist, the ORDEM_EXERC values and the candidate net-income lines,
so we can see whether the gap comes from the CNPJ filter, the ORDEM_EXERC
filter or account-description changes.

    python -m src.diagnose
"""
import pandas as pd

from src import config
from src.transform import _load, _norm


def main() -> None:
    names = {b["cnpj"]: b["name"] for b in config.BANKS}
    for stmt in ["DRE", "BPP"]:
        df = _load(stmt)
        if df.empty:
            print(f"{stmt}: no raw data — run `python -m src.fetch` first")
            continue
        df["bank"] = df["CNPJ_CIA"].map(names)
        df["year"] = pd.to_datetime(df["DT_REFER"]).dt.year
        print(f"\n=== {stmt}: rows per year x bank ===")
        print(df.pivot_table(index="year", columns="bank", values="VL_CONTA", aggfunc="size").fillna(0).astype(int))
        print(f"\n=== {stmt}: ORDEM_EXERC values ===")
        print(df["ORDEM_EXERC"].value_counts())

    dre = _load("DRE")
    if not dre.empty:
        dre["bank"] = dre["CNPJ_CIA"].map(names)
        dre["year"] = pd.to_datetime(dre["DT_REFER"]).dt.year
        mask = _norm(dre["DS_CONTA"]).str.contains("LUCRO") & (_norm(dre["ORDEM_EXERC"]) == "ULTIMO")
        print("\n=== Net income candidate lines (legacy filter would SUM all of these) ===")
        cols = ["bank", "year", "CD_CONTA", "DS_CONTA", "VL_CONTA"]
        with pd.option_context("display.max_rows", 400, "display.width", 200):
            print(dre.loc[mask, cols].sort_values(["bank", "year", "CD_CONTA"]).to_string(index=False))


if __name__ == "__main__":
    main()
