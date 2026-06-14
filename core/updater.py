from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Optional

from core.constants import APP_VERSION


REPO_OWNER = "dabstebplay2-jpg"
REPO_NAME = "Nexus_mincraft_laucher"
LATEST_RELEASE_API = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
LATEST_RELEASE_PAGE = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/latest"


@dataclass
class ReleaseInfo:
    version: str
    tag: str
    name: str
    page_url: str
    download_url: str | None
    asset_name: str | None
    published_at: str | None
    is_newer: bool


def normalize_version(value: str) -> tuple[int, ...]:
    value = (value or "").strip().lower()
    value = value.removeprefix("v")
    parts = re.findall(r"\d+", value)
    return tuple(int(part) for part in parts) if parts else (0,)


def is_newer_version(remote: str, local: str) -> bool:
    return normalize_version(remote) > normalize_version(local)


def fetch_latest_release(timeout: int = 8) -> Optional[ReleaseInfo]:
    request = urllib.request.Request(
        LATEST_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"NexusLauncher/{APP_VERSION}",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    tag = data.get("tag_name") or ""
    version = tag.removeprefix("v")
    assets = data.get("assets") or []

    preferred_asset = None

    for asset in assets:
        name = asset.get("name", "").lower()
        if name.endswith(".exe") or name.endswith(".zip"):
            preferred_asset = asset
            break

    download_url = None
    asset_name = None

    if preferred_asset:
        download_url = preferred_asset.get("browser_download_url")
        asset_name = preferred_asset.get("name")

    return ReleaseInfo(
        version=version,
        tag=tag,
        name=data.get("name") or tag,
        page_url=data.get("html_url") or LATEST_RELEASE_PAGE,
        download_url=download_url,
        asset_name=asset_name,
        published_at=data.get("published_at"),
        is_newer=is_newer_version(version, APP_VERSION),
    )


def get_latest_download_url() -> str:
    release = fetch_latest_release()

    if release and release.download_url:
        return release.download_url

    return LATEST_RELEASE_PAGE
