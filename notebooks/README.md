# Notebooks

- `task1_eda.ipynb` — Task 1 initial exploratory data analysis: trend inspection,
  ADF/KPSS stationarity testing, volatility diagnostics, and an overlay of the
  compiled event dataset on the Brent price series. Uses functions from `src/`
  so the logic stays unit-tested and reusable.

Run `jupyter lab` (or open in VS Code) from the project root, or execute headlessly:

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/task1_eda.ipynb
```
