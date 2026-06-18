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
    WEBSITE_RELEASE_JSON_URL,
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
    source: str = "github"


def normalize_version(value: str) -> tuple[int, ...]:
    value = (value or "").strip().lower()
    value = value.removeprefix("v")
    parts = re.findall(r"\d+", value)
    return tuple(int(part) for part in parts) if parts else (0,)


def is_newer_version(remote: str, local: str) -> bool:
    return normalize_version(remote) > normalize_version(local)


def repo_is_configured() -> bool:
    return bool(GITHUB_OWNER and GITHUB_REPO and "YOUR_GITHUB_USERNAME" not in GITHUB_OWNER)


def _request_json(url: str, timeout: int = 10, accept: str = "application/json") -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": USER_AGENT,
        },
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_github_latest_release(timeout: int = 10) -> Optional[ReleaseInfo]:
    if not repo_is_configured():
        logger.warning("GitHub repo is not configured: %s/%s", GITHUB_OWNER, GITHUB_REPO)
        return None

    last_error = None

    for attempt in range(RETRY_ATTEMPTS):
        try:
            data = _request_json(
                GITHUB_LATEST_RELEASE_API,
                timeout=timeout,
                accept="application/vnd.github+json",
            )

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
                tag=tag or f"v{version}",
                name=data.get("name") or tag or f"Nexus Launcher {version}",
                body=data.get("body") or "",
                page_url=data.get("html_url") or GITHUB_LATEST_RELEASE_PAGE,
                published_at=data.get("published_at"),
                assets=assets,
                preferred_asset=preferred_asset,
                is_newer=is_newer_version(version, APP_VERSION),
                repo=f"{GITHUB_OWNER}/{GITHUB_REPO}",
                source="github",
            )

        except Exception as error:
            last_error = error
            logger.warning("GitHub updater attempt %d/%d failed: %s", attempt + 1, RETRY_ATTEMPTS, error)
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))

    logger.error("All GitHub updater attempts failed: %s", last_error)
    return None


def fetch_website_release(timeout: int = 10) -> Optional[ReleaseInfo]:
    if not WEBSITE_RELEASE_JSON_URL:
        return None

    try:
        data = _request_json(WEBSITE_RELEASE_JSON_URL, timeout=timeout)

        version = str(data.get("version") or "").removeprefix("v")
        if not version:
            return None

        assets: list[ReleaseAsset] = []

        installer_url = data.get("direct_download") or data.get("download_url")
        installer_name = data.get("installer_filename") or data.get("filename") or f"NexusLauncherSetup-{version}-win-x64.exe"
        if installer_url:
            assets.append(
                ReleaseAsset(
                    name=str(installer_name),
                    download_url=str(installer_url),
                    content_type="application/vnd.microsoft.portable-executable",
                )
            )

        portable_url = data.get("portable_download") or data.get("portable_download_url")
        portable_name = data.get("portable_filename") or f"NexusLauncher-{version}-win-x64-portable.zip"
        if portable_url:
            assets.append(
                ReleaseAsset(
                    name=str(portable_name),
                    download_url=str(portable_url),
                    content_type="application/zip",
                )
            )

        preferred_asset = choose_preferred_asset(assets)

        return ReleaseInfo(
            version=version,
            tag=f"v{version}",
            name=f"Nexus Launcher {version}",
            body=str(data.get("note") or ""),
            page_url=str(data.get("latest_release_page") or GITHUB_LATEST_RELEASE_PAGE),
            published_at=str(data.get("updated_at") or "") or None,
            assets=assets,
            preferred_asset=preferred_asset,
            is_newer=is_newer_version(version, APP_VERSION),
            repo=str(data.get("repo") or f"{GITHUB_OWNER}/{GITHUB_REPO}"),
            source="website",
        )
    except Exception as error:
        logger.warning("Website release check failed: %s", error)
        return None


def fetch_latest_release(timeout: int = 10) -> Optional[ReleaseInfo]:
    """Backward-compatible update check.

    Nexus checks GitHub Releases first, then website release.json as fallback.
    If both are available, the highest version wins.
    """

    candidates = [
        fetch_github_latest_release(timeout=timeout),
        fetch_website_release(timeout=timeout),
    ]

    candidates = [item for item in candidates if item]
    if not candidates:
        return None

    return sorted(candidates, key=lambda item: normalize_version(item.version), reverse=True)[0]


def choose_preferred_asset(assets: list[ReleaseAsset]) -> ReleaseAsset | None:
    if not assets:
        return None

    def score(asset: ReleaseAsset):
        name = asset.name.lower()
        value = 0

        if name.endswith(".sha256"):
            value -= 1000

        if name.endswith(".exe"):
            value += 100

        # User-guided auto-update should prefer installer because it can replace the installed app safely.
        if "setup" in name or "installer" in name:
            value += 140

        if "portable" in name and name.endswith(".zip"):
            value += 50

        if "win" in name or "windows" in name:
            value += 25

        if "x64" in name or "amd64" in name:
            value += 15

        return value

    return sorted(assets, key=score, reverse=True)[0]


def is_installer_path(path: str | Path) -> bool:
    name = Path(path).name.lower()
    return name.endswith(".exe") and ("setup" in name or "installer" in name)


def is_archive_path(path: str | Path) -> bool:
    return Path(path).name.lower().endswith(".zip")


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
        f"Source: {release.source}\n"
        f"Repo: {release.repo}\n"
        f"Current version: {APP_VERSION}\n"
        f"Latest version: {release.version}\n"
        f"Asset: {downloaded_path.name}\n"
        f"SHA256: {sha256_file(downloaded_path)}\n\n"
        f"File path:\n{downloaded_path}\n\n"
        "If this is an installer .exe, Nexus can close itself and launch it.\n"
        "If this is portable .zip, extract it over the old portable folder.\n",
        encoding="utf-8",
    )
    return notes


def create_update_launcher_script(downloaded_path: str | Path) -> Path:
    """Create a small Windows .cmd helper that starts installer after Nexus exits."""

    downloaded_path = Path(downloaded_path).resolve()
    UPDATES_DIR.mkdir(parents=True, exist_ok=True)

    script = UPDATES_DIR / "run_nexus_update.cmd"

    if os.name == "nt":
        script.write_text(
            "@echo off\r\n"
            "title Nexus Launcher Update\r\n"
            "echo Waiting for Nexus Launcher to close...\r\n"
            "timeout /t 2 /nobreak >nul\r\n"
            f'start "" "{downloaded_path}"\r\n',
            encoding="utf-8",
        )
    else:
        script.write_text(
            "#!/usr/bin/env sh\n"
            "sleep 2\n"
            f'xdg-open "{downloaded_path}" >/dev/null 2>&1 &\n',
            encoding="utf-8",
        )
        try:
            script.chmod(0o755)
        except Exception:
            pass

    return script


def start_installer_after_exit(downloaded_path: str | Path) -> Path:
    """Start downloaded setup installer through helper script.

    The caller should close the Qt application after this function returns.
    """

    downloaded_path = Path(downloaded_path)

    if not downloaded_path.exists():
        raise FileNotFoundError(str(downloaded_path))

    if not is_installer_path(downloaded_path):
        raise RuntimeError("Автообновление доступно только для Setup .exe. Portable ZIP нужно распаковывать вручную.")

    script = create_update_launcher_script(downloaded_path)

    if os.name == "nt":
        flags = 0
        try:
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        except Exception:
            flags = 0

        subprocess.Popen(
            ["cmd.exe", "/c", str(script)],
            creationflags=flags,
            close_fds=True,
        )
        return script

    subprocess.Popen([str(script)], close_fds=True)
    return script
