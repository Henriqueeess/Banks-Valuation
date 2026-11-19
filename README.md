# Valuation dos Bancos Brasileiros — Modelo de Excess Return (v2, em desenvolvimento)

> **Não é recomendação de investimento.** Projeto acadêmico e de portfólio.
> *A versão em inglês deste README será publicada ao final do projeto.*

Valuation dos quatro maiores bancos listados do Brasil — Itaú Unibanco (ITUB4), Bradesco (BBDC4), Banco do Brasil (BBAS3) e Santander Brasil (SANB11) — no período de 2010 a 2025.

## Problema
Um ROE alto não torna um banco caro ou barato; o que importa é o spread sobre o custo de capital próprio. A versão 1 media o spread histórico ROE − Ke. A versão 2 transforma isso em um valuation completo: valor intrínseco por ação × preço de mercado, P/VP justificado × P/VP de mercado, cenários e sensibilidade.

## Por que não DCF?
Em bancos, a dívida é insumo operacional, o capital regulatório limita o reinvestimento e o fluxo de caixa livre é difícil de definir. Modelos baseados no patrimônio (Excess Return / Residual Income) são o padrão para instituições financeiras.

## Dados
| Dado | Fonte |
|---|---|
| Lucro líquido e PL (DFP) | CVM Dados Abertos |
| Selic e IPCA | BCB SGS (séries 432 e 433) |
| Preços e IBOV | Yahoo Finance (`yfinance`) |
| ERP, risco-país e betas setoriais | Damodaran *(semana 3)* |
| Margem financeira, PDD e carteira | BCB IF.data *(semana 6)* |

## Metodologia
- **ROE** = lucro líquido atribuído aos controladores / PL do controlador no início do ano.
- **Ke (CAPM, ex-ante)** = Rf + β × ERP. β por regressão de retornos semanais contra o IBOV (janela de 5 anos, ajuste de Blume). As premissas em `src/config.py` são **provisórias** até a semana 3.
- **Modelo de Excess Return, P/VP justificado, cenários e decomposição do ROE** — em construção (ver roteiro).

## Estrutura do projeto
```
src/
  config.py      bancos, período, caminhos e premissas
  fetch.py       dados brutos -> data/raw/*.parquet
  transform.py   limpeza CVM -> data/processed/fundamentals.parquet
  model.py       beta, Ke, spread -> data/processed/ke_spread.parquet
  report.py      gráficos e tabelas -> outputs/
  diagnose.py    diagnóstico de cobertura dos dados
tests/           pytest
legacy/          script da v1 (mantido como referência)
```

## Como rodar
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py              # fetch -> transform -> model -> report
python -m src.diagnose     # cobertura ano × banco
pytest
```

## Roteiro
- [x] Reestruturação do repositório, camadas em Parquet e testes
- [x] Correção: dupla contagem do lucro; Ke calculado com o retorno realizado do IBOV
- [x] Correção: Bradesco/BB/Santander sem dados após 2019 (o PL passou da conta 2.08 para a 2.07 em 2020)
- [ ] Ke com fontes documentadas (NTN-B / Damodaran) e comparação de betas
- [ ] Valuation por Excess Return, valor por ação e upside/downside
- [ ] P/VP justificado × de mercado, cenários e sensibilidade Ke × g
- [ ] Decomposição do ROE (DuPont, IF.data)

## Limitações
Betas de bancos são instáveis (controle estatal no BB, crise do Bradesco em 2023); o valuation é muito sensível a Ke − g; há diferenças entre COSIF e IFRS e entre ROE recorrente e contábil.
