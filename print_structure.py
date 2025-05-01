import os


def print_directory_structure(startpath):
    # Список игнорируемых папок и файлов
    IGNORE_LIST = {
        '__pycache__', '.git', '.idea', 'venv', 'env', '.env',
        '.vscode', '.dockerignore', '.gitignore', '*.pyc',
        '*.pyo', '*.pyd', '.DS_Store', '*.sqlite3', '*.db',
        '*.log', 'staticfiles', 'node_modules', 'dist', 'build'
    }

    for root, dirs, files in os.walk(startpath):
        # Удаляем игнорируемые папки из списка dirs (чтобы os.walk их не обрабатывал)
        dirs[:] = [d for d in dirs if d not in IGNORE_LIST]

        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)

        # Выводим только базовое имя текущей папки (если она не в игнорируемом списке)
        current_dir = os.path.basename(root)
        if current_dir not in IGNORE_LIST:
            print(f"{indent}{current_dir}/")

            subindent = ' ' * 4 * (level + 1)
            for f in files:
                # Игнорируем файлы из списка
                if not any(f.endswith(ext) for ext in IGNORE_LIST) and f not in IGNORE_LIST:
                    print(f"{subindent}{f}")


if __name__ == "__main__":
    project_path = os.getcwd()  # Текущая директория
    print("Структура проекта (игнорируются системные/служебные файлы):")
    print_directory_structure(project_path)