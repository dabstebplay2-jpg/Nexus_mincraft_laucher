const latestVersion = window.NEXUS_LATEST_VERSION || "0.6.0";

const presets = {
  fps: {
    title: "⚡ FPS Boost",
    desc: "Для слабых и средних ПК: повышает FPS, снижает микрофризы и расход памяти.",
    score: "92%",
    ram: "4096 MB",
    mods: "5",
    tags: ["Sodium", "Lithium", "FerriteCore", "ModernFix", "+1"]
  },
  beauty: {
    title: "🌸 Beauty Pack",
    desc: "Для красивой картинки: шейдеры, освещение, текстуры и визуальные улучшения.",
    score: "84%",
    ram: "8192 MB",
    mods: "7",
    tags: ["Iris", "Sodium", "Continuity", "ETF", "Dynamic Lights"]
  },
  vanilla: {
    title: "🏰 Vanilla+",
    desc: "Больше удобства без сильного изменения оригинального Minecraft.",
    score: "96%",
    ram: "4096 MB",
    mods: "9",
    tags: ["Jade", "AppleSkin", "Xaero", "Mouse Tweaks", "Controlling"]
  },
  survival: {
    title: "🔥 Survival",
    desc: "Выживание с картой, QoL-модами, навигацией и стабильной производительностью.",
    score: "88%",
    ram: "6144 MB",
    mods: "11",
    tags: ["JourneyMap", "Waystones", "Jade", "Nature Compass", "Backpack"]
  }
};

const mods = [
  {
    icon: "🔥",
    title: "Sodium",
    downloads: "167M+ скачиваний",
    desc: "Рендеринг-оптимизация для повышения FPS.",
    tags: ["Оптимизация", "Fabric"],
    gradient: "linear-gradient(135deg, #fb923c, #ef4444)"
  },
  {
    icon: "🌈",
    title: "Iris Shaders",
    downloads: "80M+ скачиваний",
    desc: "Шейдеры, совместимые с Sodium.",
    tags: ["Шейдеры", "Fabric"],
    gradient: "linear-gradient(135deg, #38bdf8, #a855f7)"
  },
  {
    icon: "🧩",
    title: "Fabric API",
    downloads: "184M+ скачиваний",
    desc: "Базовая библиотека для множества модов.",
    tags: ["Библиотека", "Fabric"],
    gradient: "linear-gradient(135deg, #22c55e, #bef264)"
  },
  {
    icon: "🧠",
    title: "Lithium",
    downloads: "75M+ скачиваний",
    desc: "Оптимизирует игровую логику и серверную часть.",
    tags: ["FPS", "Fabric"],
    gradient: "linear-gradient(135deg, #22c55e, #14b8a6)"
  },
  {
    icon: "🗺",
    title: "Jade",
    downloads: "60M+ скачиваний",
    desc: "Показывает информацию о блоках, мобах и предметах.",
    tags: ["Интерфейс", "QoL"],
    gradient: "linear-gradient(135deg, #0ea5e9, #22c55e)"
  }
];

let modOffset = 0;

function $(selector) {
  return document.querySelector(selector);
}

function $all(selector) {
  return Array.from(document.querySelectorAll(selector));
}

function showToast(text) {
  const toast = $("#toast");
  toast.textContent = text;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 1800);
}

function setVersion() {
  const versionTargets = [
    "#versionPill",
    "#metricVersion",
    "#footerVersion"
  ];

  versionTargets.forEach((id) => {
    const el = $(id);
    if (el) el.textContent = latestVersion;
  });

  const downloadVersion = $("#downloadVersion");
  if (downloadVersion) downloadVersion.textContent = `Версия ${latestVersion}`;

  const current = $("#roadCurrent");
  if (current) current.textContent = latestVersion;
}

function renderPreset(key) {
  const preset = presets[key] || presets.fps;

  $("#presetTitle").textContent = preset.title;
  $("#presetDesc").textContent = preset.desc;
  $("#presetScore").textContent = preset.score;
  $("#presetRam").textContent = preset.ram;
  $("#presetMods").textContent = preset.mods;

  $("#presetTags").innerHTML = preset.tags.map((tag) => `<span>${tag}</span>`).join("");

  const visual = $("#presetVisual");
  visual.dataset.preset = key;
}

function renderMods() {
  const visible = [];

  for (let i = 0; i < 3; i++) {
    visible.push(mods[(modOffset + i) % mods.length]);
  }

  $("#modCards").innerHTML = visible.map((mod) => `
    <article>
      <div class="mod-icon" style="background:${mod.gradient}">${mod.icon}</div>
      <h3>${mod.title}</h3>
      <div class="mod-downloads">${mod.downloads}</div>
      <p>${mod.desc}</p>
      <div class="mod-chip-row">
        ${mod.tags.map((tag) => `<span>${tag}</span>`).join("")}
      </div>
    </article>
  `).join("");
}

function createParticles() {
  const holder = $("#particles");
  if (!holder) return;

  holder.innerHTML = "";

  for (let i = 0; i < 90; i++) {
    const p = document.createElement("span");
    p.className = "particle";
    p.style.left = `${Math.random() * 100}%`;
    p.style.top = `${Math.random() * 100}%`;
    p.style.animationDelay = `${Math.random() * 7}s`;
    p.style.animationDuration = `${5 + Math.random() * 8}s`;
    holder.appendChild(p);
  }
}

function setupReveal() {
  const items = $all(".reveal");

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
      }
    });
  }, { threshold: 0.12 });

  items.forEach((item) => observer.observe(item));
}

function setupNavActive() {
  const links = $all(".nav a");
  const sections = links
    .map((link) => document.querySelector(link.getAttribute("href")))
    .filter(Boolean);

  window.addEventListener("scroll", () => {
    let current = "";

    sections.forEach((section) => {
      if (window.scrollY >= section.offsetTop - 140) {
        current = `#${section.id}`;
      }
    });

    links.forEach((link) => {
      link.classList.toggle("active", link.getAttribute("href") === current);
    });
  });
}

function copySiteCommand() {
  const command = "cd C:\\Nexus_minecraft_launcher\\website && ..\\.venv\\Scripts\\python.exe -m http.server 8080";

  navigator.clipboard?.writeText(command)
    .then(() => showToast("Команда скопирована"))
    .catch(() => {
      alert(command);
    });
}

function setupMagnetic() {
  $all(".magnetic").forEach((el) => {
    el.addEventListener("mousemove", (event) => {
      const rect = el.getBoundingClientRect();
      const x = event.clientX - rect.left - rect.width / 2;
      const y = event.clientY - rect.top - rect.height / 2;

      el.style.transform = `translate(${x * 0.04}px, ${y * 0.04}px)`;
    });

    el.addEventListener("mouseleave", () => {
      el.style.transform = "";
    });
  });
}

function setupCoreTilt() {
  const core = $("#nexusCore");

  if (!core) return;

  core.addEventListener("mousemove", (event) => {
    const rect = core.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width - 0.5;
    const y = (event.clientY - rect.top) / rect.height - 0.5;

    core.style.transform = `rotateY(${x * 8}deg) rotateX(${-y * 8}deg)`;
  });

  core.addEventListener("mouseleave", () => {
    core.style.transform = "";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setVersion();
  createParticles();
  setupReveal();
  setupNavActive();
  setupMagnetic();
  setupCoreTilt();
  renderPreset("fps");
  renderMods();

  $all(".preset-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      $all(".preset-tab").forEach((item) => item.classList.remove("active"));
      btn.classList.add("active");
      renderPreset(btn.dataset.preset);
      showToast(`Пресет выбран: ${btn.textContent.trim()}`);
    });
  });

  $all(".check-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      $all(".check-item").forEach((item) => item.classList.remove("active"));
      btn.classList.add("active");
      showToast(btn.textContent.replace("✓", "").trim());
    });
  });

  $("#prevMod")?.addEventListener("click", () => {
    modOffset = (modOffset - 1 + mods.length) % mods.length;
    renderMods();
  });

  $("#nextMod")?.addEventListener("click", () => {
    modOffset = (modOffset + 1) % mods.length;
    renderMods();
  });

  $("#themeToggle")?.addEventListener("click", () => {
    document.body.classList.toggle("light");
    localStorage.setItem("nexus-theme", document.body.classList.contains("light") ? "light" : "dark");
    showToast(document.body.classList.contains("light") ? "Светлая тема" : "Тёмная тема");
  });

  if (localStorage.getItem("nexus-theme") === "light") {
    document.body.classList.add("light");
  }

  $("#copyCommand")?.addEventListener("click", copySiteCommand);
  $("#copyFooter")?.addEventListener("click", copySiteCommand);

  $("#createBuildBtn")?.addEventListener("click", () => {
    showToast("Smart Builder будет подключён в Nexus 0.7");
  });

  $("#openCatalog")?.addEventListener("click", () => {
    document.querySelector("#modrinth")?.scrollIntoView({ behavior: "smooth" });
    showToast("Каталог Modrinth открыт");
  });

  $all("[data-demo]").forEach((btn) => {
    btn.addEventListener("click", () => {
      showToast(`Демо: ${btn.textContent.trim()}`);
    });
  });

  $("#downloadBtn")?.addEventListener("click", () => {
    showToast("Скачивание Nexus Launcher");
  });
});

async function setupLatestGitHubRelease() {
  const api = "https://api.github.com/repos/dabstebplay2-jpg/Nexus_mincraft_laucher/releases/latest";
  const fallback = "https://github.com/dabstebplay2-jpg/Nexus_mincraft_laucher/releases/latest";

  const btn = document.querySelector("#downloadBtn");
  const versionPill = document.querySelector("#versionPill");
  const metricVersion = document.querySelector("#metricVersion");
  const footerVersion = document.querySelector("#footerVersion");
  const downloadVersion = document.querySelector("#downloadVersion");

  try {
    const response = await fetch(api, {
      headers: {
        "Accept": "application/vnd.github+json"
      }
    });

    if (!response.ok) {
      throw new Error("GitHub release not available");
    }

    const release = await response.json();
    const tag = release.tag_name || "latest";
    const version = tag.replace(/^v/i, "");

    const assets = Array.isArray(release.assets) ? release.assets : [];
    const asset = assets.find((item) => {
      const name = String(item.name || "").toLowerCase();
      return name.endsWith(".exe") || name.endsWith(".zip");
    });

    const downloadUrl = asset?.browser_download_url || release.html_url || fallback;
    const assetName = asset?.name || "последний релиз";

    if (btn) {
      btn.href = downloadUrl;
      btn.textContent = "▣ Скачать " + assetName;
      btn.setAttribute("download", "");
    }

    [versionPill, metricVersion, footerVersion].forEach((el) => {
      if (el) el.textContent = version;
    });

    if (downloadVersion) {
      downloadVersion.textContent = "Версия " + version;
    }
  }
  catch (error) {
    if (btn) {
      btn.href = fallback;
      btn.textContent = "▣ Открыть последнюю версию на GitHub";
      btn.removeAttribute("download");
    }
  }
}

document.addEventListener("DOMContentLoaded", setupLatestGitHubRelease);
