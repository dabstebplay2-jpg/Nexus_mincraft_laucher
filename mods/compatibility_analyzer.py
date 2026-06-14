from pathlib import Path


class CompatibilityAnalyzer:
    def __init__(self, instance: dict):
        self.instance = instance
        self.issues = []
        self.warnings = []
        self.success = []

    def analyze(self):
        self.issues = []
        self.warnings = []
        self.success = []

        self.check_loader()
        self.check_ram()
        self.check_mods_folder()
        self.check_mod_count()

        return {
            "score": self.calculate_score(),
            "status": self.get_status(),
            "issues": self.issues,
            "warnings": self.warnings,
            "success": self.success,
        }

    def check_loader(self):
        loader = self.instance.get("loader", "vanilla")

        if loader == "vanilla":
            self.warnings.append("Сборка Vanilla. Большинство модов требует Fabric или Forge.")
        else:
            self.success.append(f"Loader выбран: {loader}")

    def check_ram(self):
        ram = int(self.instance.get("ram", 2048))

        if ram < 2048:
            self.issues.append("Слишком мало RAM. Рекомендуется минимум 2 GB.")
        elif ram < 4096:
            self.warnings.append("Для модов лучше поставить 4 GB RAM или больше.")
        else:
            self.success.append(f"RAM достаточно: {ram} MB")

    def check_mods_folder(self):
        path = self.instance.get("path")

        if not path:
            self.issues.append("У сборки не найден путь к папке.")
            return

        mods_dir = Path(path) / ".minecraft" / "mods"

        if not mods_dir.exists():
            self.warnings.append("Папка mods пока не создана.")
            return

        jar_files = list(mods_dir.glob("*.jar"))

        if not jar_files:
            self.warnings.append("В сборке пока нет модов.")
        else:
            self.success.append(f"Найдено модов: {len(jar_files)}")

    def check_mod_count(self):
        path = self.instance.get("path")

        if not path:
            return

        mods_dir = Path(path) / ".minecraft" / "mods"

        if not mods_dir.exists():
            return

        count = len(list(mods_dir.glob("*.jar")))

        if count > 80:
            self.warnings.append("Очень много модов. Возможны конфликты и долгий запуск.")
        elif count > 40:
            self.warnings.append("Модов довольно много. Желательно проверить совместимость.")
        elif count > 0:
            self.success.append("Количество модов выглядит нормально.")

    def calculate_score(self):
        score = 100

        score -= len(self.issues) * 25
        score -= len(self.warnings) * 10

        return max(0, min(100, score))

    def get_status(self):
        score = self.calculate_score()

        if score >= 85:
            return "Отлично"
        if score >= 65:
            return "Нормально"
        if score >= 40:
            return "Есть риски"

        return "Проблемная сборка"