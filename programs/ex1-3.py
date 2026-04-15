#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "matplotlib",
#   "numpy",
#   "requests",
# ]
# ///

import csv
import datetime as dt
import os
import time
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import requests


SENSOR_NAME = "Ｒ３ーB１Ｆ_ＥＨ"
PLOT_TITLE = "R3-B1F_EH CO2 density for the past week"
OUTPUT_PATH = Path(__file__).with_name("ex1-3.png")
ENV_PATH = Path(__file__).with_name(".env")
API_URL = "https://airoco.necolico.jp/data-api/day-csv"
DAY_SECONDS = 3600 * 24
FETCH_DAYS = 7


def load_env(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f".env file was not found: {path}")

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        os.environ[key.strip()] = value.strip().strip("\"'")


def fetch_day_csv(
    subscription_key: str,
    id_hash_key: str,
    start_time: int,
) -> list[list[str]]:
    response = requests.get(
        API_URL,
        params={
            "id": id_hash_key,
            "subscription-key": subscription_key,
            "startDate": start_time,
        },
        timeout=30,
    )
    response.raise_for_status()
    return list(csv.reader(response.text.strip().splitlines()))


def main() -> None:
    load_env(ENV_PATH)

    subscription_key = os.environ["SUBSCRIPTION_KEY"]
    id_hash_key = os.environ["ID_HASH_KEY"]

    current_time = int(time.time())
    base_start_time = current_time - DAY_SECONDS * FETCH_DAYS

    sensor_data_by_timestamp: dict[int, tuple[float, float, float]] = {}
    for day_index in range(FETCH_DAYS):
        start_time = base_start_time + DAY_SECONDS * day_index
        raw_data = fetch_day_csv(subscription_key, id_hash_key, start_time)
        for row in raw_data:
            if len(row) < 7 or row[1] != SENSOR_NAME:
                continue

            timestamp = int(float(row[6]))
            sensor_data_by_timestamp[timestamp] = (
                float(row[3]),
                float(row[4]),
                float(row[5]),
            )

    data = [
        [co2, temperature, humidity, timestamp]
        for timestamp, (co2, temperature, humidity) in sorted(sensor_data_by_timestamp.items())
    ]

    if not data:
        print("This sensor is not connected")
        return

    values = np.array(data, dtype=float)
    timestamps = np.array(
        [dt.datetime.fromtimestamp(ts) for ts in values[:, 3]],
        dtype=object,
    )
    date_numbers = np.array(mdates.date2num(timestamps), dtype=float)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(date_numbers, values[:, 0], color="tab:blue")
    ax.set_title(PLOT_TITLE)
    ax.set_xlabel("Date")
    ax.set_ylabel("CO2 density [ppm]")
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H:%M"))
    fig.autofmt_xdate()
    plt.tight_layout()

    if matplotlib.get_backend().lower().endswith("agg"):
        fig.savefig(OUTPUT_PATH, dpi=150)
        print(f"Saved graph to {OUTPUT_PATH}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
