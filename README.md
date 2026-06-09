# NXP Life Expectancy Dashboard

Python dashboard for analyzing World Bank life expectancy, fertility, and death-rate indicators.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the pipeline

Build the master dataset from World Bank CSV files:

```bash
python preprocessing.py
```

## Run the analysis

Run statistical analysis on the master dataset:

```bash
python analysis.py
```

This exports results to `analysis_results.csv`, covering:

1. Income-group change in male–female life expectancy gap (1960 vs 2023)
2. Income-group change in life expectancy variability (1960 vs 2023)
3. Per-country Pearson correlation between fertility rate and life expectancy

## Project files

| File | Description |
|------|-------------|
| `data_loader.py` | Download and load World Bank WDI datasets |
| `preprocessing.py` | Wide-to-long transformation and master dataset merge |
| `master_dataset.csv` | Merged country-year dataset |
| `analysis.py` | Statistical analysis functions and pipeline |
| `analysis_results.csv` | Exported analysis output |

## Data sources

- [Life expectancy at birth, total](https://data.worldbank.org/indicator/SP.DYN.LE00.IN)
- [Life expectancy at birth, male](https://data.worldbank.org/indicator/SP.DYN.LE00.MA.IN)
- [Life expectancy at birth, female](https://data.worldbank.org/indicator/SP.DYN.LE00.FE.IN)
- [Fertility rate, total](https://data.worldbank.org/indicator/SP.DYN.TFRT.IN)
- [Death rate, crude](https://data.worldbank.org/indicator/SP.DYN.CDRT.IN)
