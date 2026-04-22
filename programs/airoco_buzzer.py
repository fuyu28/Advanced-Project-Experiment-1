#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "RPi.GPIO",
# ]
# ///

import os
import time
from pathlib import Path
from typing import Any

import requests
import RPi.GPIO as GPIO


ENV_PATH = Path(__file__).with_name(".env")
API_URL = "https://airoco.necolico.jp/data-api/latest"
DEFAULT_BUZZER_PIN = 18
DEFAULT_CO2_THRESHOLD = 1000.0
DEFAULT_POLL_INTERVAL = 5.0
DEFAULT_SENSOR_INDEX = 0


def load_env(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f".env ファイルが見つかりません: {path}")

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        os.environ[key.strip()] = value.strip().strip("\"'")


def getenv_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def getenv_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def getenv_gpio_state(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default

    normalized = value.strip().upper()
    if normalized == "HIGH":
        return GPIO.HIGH
    if normalized == "LOW":
        return GPIO.LOW

    raise ValueError(f"{name} には HIGH または LOW を指定してください: {value}")


def fetch_latest_data(subscription_key: str, id_hash_key: str) -> list[dict[str, Any]]:
    response = requests.get(
        API_URL,
        params={
            "id": id_hash_key,
            "subscription-key": subscription_key,
        },
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, list):
        raise ValueError("AirocO API のレスポンスが配列ではありません")

    return data


def select_sensor(sensors: list[dict[str, Any]]) -> dict[str, Any]:
    sensor_name = os.getenv("SENSOR_NAME")
    if sensor_name:
        for sensor in sensors:
            if str(sensor.get("name", "")).strip() == sensor_name:
                return sensor
        raise ValueError(f"指定した SENSOR_NAME のセンサが見つかりません: {sensor_name}")

    sensor_index = getenv_int("SENSOR_INDEX", DEFAULT_SENSOR_INDEX)
    if sensor_index < 0 or sensor_index >= len(sensors):
        raise IndexError(
            f"SENSOR_INDEX={sensor_index} は範囲外です。取得件数: {len(sensors)}"
        )
    return sensors[sensor_index]


def main() -> None:
    load_env(ENV_PATH)

    subscription_key = os.environ["SUBSCRIPTION_KEY"]
    id_hash_key = os.environ["ID_HASH_KEY"]
    buzzer_pin = getenv_int("BUZZER_PIN", DEFAULT_BUZZER_PIN)
    co2_threshold = getenv_float("CO2_THRESHOLD", DEFAULT_CO2_THRESHOLD)
    poll_interval = getenv_float("POLL_INTERVAL_SECONDS", DEFAULT_POLL_INTERVAL)
    buzzer_active_state = getenv_gpio_state("BUZZER_ACTIVE_STATE", GPIO.HIGH)
    buzzer_inactive_state = GPIO.LOW if buzzer_active_state == GPIO.HIGH else GPIO.HIGH

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(buzzer_pin, GPIO.OUT, initial=buzzer_inactive_state)

    print(
        "AirocO CO2 監視を開始します: "
        f"pin={buzzer_pin}, threshold={co2_threshold}ppm, interval={poll_interval}s"
    )

    try:
        while True:
            sensors = fetch_latest_data(subscription_key, id_hash_key)
            if not sensors:
                raise ValueError("AirocO API からセンサ情報を取得できませんでした")

            sensor = select_sensor(sensors)
            sensor_label = str(sensor.get("name") or sensor.get("devName") or "unknown")
            co2 = float(sensor["co2"])

            if co2 >= co2_threshold:
                GPIO.output(buzzer_pin, buzzer_active_state)
                status = "ブザーON"
            else:
                GPIO.output(buzzer_pin, buzzer_inactive_state)
                status = "ブザーOFF"

            print(f"{sensor_label}: CO2={co2:.1f}ppm / threshold={co2_threshold:.1f}ppm / {status}")
            time.sleep(poll_interval)
    finally:
        GPIO.output(buzzer_pin, buzzer_inactive_state)
        GPIO.cleanup()


if __name__ == "__main__":
    main()
