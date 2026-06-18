# Nexus Emergency Fix

Исправлено:

1. `core/download_manager.py`
   - общий lock для всех экземпляров DownloadManager;
   - уникальные временные файлы вместо одного `downloads.json.tmp`;
   - retry при `PermissionError`/`WinError 5` на Windows;
   - безопасное чтение повреждённого/занятого `downloads.json`.

2. `ui/pages/instances_page.py`
   - ошибка записи в `downloads.json` больше не прерывает запуск Minecraft/Fabric;
   - прогресс UI продолжает работать даже если журнал загрузок временно занят.

3. `mods/mod_installer.py`
   - ошибка записи в `downloads.json` больше не прерывает установку мода.

4. `ui/pages/mods_page.py`
   - иконки модов снова включены;
   - иконки грузятся в фоне через `RemoteImageLabel`, поэтому поиск Modrinth не ждёт загрузку картинок.

Как ставить:

```powershell
cd C:\Nexus_minecraft_launcher
Copy-Item -Recurse -Force .\data .\data_backup_before_emergencyfix
Expand-Archive -Force "$env:USERPROFILE\Downloads\Nexus_emergencyfix_changed_files.zip" "$env:USERPROFILE\Downloads\Nexus_emergencyfix"
Copy-Item -Recurse -Force "$env:USERPROFILE\Downloads\Nexus_emergencyfix\Nexus_emergency_changed\*" "C:\Nexus_minecraft_launcher\"
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
.\.venv\Scripts\python.exe -m py_compile main.py core\download_manager.py ui\pages\instances_page.py mods\mod_installer.py ui\pages\mods_page.py ui\utils\image_loader.py
.\.venv\Scripts\python.exe main.py
```
