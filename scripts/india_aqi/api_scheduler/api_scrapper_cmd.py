"""Fetch and reshape CPCB-backed air-quality observations from data.gov.in."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests


RESOURCE_ID = "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"
POLLUTANT_COLUMNS = ["PM2.5", "PM10", "NO2", "NH3", "SO2", "CO", "O3"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a station-level India AQI snapshot."
    )
    parser.add_argument(
        "--file_path",
        type=Path,
        required=True,
        help="Directory in which date-partitioned CSV snapshots are written.",
    )
    parser.add_argument("--limit", type=int, default=4000)
    return parser.parse_args()


def fetch_records(api_key: str, limit: int) -> list[dict]:
    url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
    response = requests.get(
        url,
        params={"api-key": api_key, "format": "json", "limit": limit},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("API response did not contain a records list")
    return records


def transform_records(records: list[dict], mapping_path: Path) -> pd.DataFrame:
    frame = pd.json_normalize(records)
    required = {"city", "station", "state", "last_update", "pollutant_id", "pollutant_avg"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"API response is missing required fields: {sorted(missing)}")

    frame["pollutant_avg"] = pd.to_numeric(
        frame["pollutant_avg"].replace("NA", np.nan), errors="coerce"
    )
    frame["pollutant_id"] = frame["pollutant_id"].replace("OZONE", "O3")

    output = frame.pivot_table(
        index=["city", "station", "state", "last_update"],
        columns="pollutant_id",
        values="pollutant_avg",
        aggfunc="first",
    ).reset_index()
    output = output.reindex(
        columns=["city", "station", "state", *POLLUTANT_COLUMNS, "last_update"]
    )
    output["last_update"] = pd.to_datetime(
        output["last_update"], format="%d-%m-%Y %H:%M:%S", errors="raise"
    ).dt.strftime("%Y-%m-%dT%H:%M:%S")
    output = output.rename(columns={"PM2.5": "PM25", "last_update": "Date"})

    with mapping_path.open(encoding="utf-8") as stream:
        station_to_dcid = json.load(stream)
    output["dcid"] = output["station"].map(station_to_dcid)
    return output.dropna(subset=["dcid"])


def main() -> None:
    args = parse_args()
    api_key = os.environ.get("DATA_GOV_IN_API_KEY")
    if not api_key:
        raise SystemExit("Set DATA_GOV_IN_API_KEY before running the pipeline")

    script_dir = Path(__file__).resolve().parent
    records = fetch_records(api_key, args.limit)
    output = transform_records(records, script_dir / "dcid_output.json")

    now = datetime.now()
    destination = args.file_path / now.strftime("%Y-%m-%d")
    destination.mkdir(parents=True, exist_ok=True)
    output_path = destination / f"{now:%Y-%m-%d-%H-%M-%S}.csv"
    output.to_csv(output_path, index=False)
    print(f"Wrote {len(output):,} mapped station rows to {output_path}")


if __name__ == "__main__":
    main()
