import json
import time

import requests

BASE_URL = "https://api.brightdata.com/datasets/v3"
CHANNEL_DATASET_ID = "gd_lk56epmy2i5g7lzu0k"

DEFAULT_TIMEOUT = 120
SNAPSHOT_TIMEOUT = 600
RETRYABLE_STATUS = {502, 503, 504}


class BrightDataError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _request(method: str, url: str, api_key: str, timeout: int, retries: int, **kwargs):
    last_error = None
    last_status = None
    last_body = ""

    for attempt in range(retries):
        try:
            response = requests.request(
                method,
                url,
                headers=_headers(api_key),
                timeout=(30, timeout),
                **kwargs,
            )
            last_status = response.status_code
            last_body = response.text[:500]

            if response.status_code in RETRYABLE_STATUS and attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
                continue

            if not response.ok:
                raise BrightDataError(
                    f"Bright Data API error ({response.status_code}): {response.text[:300]}",
                    response.status_code,
                )

            content_type = response.headers.get("content-type", "")
            if content_type.startswith("application/json"):
                return response.json()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))

    if last_error:
        raise last_error
    raise BrightDataError(
        f"Bright Data API error ({last_status}): {last_body or 'Unknown error'}",
        last_status,
    )


def _post(api_key: str, url: str, payload: list | dict, retries: int = 5) -> dict:
    return _request("POST", url, api_key, DEFAULT_TIMEOUT, retries, json=payload)


def _get(api_key: str, url: str, timeout: int = DEFAULT_TIMEOUT, retries: int = 3):
    return _request("GET", url, api_key, timeout, retries)


def trigger_scraping_niche(
    api_key: str,
    keyword: str,
    num_of_posts: int,
    start_date: str,
    end_date: str,
    country: str,
    endpoint: str,
) -> dict:
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
) -> dict:
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


def get_progress(api_key: str, snapshot_id: str) -> dict:
    return _get(api_key, f"{BASE_URL}/progress/{snapshot_id}", retries=5)


def get_output(api_key: str, snapshot_id: str, format: str = "json") -> list:
    data = _get(
        api_key,
        f"{BASE_URL}/snapshot/{snapshot_id}?format={format}",
        timeout=SNAPSHOT_TIMEOUT,
        retries=5,
    )
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


def wait_for_snapshot(
    api_key: str,
    snapshot_id: str,
    poll_seconds: int = 15,
    timeout_seconds: int = 1800,
) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            status = get_progress(api_key, snapshot_id)
        except (requests.RequestException, BrightDataError):
            time.sleep(poll_seconds)
            continue
        if not status:
            time.sleep(poll_seconds)
            continue
        if status.get("status") in {"ready", "failed"}:
            return status
        time.sleep(poll_seconds)
    raise TimeoutError(f"Scraping timed out after {timeout_seconds}s.")
