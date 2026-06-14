const presets = {
  fps: {
    title: '⚡ FPS Boost',
    description: 'Для слабых и средних ПК: повышает FPS, снижает микрофризы и расход памяти.',
    ram: '4096 MB',
    score: '92%',
    mods: [
      ['Sodium', 'Главный мод для повышения FPS.'],
      ['Lithium', 'Оптимизирует игровую логику.'],
      ['FerriteCore', 'Снижает потребление RAM.'],
      ['ModernFix', 'Ускоряет загрузку и исправляет проблемы памяти.'],
      ['Mod Menu', 'Удобное меню модов.'],
    ],
  },
  beauty: {
    title: '🌄 Beautiful Minecraft',
    description: 'Красивый Minecraft с шейдерами, улучшенными текстурами и хорошей производительностью.',
    ram: '6144 MB',
    score: '86%',
    mods: [
      ['Sodium', 'Производительность для графической сборки.'],
      ['Iris Shaders', 'Поддержка шейдеров.'],
      ['Continuity', 'Соединённые текстуры.'],
      ['Entity Texture Features', 'Улучшенные текстуры сущностей.'],
      ['Mod Menu', 'Удобное управление модами.'],
    ],
  },
  vanilla: {
    title: '🧱 Vanilla+',
    description: 'Аккуратная сборка без перегруза: Minecraft остаётся ванильным, но становится удобнее.',
    ram: '4096 MB',
    score: '94%',
    mods: [
      ['Mod Menu', 'Меню установленных модов.'],
      ['AppleSkin', 'Информация о еде и насыщении.'],
      ['Jade', 'Подсказки по блокам и мобам.'],
      ['Xaero’s Minimap', 'Удобная миникарта.'],
    ],
  },
  survival: {
    title: '⚔ Survival Adventure',
    description: 'Сборка для исследования, выживания и навигации по миру.',
    ram: '6144 MB',
    score: '88%',
    mods: [
      ['Xaero’s Minimap', 'Миникарта для путешествий.'],
      ['Xaero’s World Map', 'Полная карта мира.'],
      ['Jade', 'Информация о блоках и мобах.'],
      ['AppleSkin', 'Понятная система еды.'],
    ],
  },
};

const presetOutput = document.getElementById('presetOutput');
const tabs = document.querySelectorAll('.tab');
const toast = document.getElementById('toast');
const mobileMenu = document.getElementById('mobileMenu');
const menuBtn = document.getElementById('menuBtn');
const themeToggle = document.getElementById('themeToggle');
const cursorGlow = document.getElementById('cursorGlow');

function renderPreset(key) {
  const preset = presets[key] || presets.fps;
  presetOutput.innerHTML = `
    <h3>${preset.title}</h3>
    <p>${preset.description}</p>
    <div class="score-card">
      <div><strong>${preset.score}</strong><span>стабильность</span></div>
      <div><strong>${preset.ram}</strong><span>RAM</span></div>
      <div><strong>${preset.mods.length}</strong><span>модов</span></div>
    </div>
    <div class="mods">
      ${preset.mods.map(([name, reason]) => `<div><b>${name}</b><span>${reason}</span></div>`).join('')}
    </div>
  `;
}

renderPreset('fps');

tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    tabs.forEach((item) => item.classList.remove('active'));
    tab.classList.add('active');
    renderPreset(tab.dataset.preset);
  });
});

function showToast(text) {
  toast.textContent = text;
  toast.classList.add('show');
  window.setTimeout(() => toast.classList.remove('show'), 1800);
}

document.getElementById('copyInstall')?.addEventListener('click', async () => {
  const command = 'cd C:\\Nexus_minecraft_launcher\\website && ..\\.venv\\Scripts\\python.exe -m http.server 8080';
  try {
    await navigator.clipboard.writeText(command);
    showToast('Команда скопирована');
  } catch {
    showToast('Не удалось скопировать');
  }
});

menuBtn?.addEventListener('click', () => {
  mobileMenu.classList.toggle('open');
  document.body.classList.toggle('no-scroll', mobileMenu.classList.contains('open'));
});

mobileMenu?.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', () => {
    mobileMenu.classList.remove('open');
    document.body.classList.remove('no-scroll');
  });
});

const savedTheme = localStorage.getItem('nexus-theme');
if (savedTheme) document.documentElement.dataset.theme = savedTheme;
if (themeToggle) themeToggle.textContent = document.documentElement.dataset.theme === 'light' ? '☀' : '☾';

themeToggle?.addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('nexus-theme', next);
  themeToggle.textContent = next === 'light' ? '☀' : '☾';
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) entry.target.classList.add('visible');
  });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal').forEach((item) => observer.observe(item));

window.addEventListener('pointermove', (event) => {
  if (!cursorGlow) return;
  cursorGlow.style.left = `${event.clientX}px`;
  cursorGlow.style.top = `${event.clientY}px`;
});
