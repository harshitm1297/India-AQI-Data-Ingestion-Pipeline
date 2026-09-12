# India AQI Data Ingestion Pipeline

A focused extraction of the India AQI refresh work originally developed as an
extension to the Google Data Commons data-import repository. The pipeline reads
hourly station-level observations from India's CPCB-backed Open Government Data
API, reshapes pollutant records, maps monitoring stations to Data Commons IDs,
and writes timestamped CSV snapshots.

## Features

- Processes PM2.5, PM10, NO2, NH3, SO2, CO, and O3 observations.
- Normalizes nested API JSON into station-level rows.
- Converts unavailable measurements to missing values.
- Maps station labels to Data Commons identifiers.
- Writes snapshots to date-partitioned output directories.
- Reads the API key from the environment rather than source control.

## Run

Install the dependencies, set a data.gov.in API key, and choose an output
directory:

```powershell
python -m pip install -r requirements.txt
$env:DATA_GOV_IN_API_KEY = "your-api-key"
python scripts/india_aqi/api_scheduler/api_scrapper_cmd.py --file_path output
```

The command creates a directory named with the current date and writes a
timestamped CSV snapshot inside it.

## Scope and limitations

This repository demonstrates data ingestion and transformation. It does not
calculate AQI, train a forecasting model, or prove that the command was deployed
as a production scheduler. The request remains capped at 4,000 API records and
does not yet implement pagination.

The station mapping includes unresolved entries represented by JSON `null`.
Rows without a resolved Data Commons identifier are excluded from the exported
snapshot.

## Provenance

The work originated on the `aqi_refresh` branch of
`ANJALI1928/AQI-DATA`, a fork of the Google Data Commons data repository. The
focused portfolio repository retains only the project-specific ingestion files
instead of republishing the full upstream Data Commons codebase.

Data source: https://www.data.gov.in/resource/real-time-air-quality-index-various-locations
