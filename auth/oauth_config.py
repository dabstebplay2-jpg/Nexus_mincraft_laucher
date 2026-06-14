import os


MICROSOFT_CLIENT_ID = os.environ.get("NEXUS_MICROSOFT_CLIENT_ID", "").strip()
MICROSOFT_REDIRECT_URI = os.environ.get(
    "NEXUS_MICROSOFT_REDIRECT_URI",
    "http://localhost:8089/auth/microsoft/callback",
).strip()


ELY_CLIENT_ID = os.environ.get("NEXUS_ELY_CLIENT_ID", "").strip()
ELY_CLIENT_SECRET = os.environ.get("NEXUS_ELY_CLIENT_SECRET", "").strip()
ELY_REDIRECT_URI = os.environ.get(
    "NEXUS_ELY_REDIRECT_URI",
    "http://localhost:8089/auth/ely/callback",
).strip()


def microsoft_is_configured():
    return bool(MICROSOFT_CLIENT_ID and MICROSOFT_REDIRECT_URI)


def ely_is_configured():
    return bool(ELY_CLIENT_ID and ELY_CLIENT_SECRET and ELY_REDIRECT_URI)