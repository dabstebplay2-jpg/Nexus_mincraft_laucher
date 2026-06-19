const menuBtn = document.getElementById("menuBtn");
const nav = document.getElementById("nav");

if (menuBtn && nav) {
  menuBtn.addEventListener("click", () => {
    nav.classList.toggle("open");
  });
}

const repo = "dabstebplay2-jpg/Nexus_mincraft_laucher";
const fallbackVersion = "0.7.13";

const versionText = document.getElementById("versionText");
const versionStat = document.getElementById("versionStat");
const footerVersion = document.getElementById("footerVersion");
const downloadBtn = document.getElementById("downloadBtn");
const setupBtn = document.getElementById("setupBtn");
const portableBtn = document.getElementById("portableBtn");
const copyLinkBtn = document.getElementById("copyLinkBtn");
const fileName = document.getElementById("fileName");

function setVersion(version) {
  const clean = String(version || fallbackVersion).replace(/^v/i, "");
  const setupName = `NexusLauncherSetup-${clean}-win-x64.exe`;
  const portableName = `NexusLauncher-${clean}-win-x64-portable.zip`;
  const setupUrl = `https://github.com/${repo}/releases/latest/download/${setupName}`;
  const portableUrl = `https://github.com/${repo}/releases/latest/download/${portableName}`;

  [versionText, versionStat, footerVersion].forEach((el) => {
    if (el) el.textContent = clean;
  });

  [downloadBtn, setupBtn].forEach((el) => {
    if (el) el.href = setupUrl;
  });

  if (portableBtn) portableBtn.href = portableUrl;
  if (fileName) fileName.textContent = setupName;

  if (copyLinkBtn) {
    copyLinkBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(setupUrl);
        copyLinkBtn.textContent = "Ссылка скопирована";
        setTimeout(() => (copyLinkBtn.textContent = "Скопировать ссылку"), 1400);
      } catch {
        window.prompt("Скопируй ссылку:", setupUrl);
      }
    }, { once: true });
  }
}

setVersion(fallbackVersion);

fetch(`https://api.github.com/repos/${repo}/releases/latest`, { cache: "no-store" })
  .then((res) => (res.ok ? res.json() : null))
  .then((release) => {
    if (!release || !release.tag_name) return;
    setVersion(release.tag_name);
  })
  .catch(() => {});
