#!/usr/bin/env python3
"""Solax Cloud solar inverter data collector — writes to InfluxDB."""

import logging
import os
import time

import requests
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

load_dotenv()

# --- Configuration (from environment / .env) ---
SOLAX_URL = "https://global.solaxcloud.com/api/v2/dataAccess/realtimeInfo/get"
SOLAX_TOKEN = os.environ["SOLAX_TOKEN"]
SOLAX_WIFI_SN = os.environ["SOLAX_WIFI_SN"]
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))  # 5 min default

INFLUX_URL = os.environ["INFLUX_URL"]
INFLUX_TOKEN = os.environ["INFLUX_TOKEN"]
INFLUX_ORG = os.environ["INFLUX_ORG"]
INFLUX_BUCKET = os.environ["INFLUX_BUCKET"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def fetch_inverter_data() -> dict:
    """Call the Solax Cloud API and return the result dict."""
    resp = requests.post(
        SOLAX_URL,
        headers={"Content-Type": "application/json", "tokenId": SOLAX_TOKEN},
        json={"wifiSn": SOLAX_WIFI_SN},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        raise ValueError(f"API error: {payload.get('exception', 'unknown')}")
    return payload["result"]


def build_point(result: dict) -> Point:
    """Convert a Solax result dict into an InfluxDB Point.

    Uses the inverter's own utcDateTime as the point timestamp so that
    re-runs or retries don't create duplicate points at a different wall-clock time.
    Null fields are omitted rather than written as zero.
    """
    p = (
        Point("solar_inverter")
        .tag("inverter_sn", result.get("inverterSN", ""))
        .tag("wifi_sn", result.get("sn", ""))
        .tag("inverter_type", result.get("inverterType", ""))
        .tag("inverter_status", result.get("inverterStatus", ""))
    )

    numeric_fields = {
        "acpower_w": result.get("acpower"),
        "yield_today_kwh": result.get("yieldtoday"),
        "yield_total_kwh": result.get("yieldtotal"),
        "feedin_power_w": result.get("feedinpower"),
        "feedin_energy_kwh": result.get("feedinenergy"),
        "consume_energy_kwh": result.get("consumeenergy"),
        "feedin_power_m2_w": result.get("feedinpowerM2"),
        "soc_pct": result.get("soc"),
        "bat_power_w": result.get("batPower"),
        "powerdc1_w": result.get("powerdc1"),
        "powerdc2_w": result.get("powerdc2"),
        "powerdc3_w": result.get("powerdc3"),
        "powerdc4_w": result.get("powerdc4"),
        "peps1_w": result.get("peps1"),
        "peps2_w": result.get("peps2"),
        "peps3_w": result.get("peps3"),
    }

    for field, value in numeric_fields.items():
        if value is not None:
            p = p.field(field, float(value))

    utc = result.get("utcDateTime")  # e.g. "2026-02-19T12:39:41Z"
    if utc:
        p = p.time(utc, WritePrecision.S)

    return p


def run() -> None:
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    log.info("Solax collector started (wifi_sn=%s, interval=%ds)", SOLAX_WIFI_SN, POLL_INTERVAL)

    last_upload_time = None

    while True:
        try:
            result = fetch_inverter_data()

            upload_time = result.get("uploadTime")
            if upload_time == last_upload_time:
                log.debug("No new data yet (uploadTime=%s), skipping write", upload_time)
            else:
                point = build_point(result)
                write_api.write(bucket=INFLUX_BUCKET, record=point)
                last_upload_time = upload_time
                log.info(
                    "Wrote: acpower=%.1fW  yield_today=%.2fkWh  soc=%s  status=%s  ts=%s",
                    result.get("acpower") or 0,
                    result.get("yieldtoday") or 0,
                    result.get("soc"),
                    result.get("inverterStatus"),
                    upload_time,
                )
        except Exception as exc:
            log.error("Collection failed: %s", exc)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
