Nexus Launcher Website — Direct Download

Что изменено:
1. Главная кнопка сайта теперь скачивает установщик напрямую:
   https://github.com/dabstebplay2-jpg/Nexus_mincraft_laucher/releases/latest/download/NexusLauncherSetup-0.7.2-win-x64.exe

2. Пользователь не переходит на страницу GitHub — браузер сразу начинает загрузку.

3. Вторая кнопка скачивает portable ZIP:
   https://github.com/dabstebplay2-jpg/Nexus_mincraft_laucher/releases/latest/download/NexusLauncher-0.7.2-win-x64-portable.zip

Важно:
- Прямая ссылка начнёт работать после того, как в GitHub Releases появится asset с точным именем:
  NexusLauncherSetup-0.7.2-win-x64.exe

- Для этого нужно собрать и опубликовать релиз v0.7.2 через GitHub Actions.

Как залить сайт:
- Если используешь GitHub Pages из папки /website, просто закоммить изменения website/
- Если сайт деплоится на Vercel/Netlify, запушь изменения в main
