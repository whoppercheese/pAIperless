#requirements:
#httpx==0.27.2

import os

import httpx


def _headers() -> dict:
    return {"Authorization": f"Token {os.environ['PAPERLESS_API_TOKEN']}"}


def _base_url() -> str:
    return os.environ["PAPERLESS_URL"].rstrip("/")


def get(path: str, params: dict | None = None) -> dict:
    with httpx.Client(timeout=120.0) as client:
        r = client.get(f"{_base_url()}{path}", headers=_headers(), params=params)
        r.raise_for_status()
        return r.json()


def post(path: str, payload: dict) -> dict:
    with httpx.Client(timeout=120.0) as client:
        r = client.post(f"{_base_url()}{path}", headers=_headers(), json=payload)
        r.raise_for_status()
        return r.json()


def patch(path: str, payload: dict) -> dict:
    with httpx.Client(timeout=120.0) as client:
        r = client.patch(f"{_base_url()}{path}", headers=_headers(), json=payload)
        r.raise_for_status()
        return r.json()


def paginate(path: str) -> list[dict]:
    results: list[dict] = []
    page = 1
    while True:
        data = get(path, params={"page": page, "page_size": 100})
        results.extend(data.get("results", []))
        if not data.get("next"):
            break
        page += 1
    return results
