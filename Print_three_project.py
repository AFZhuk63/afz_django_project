import os


def print_tree_structure(startpath):
    # Игнорируемые папки и файлы
    IGNORE = {
        '__pycache__', '.git', '.idea', '.venv', '.vscode',
        'env', '.env', 'staticfiles', 'node_modules'
    }

    # Разрешенные расширения
    ALLOWED_EXT = {'.py', '.html', '.css', '.txt', '.json', '.yml', '.sh', '.conf'}
    ALLOWED_FILES = {'Dockerfile', 'docker-compose.yml', 'manage.py'}

    print(f"{os.path.basename(startpath)}/")
    _print_tree(startpath, "", IGNORE, ALLOWED_EXT, ALLOWED_FILES)


def _print_tree(path, prefix, ignore, allowed_ext, allowed_files):
    entries = []
    try:
        entries = sorted(os.listdir(path))
    except:
        return

    entries = [e for e in entries if e not in ignore and not e.startswith('.')]

    for i, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        is_last = i == len(entries) - 1

        if os.path.isdir(full_path):
            # Обработка директории
            print(f"{prefix}{'└── ' if is_last else '├── '}{entry}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            _print_tree(full_path, new_prefix, ignore, allowed_ext, allowed_files)
        else:
            # Обработка файла
            ext = os.path.splitext(entry)[1]
            if ext in allowed_ext or entry in allowed_files:
                print(f"{prefix}{'└── ' if is_last else '├── '}{entry}")


if __name__ == "__main__":
    project_path = os.getcwd()
    print("СТРУКТУРА ПРОЕКТА:")
    print_tree_structure(project_path)