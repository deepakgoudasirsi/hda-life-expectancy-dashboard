# NXP Life Expectancy Dashboard

Python dashboard for analyzing World Bank life expectancy, fertility, and death-rate indicators.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the pipeline

```bash
python preprocessing.py
```

## Data sources

- [Life expectancy at birth, total](https://data.worldbank.org/indicator/SP.DYN.LE00.IN)
- [Life expectancy at birth, male](https://data.worldbank.org/indicator/SP.DYN.LE00.MA.IN)
- [Life expectancy at birth, female](https://data.worldbank.org/indicator/SP.DYN.LE00.FE.IN)
- [Fertility rate, total](https://data.worldbank.org/indicator/SP.DYN.TFRT.IN)
- [Death rate, crude](https://data.worldbank.org/indicator/SP.DYN.CDRT.IN)
