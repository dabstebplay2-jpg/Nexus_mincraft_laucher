const DEFAULT_VERSION = window.NEXUS_VERSION || "0.7.8";
const DEFAULT_REPO = window.NEXUS_REPO || "dabstebplay2-jpg/Nexus_mincraft_laucher";

const $ = (selector) => document.querySelector(selector);

function latestDownloadUrl(repo, filename) {
  return `https://github.com/${repo}/releases/latest/download/${filename}`;
}

function buildFallbackRelease(version = DEFAULT_VERSION, repo = DEFAULT_REPO) {
  const installer = `NexusLauncherSetup-${version}-win-x64.exe`;
  const portable = `NexusLauncher-${version}-win-x64-portable.zip`;

  return {
    repo,
    version,
    latest_release_api: `https://api.github.com/repos/${repo}/releases/latest`,
    direct_download: latestDownloadUrl(repo, installer),
    portable_download: latestDownloadUrl(repo, portable),
    installer_filename: installer,
    portable_filename: portable,
  };
}

async function fetchJson(url) {
  const response = await fetch(url, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`${url}: ${response.status}`);
  }

  return response.json();
}

function setDownloadLinks(setupUrl, portableUrl, assetName, version) {
  ["#downloadBtn", "#mainDownloadBtn"].forEach((selector) => {
    const item = $(selector);
    if (item) item.href = setupUrl;
  });

  const portable = $("#portableBtn");
  if (portable) portable.href = portableUrl;

  const asset = $("#assetName");
  if (asset) asset.textContent = assetName;

  ["#versionText", "#versionStat", "#footerVersion"].forEach((selector) => {
    const item = $(selector);
    if (item) item.textContent = version;
  });
}

function pickSetupAsset(assets) {
  return (assets || []).find((asset) => {
    const name = String(asset.name || "").toLowerCase();
    return name.includes("setup") && name.endsWith(".exe");
  }) || (assets || []).find((asset) => String(asset.name || "").toLowerCase().endsWith(".exe"));
}

function pickPortableAsset(assets) {
  return (assets || []).find((asset) => {
    const name = String(asset.name || "").toLowerCase();
    return name.includes("portable") && name.endsWith(".zip");
  });
}

async function loadLocalRelease() {
  try {
    return await fetchJson("./release.json");
  } catch (error) {
    return buildFallbackRelease();
  }
}

async function loadRelease() {
  const local = await loadLocalRelease();
  const repo = local.repo || DEFAULT_REPO;
  const fallback = buildFallbackRelease(local.version || DEFAULT_VERSION, repo);

  const localSetupUrl = local.direct_download || local.download_url || fallback.direct_download;
  const localPortableUrl = local.portable_download || local.portable_download_url || fallback.portable_download;
  const localSetupName = local.installer_filename || local.filename || fallback.installer_filename;
  const localVersion = local.version || fallback.version;

  setDownloadLinks(localSetupUrl, localPortableUrl, localSetupName, localVersion);

  try {
    const apiUrl = local.latest_release_api || `https://api.github.com/repos/${repo}/releases/latest`;
    const release = await fetchJson(apiUrl);

    const setup = pickSetupAsset(release.assets);
    const portable = pickPortableAsset(release.assets);
    const latestVersion = String(release.tag_name || localVersion).replace(/^v/i, "");

    setDownloadLinks(
      setup?.browser_download_url || localSetupUrl,
      portable?.browser_download_url || localPortableUrl,
      setup?.name || localSetupName,
      latestVersion
    );
  } catch (error) {
    console.warn("GitHub latest release unavailable, using local release.json", error);
  }
}

function setupMenu() {
  const btn = $("#menuBtn");
  const nav = $("#nav");
  if (!btn || !nav) return;

  btn.addEventListener("click", () => nav.classList.toggle("open"));
  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => nav.classList.remove("open"));
  });
}

function setupCopy() {
  const btn = $("#copyBtn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const link = $("#mainDownloadBtn")?.href || buildFallbackRelease().direct_download;
    try {
      await navigator.clipboard.writeText(link);
      btn.textContent = "Ссылка скопирована";
      setTimeout(() => btn.textContent = "Скопировать ссылку", 1800);
    } catch (error) {
      alert(link);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupMenu();
  setupCopy();
  loadRelease();
});
