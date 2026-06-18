const NEXUS_VERSION = window.NEXUS_VERSION || "0.7.5";
const RELEASE_API = "https://api.github.com/repos/dabstebplay2-jpg/Nexus_mincraft_laucher/releases/latest";
const FALLBACK_SETUP = "https://github.com/dabstebplay2-jpg/Nexus_mincraft_laucher/releases/latest/download/NexusLauncherSetup-0.7.5-win-x64.exe";
const FALLBACK_PORTABLE = "https://github.com/dabstebplay2-jpg/Nexus_mincraft_laucher/releases/latest/download/NexusLauncher-0.7.5-win-x64-portable.zip";

const $ = (selector) => document.querySelector(selector);

function setDownloadLinks(setupUrl, portableUrl, assetName, version) {
  ["#downloadBtn", "#mainDownloadBtn"].forEach((selector) => {
    const item = $(selector);
    if (item) item.href = setupUrl || FALLBACK_SETUP;
  });

  const portable = $("#portableBtn");
  if (portable) portable.href = portableUrl || FALLBACK_PORTABLE;

  const asset = $("#assetName");
  if (asset) asset.textContent = assetName || "NexusLauncherSetup-0.7.5-win-x64.exe";

  ["#versionText", "#versionStat", "#footerVersion"].forEach((selector) => {
    const item = $(selector);
    if (item) item.textContent = version || NEXUS_VERSION;
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

async function loadRelease() {
  try {
    const response = await fetch(RELEASE_API, { headers: { Accept: "application/vnd.github+json" } });
    if (!response.ok) throw new Error("No release");
    const release = await response.json();
    const setup = pickSetupAsset(release.assets);
    const portable = pickPortableAsset(release.assets);
    const version = String(release.tag_name || NEXUS_VERSION).replace(/^v/i, "");

    setDownloadLinks(
      setup?.browser_download_url || FALLBACK_SETUP,
      portable?.browser_download_url || FALLBACK_PORTABLE,
      setup?.name || "NexusLauncherSetup-0.7.5-win-x64.exe",
      version
    );
  } catch (error) {
    setDownloadLinks(FALLBACK_SETUP, FALLBACK_PORTABLE, "NexusLauncherSetup-0.7.5-win-x64.exe", NEXUS_VERSION);
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
    const link = $("#mainDownloadBtn")?.href || FALLBACK_SETUP;
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
