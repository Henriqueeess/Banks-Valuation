"""Layer 4 — figures and tables in outputs/.

    python -m src.report
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src import config  # noqa: E402


def plot_spread(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    for bank, g in df.groupby("bank"):
        ax.plot(g["year"], g["spread"], marker="o", label=bank)
    ax.axhline(0, color="grey", lw=0.8)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_title("ROE − Ke spread (provisional Ke)")
    ax.legend(frameon=False)
    fig.tight_layout()
    config.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(config.FIGURES / "spread_roe_ke.png", dpi=150)


def main() -> None:
    df = pd.read_parquet(config.DATA_PROCESSED / "ke_spread.parquet")
    plot_spread(df)
    df.to_csv(config.OUTPUTS / "ke_spread.csv", index=False)
    print(f"[OK] outputs written to {config.OUTPUTS}")


if __name__ == "__main__":
    main()
