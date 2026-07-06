import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.brightdata.com/datasets/v3"
CHANNEL_DATASET_ID = "gd_lk56epmy2i5g7lzu0k"


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _post(api_key: str, url: str, payload: list | dict) -> dict | None:
    response = requests.post(url, headers=_headers(api_key), json=payload, timeout=60)
    if not response.ok:
        print(f"Error: {response.status_code} {response.text}")
        return None
    return response.json()


def _get(api_key: str, url: str) -> dict | str | None:
    response = requests.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=60)
    if not response.ok:
        print(f"Error: {response.status_code} {response.text}")
        return None
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def trigger_scraping_niche(
    api_key: str,
    keyword: str,
    num_of_posts: int,
    start_date: str,
    end_date: str,
    country: str,
    endpoint: str,
) -> dict | None:
    payload = [{
        "keyword": keyword,
        "num_of_posts": num_of_posts,
        "start_date": start_date,
        "end_date": end_date,
        "country": country,
    }]
    return _post(api_key, endpoint, payload)


def trigger_scraping_channels(
    api_key: str,
    channel_urls: list[str],
    num_of_posts: int,
    start_date: str,
    end_date: str,
    order_by: str,
    country: str,
) -> dict | None:
    endpoint = (
        f"{BASE_URL}/trigger"
        f"?dataset_id={CHANNEL_DATASET_ID}&include_errors=true&type=discover_new&discover_by=url"
    )
    payload = [
        {
            "url": url,
            "num_of_posts": num_of_posts,
            "start_date": start_date,
            "end_date": end_date,
            "order_by": order_by,
            "country": country,
        }
        for url in channel_urls
    ]
    return _post(api_key, endpoint, payload)


def get_progress(api_key: str, snapshot_id: str) -> dict | None:
    return _get(api_key, f"{BASE_URL}/progress/{snapshot_id}")


def get_output(api_key: str, snapshot_id: str, format: str = "json") -> list:
    data = _get(api_key, f"{BASE_URL}/snapshot/{snapshot_id}?format={format}")
    if not data:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    if isinstance(data, str):
        return [json.loads(line) for line in data.strip().split("\n") if line.strip()]
    return []


def normalize_videos(scraped: list) -> list:
    if not scraped:
        return []
    if isinstance(scraped[0], dict):
        return scraped
    if isinstance(scraped[0], list):
        return scraped[0]
    return scraped


def wait_for_snapshot(api_key: str, snapshot_id: str, poll_seconds: int = 10, timeout_seconds: int = 600) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        status = get_progress(api_key, snapshot_id)
        if not status:
            raise RuntimeError("Failed to check scraping progress.")
        if status.get("status") in {"ready", "failed"}:
            return status
        time.sleep(poll_seconds)
    raise TimeoutError(f"Scraping timed out after {timeout_seconds}s.")
