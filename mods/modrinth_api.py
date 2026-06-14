import json
import logging

import requests

try:
    from core.app_info import USER_AGENT
except Exception:
    USER_AGENT = "NexusLauncher/0.6.0"


logger = logging.getLogger(__name__)


class ModrinthAPI:
    BASE_URL = "https://api.modrinth.com/v2"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
        })

    def build_facets(
        self,
        minecraft_version: str | None = None,
        loader: str | None = None,
        project_type: str = "mod",
    ):
        facets = [
            [f"project_type:{project_type}"],
        ]

        if minecraft_version:
            facets.append([f"versions:{minecraft_version}"])

        if loader and loader != "vanilla":
            facets.append([f"categories:{loader}"])

        return json.dumps(facets)

    def search_projects_page(
        self,
        query: str = "",
        minecraft_version: str | None = None,
        loader: str | None = None,
        project_type: str = "mod",
        limit: int = 48,
        offset: int = 0,
        index: str = "downloads",
    ):
        limit = max(1, min(int(limit), 100))
        offset = max(0, int(offset))

        params = {
            "query": query or "",
            "limit": limit,
            "offset": offset,
            "index": index,
            "facets": self.build_facets(
                minecraft_version=minecraft_version,
                loader=loader,
                project_type=project_type,
            ),
        }

        logger.info("Searching Modrinth page: %s", params)

        response = self.session.get(
            f"{self.BASE_URL}/search",
            params=params,
            timeout=25,
        )
        response.raise_for_status()

        data = response.json()

        return {
            "hits": data.get("hits", []),
            "offset": data.get("offset", offset),
            "limit": data.get("limit", limit),
            "total_hits": data.get("total_hits", 0),
        }

    def search_projects(
        self,
        query: str = "",
        minecraft_version: str | None = None,
        loader: str | None = None,
        project_type: str = "mod",
        limit: int = 48,
        offset: int = 0,
        index: str = "downloads",
    ):
        page = self.search_projects_page(
            query=query,
            minecraft_version=minecraft_version,
            loader=loader,
            project_type=project_type,
            limit=limit,
            offset=offset,
            index=index,
        )

        return page.get("hits", [])

    def get_popular_projects(
        self,
        minecraft_version: str | None = None,
        loader: str | None = None,
        project_type: str = "mod",
        limit: int = 48,
        offset: int = 0,
    ):
        return self.search_projects(
            query="",
            minecraft_version=minecraft_version,
            loader=loader,
            project_type=project_type,
            limit=limit,
            offset=offset,
            index="downloads",
        )

    def get_project(self, project_id_or_slug: str):
        logger.info("Getting Modrinth project: %s", project_id_or_slug)

        response = self.session.get(
            f"{self.BASE_URL}/project/{project_id_or_slug}",
            timeout=25,
        )
        response.raise_for_status()

        return response.json()

    def get_project_versions(
        self,
        project_id_or_slug: str,
        minecraft_version: str | None = None,
        loader: str | None = None,
    ):
        params = {}

        if minecraft_version:
            params["game_versions"] = json.dumps([minecraft_version])

        if loader and loader != "vanilla":
            params["loaders"] = json.dumps([loader])

        logger.info(
            "Getting Modrinth versions: project=%s params=%s",
            project_id_or_slug,
            params,
        )

        response = self.session.get(
            f"{self.BASE_URL}/project/{project_id_or_slug}/version",
            params=params,
            timeout=25,
        )
        response.raise_for_status()

        return response.json()

    def get_version(self, version_id: str):
        response = self.session.get(
            f"{self.BASE_URL}/version/{version_id}",
            timeout=25,
        )
        response.raise_for_status()

        return response.json()