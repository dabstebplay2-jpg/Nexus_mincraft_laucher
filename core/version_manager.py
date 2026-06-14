import minecraft_launcher_lib


class VersionManager:
    def get_all_versions(self):
        versions = minecraft_launcher_lib.utils.get_version_list()
        return versions

    def get_release_versions(self):
        versions = self.get_all_versions()

        release_versions = [
            version["id"]
            for version in versions
            if version.get("type") == "release"
        ]

        return release_versions

    def get_snapshot_versions(self):
        versions = self.get_all_versions()

        snapshot_versions = [
            version["id"]
            for version in versions
            if version.get("type") == "snapshot"
        ]

        return snapshot_versions