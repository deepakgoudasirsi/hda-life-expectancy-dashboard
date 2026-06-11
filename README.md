# NXP Life Expectancy Dashboard

Production-quality analytics pipeline and Streamlit dashboard for World Bank life
expectancy, fertility, and death-rate indicators.

## Features

- Automated WDI data ingestion and master dataset generation
- Statistical analysis for income-group gaps, variability, and correlations
- Static Plotly exports (trends, choropleth map, Sankey diagram)
- Interactive Streamlit dashboard with filters, KPIs, trends, comparisons, and data export

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Build the master dataset (uses cached CSVs in `data/raw/` when available):

```bash
python preprocessing.py
```

Launch the dashboard:

```bash
streamlit run dashboard/app.py
```

## Project structure

```
├── config.py                 # Shared constants and paths
├── data_loader.py            # World Bank WDI download and parsing
├── preprocessing.py          # ETL pipeline → master_dataset.csv
├── analysis.py               # Statistical analysis pipeline
├── visualizations.py         # Static Plotly visualizations
├── wb_metadata.py            # Cached World Bank country metadata client
├── dashboard/
│   ├── app.py                # Streamlit entry point
│   ├── styles.py             # CSS and layout configuration
│   ├── services/data_service.py
│   └── components/           # Charts, filters, KPIs, data table
├── data/raw/                 # Cached WDI CSV exports
├── data/cache/               # Cached World Bank metadata JSON
├── outputs/figures/          # HTML/PNG static visualizations
├── outputs/screenshots/      # Dashboard chart screenshots
├── docs/ARCHITECTURE.md      # System architecture documentation
└── scripts/export_assets.py  # Generate output assets
```

## Run the analysis

```bash
python analysis.py
```

Exports `analysis_results.csv` covering:

1. Income-group change in male–female life expectancy gap (1960 vs 2023)
2. Income-group change in life expectancy variability (1960 vs 2023)
3. Per-country Pearson correlation between fertility rate and life expectancy

## Generate output assets

Export static figures and dashboard screenshots:

```bash
python scripts/export_assets.py
```

## Dashboard sections

| Section | Description |
|---------|-------------|
| KPI cards | Life expectancy, fertility, death rate, male–female gap |
| Life expectancy trend | Country-level time series |
| Fertility / death rate trends | Side-by-side trend charts |
| Gender comparison | Male vs female life expectancy |
| Region / income comparisons | Aggregate bar charts |
| Data table | Filtered records with CSV download |

Sidebar filters: **Country**, **Income Group**, **Region**, **Year Range**

## Development

Lint with Ruff (PEP 8 compatible):

```bash
pip install ruff
ruff check .
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for layered design, caching,
error handling, and extension points.

## Data sources

- [Life expectancy at birth, total](https://data.worldbank.org/indicator/SP.DYN.LE00.IN)
- [Life expectancy at birth, male](https://data.worldbank.org/indicator/SP.DYN.LE00.MA.IN)
- [Life expectancy at birth, female](https://data.worldbank.org/indicator/SP.DYN.LE00.FE.IN)
- [Fertility rate, total](https://data.worldbank.org/indicator/SP.DYN.TFRT.IN)
- [Death rate, crude](https://data.worldbank.org/indicator/SP.DYN.CDRT.IN)

## License

Submitted as part of the NXP Life Expectancy Dashboard assignment.
