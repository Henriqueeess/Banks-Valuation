import numpy as np
import pandas as pd
import pytest

from src.model import blume, capm, ols_beta
from src.transform import compute_roe, extract_equity, extract_net_income


def _row(cnpj, year, code, desc, value, ordem="ÚLTIMO"):
    return {"CNPJ_CIA": cnpj, "DT_REFER": f"{year}-12-31", "ORDEM_EXERC": ordem,
            "ESCALA_MOEDA": "MIL", "CD_CONTA": code, "DS_CONTA": desc, "VL_CONTA": value}


def test_net_income_picks_single_controller_line():
    """Legacy bug: summing every 'Lucro/Prejuízo' line double-counted."""
    dre = pd.DataFrame([
        _row("X", 2024, "3.11", "Lucro ou Prejuízo Líquido Consolidado do Período", 110),
        _row("X", 2024, "3.11.01", "Atribuído a Sócios da Empresa Controladora", 100),
        _row("X", 2024, "3.11.02", "Atribuído a Sócios Não Controladores", 10),
        _row("X", 2024, "3.11", "Lucro ou Prejuízo Líquido Consolidado do Período", 999, ordem="PENÚLTIMO"),
    ])
    ni = extract_net_income(dre)
    assert len(ni) == 1
    assert ni.loc[0, "net_income"] == 100_000  # MIL -> R$


def test_net_income_fallback_to_consolidated():
    dre = pd.DataFrame([_row("X", 2015, "3.11", "Lucro ou Prejuízo Líquido Consolidado do Período", 50)])
    assert extract_net_income(dre).loc[0, "ni_source"] == "consolidated"


def test_equity_excludes_non_controlling():
    bpp = pd.DataFrame([
        _row("X", 2024, "2.08", "Patrimônio Líquido Consolidado", 1_000),
        _row("X", 2024, "2.08.09", "Participação dos Acionistas Não Controladores", 40),
    ])
    assert extract_equity(bpp).loc[0, "equity"] == 960_000


def test_roe_uses_beginning_equity():
    ni = pd.DataFrame({"cnpj": ["X", "X"], "year": [2023, 2024], "net_income": [15, 20]})
    eq = pd.DataFrame({"cnpj": ["X", "X"], "year": [2023, 2024], "equity": [100, 110]})
    roe = compute_roe(ni, eq).set_index("year")["roe"]
    assert np.isnan(roe[2023])
    assert roe[2024] == pytest.approx(20 / 100)


def test_beta_recovers_known_slope():
    rng = np.random.default_rng(0)
    m = pd.Series(rng.normal(0, 0.03, 260))
    s = 1.2 * m + pd.Series(rng.normal(0, 0.005, 260))
    assert ols_beta(s, m) == pytest.approx(1.2, abs=0.05)


def test_blume_and_capm_are_ex_ante_and_positive():
    assert blume(1.0) == pytest.approx(1.0)
    assert blume(1.5) == pytest.approx(1.335)
    ke = capm(blume(1.2), rf=0.13, erp=0.055)
    assert 0.13 < ke < 0.25  # legacy model produced Ke of -22% and +49%
