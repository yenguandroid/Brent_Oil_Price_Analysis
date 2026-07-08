# Change Point Analysis and Statistical Modeling of Time Series Data

Analysis of Brent crude oil prices to detect structural breaks (change points) and
associate them with major geopolitical, OPEC, and macroeconomic events.

## Project Status

- [x] **Task 1 — Foundations:** analysis workflow, compiled event dataset, assumptions
      and limitations, and initial EDA (trend, stationarity, volatility).
- [ ] **Task 2 — Change point modeling:** Bayesian change point detection (PyMC).
- [ ] **Task 3 — Communication:** dashboard / stakeholder-facing report.

## Project Structure

```
├── .vscode/               # Editor settings (Python path, pytest integration)
├── .github/workflows/     # CI: runs the test suite on push/PR
├── data/
│   └── raw/
│       ├── BrentOilPrices.csv        # Daily Brent price series (Date, Price)
│       └── brent_oil_key_events.csv  # 17 compiled market events (Task 1 deliverable)
├── src/                   # Reusable, unit-tested analysis code
│   ├── data_loader.py     # Loading/cleaning price & event data
│   └── eda.py             # Stationarity tests, volatility, descriptive stats
├── notebooks/
│   └── task1_eda.ipynb    # Task 1 initial EDA notebook
├── scripts/                # One-off / helper scripts (not part of the core package)
├── tests/
│   └── test_task1_eda.py  # Unit tests for src/
├── requirements.txt
└── README.md
```

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Open the folder in VS Code (the included `.vscode/settings.json` configures the
Python path and pytest integration), then open `notebooks/task1_eda.ipynb` and
run all cells — or from the command line:

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/task1_eda.ipynb
```

Run the test suite:

```bash
pytest tests/ -v
```

## Data

`data/raw/BrentOilPrices.csv` currently contains the real, public daily Brent spot
price series (US EIA, via FRED series `DCOILBRENTEU`, sourced from
[github.com/datasets/oil-prices](https://github.com/datasets/oil-prices)),
covering 1987-05-20 onward. If your course/project provides an official dataset
file, replace this file with it — as long as it has `Date` and `Price` columns,
no code changes are needed.

## Task 1 Summary

See the accompanying report (`Task1_Foundation_Analysis.docx`) for the full
write-up. Headline EDA findings, reproduced in `notebooks/task1_eda.ipynb`:

- **Trend:** Brent prices move through distinct multi-year regimes (1990s stability,
  2008 spike/collapse, 2014-16 decline, 2020 COVID-19 crash, 2022 spike) rather than
  one smooth trend — motivating a change point approach.
- **Stationarity:** ADF and KPSS both indicate the raw price level is non-stationary,
  while log returns are approximately stationary. Modeling should operate on returns.
- **Volatility:** Returns show volatility clustering and heavy tails (high kurtosis,
  negative skew) — variance is not constant over time.
- **Events:** compiled a 17-event dataset (1990-2022) spanning geopolitical conflicts,
  OPEC decisions, economic shocks, and sanctions, for later cross-referencing against
  detected change points.

**Important caveat:** any alignment between a detected change point and a compiled
event date indicates temporal correlation, not proven causation — see the
assumptions/limitations section of the Task 1 report for details.
