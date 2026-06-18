from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
import urllib.request
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.app_info import (
    APP_VERSION,
    GITHUB_LATEST_RELEASE_API,
    GITHUB_LATEST_RELEASE_PAGE,
    GITHUB_OWNER,
    GITHUB_REPO,
    USER_AGENT,
)
from storage.paths import DATA_DIR


logger = logging.getLogger(__name__)

RETRY_ATTEMPTS = 3
RETRY_DELAY = 1.5
UPDATES_DIR = DATA_DIR / "updates"


@dataclass
class ReleaseAsset:
    name: str
    download_url: str
    size: int | None = None
    content_type: str | None = None


@dataclass
class ReleaseInfo:
    version: str
    tag: str
    name: str
    body: str
    page_url: str
    published_at: str | None
    assets: list[ReleaseAsset]
    preferred_asset: ReleaseAsset | None
    is_newer: bool
    repo: str


def normalize_version(value: str) -> tuple[int, ...]:
    value = (value or "").strip().lower()
    value = value.removeprefix("v")
    parts = re.findall(r"\d+", value)
    return tuple(int(part) for part in parts) if parts else (0,)


def is_newer_version(remote: str, local: str) -> bool:
    return normalize_version(remote) > normalize_version(local)


def repo_is_configured() -> bool:
    return bool(GITHUB_OWNER and GITHUB_REPO and "YOUR_GITHUB_USERNAME" not in GITHUB_OWNER)


def fetch_latest_release(timeout: int = 10) -> Optional[ReleaseInfo]:
    if not repo_is_configured():
        logger.warning("GitHub repo is not configured: %s/%s", GITHUB_OWNER, GITHUB_REPO)
        return None

    last_error = None

    for attempt in range(RETRY_ATTEMPTS):
        try:
            request = urllib.request.Request(
                GITHUB_LATEST_RELEASE_API,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": USER_AGENT,
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))

            tag = data.get("tag_name") or ""
            version = tag.removeprefix("v")
            assets = []

            for asset in data.get("assets") or []:
                url = asset.get("browser_download_url")
                name = asset.get("name")
                if not url or not name:
                    continue

                assets.append(
                    ReleaseAsset(
                        name=name,
                        download_url=url,
                        size=asset.get("size"),
                        content_type=asset.get("content_type"),
                    )
                )

            preferred_asset = choose_preferred_asset(assets)

            return ReleaseInfo(
                version=version,
                tag=tag,
                name=data.get("name") or tag,
                body=data.get("body") or "",
                page_url=data.get("html_url") or GITHUB_LATEST_RELEASE_PAGE,
                published_at=data.get("published_at"),
                assets=assets,
                preferred_asset=preferred_asset,
                is_newer=is_newer_version(version, APP_VERSION),
                repo=f"{GITHUB_OWNER}/{GITHUB_REPO}",
            )

        except Exception as error:
            last_error = error
            logger.warning("Updater attempt %d/%d failed: %s", attempt + 1, RETRY_ATTEMPTS, error)
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))

    logger.error("All updater attempts failed: %s", last_error)
    return None


def choose_preferred_asset(assets: list[ReleaseAsset]) -> ReleaseAsset | None:
    if not assets:
        return None

    def score(asset: ReleaseAsset):
        name = asset.name.lower()
        value = 0

        if name.endswith(".exe"):
            value += 100
        if "setup" in name or "installer" in name:
            value += 80
        if "portable" in name and name.endswith(".zip"):
            value += 50
        if "win" in name or "windows" in name:
            value += 25
        if "x64" in name or "amd64" in name:
            value += 15
        if name.endswith(".sha256"):
            value -= 1000

        return value

    return sorted(assets, key=score, reverse=True)[0]


def download_asset(asset: ReleaseAsset, progress_callback=None) -> Path:
    progress_callback = progress_callback or (lambda downloaded, total, speed: None)
    UPDATES_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = re.sub(r"[^a-zA-Z0-9_.()\\- ]+", "_", asset.name)
    target = UPDATES_DIR / safe_name
    tmp = target.with_suffix(target.suffix + ".tmp")

    request = urllib.request.Request(asset.download_url, headers={"User-Agent": USER_AGENT})

    with urllib.request.urlopen(request, timeout=30) as response:
        total = int(response.headers.get("content-length") or asset.size or 0)
        downloaded = 0
        started = time.time()

        with open(tmp, "wb") as output:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break

                output.write(chunk)
                downloaded += len(chunk)

                elapsed = max(time.time() - started, 0.001)
                speed = downloaded / elapsed
                progress_callback(downloaded, total, speed)

    if target.exists():
        target.unlink()
    tmp.replace(target)
    return target


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 256), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def open_release_page():
    webbrowser.open(GITHUB_LATEST_RELEASE_PAGE)


def open_downloaded_update(path: str | Path):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(str(path))

    if os.name == "nt":
        os.startfile(str(path))  # noqa: S606
        return

    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
        return

    subprocess.Popen(["xdg-open", str(path)])


def create_update_notes(release: ReleaseInfo, downloaded_path: Path) -> Path:
    notes = UPDATES_DIR / "latest_update.txt"
    notes.write_text(
        f"Nexus Launcher update downloaded\n\n"
        f"Repo: {release.repo}\n"
        f"Current version: {APP_VERSION}\n"
        f"Latest version: {release.version}\n"
        f"Asset: {downloaded_path.name}\n"
        f"SHA256: {sha256_file(downloaded_path)}\n\n"
        f"File path:\n{downloaded_path}\n\n"
        "If this is an installer .exe, close Nexus and run it.\n"
        "If this is portable .zip, extract it over the old portable folder.\n",
        encoding="utf-8",
    )
    return notes
