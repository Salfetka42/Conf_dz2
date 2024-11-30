import configparser
import os

def load_config(config_file):
    """Загрузка конфигурации из INI файла"""
    config = configparser.ConfigParser()
    config.read(config_file)
    return config['settings']

def read_git_object(repo_path, object_hash):
    """Чтение Git-объекта по его хэшу"""
    object_dir = os.path.join(repo_path, ".git", "objects", object_hash[:2])
    object_file = os.path.join(object_dir, object_hash[2:])

    if not os.path.exists(object_file):
        raise FileNotFoundError(f"Git object {object_hash} not found")

    with open(object_file, "rb") as file:
        compressed_data = file.read()

    import zlib
    decompressed_data = zlib.decompress(compressed_data)
    return decompressed_data.decode("utf-8")


def get_commit_data(repo_path, commit_hash):
    """Получение данных коммита из его объекта"""
    commit_data = read_git_object(repo_path, commit_hash)
    lines = commit_data.split("\n")
    parents = []
    message = ""
    is_message = False

    for line in lines:
        if is_message:
            message += line + "\n"
        elif line.startswith("parent "):
            parents.append(line.split(" ")[1])
        elif line == "":
            is_message = True

    return parents, message.strip()


def get_commit_graph(repo_path, starting_commit_hash):
    """Построение графа коммитов начиная с указанного хэша"""
    commit_graph = {}
    stack = [starting_commit_hash]

    while stack:
        current_commit = stack.pop()
        if current_commit not in commit_graph:
            parents, _ = get_commit_data(repo_path, current_commit)
            commit_graph[current_commit] = parents
            stack.extend(parents)

    return commit_graph


def generate_plantuml_graph(commit_graph, repo_path):
    """Генерация PlantUML графа"""
    plantuml_code = "@startuml\n"
    for commit, parents in commit_graph.items():
        _, commit_message = get_commit_data(repo_path, commit)
        commit_message = "".join(commit_message.split())

        for parent in parents:
            _, parent_message = get_commit_data(repo_path, parent)
            parent_message = "".join(parent_message.split())

            plantuml_code += f'participant {parent_message} as {parent}\n'
            plantuml_code += f'participant {commit_message} as {commit}\n'
            plantuml_code += f'"{parent}" --> "{commit}"\n'

    plantuml_code += "@enduml"
    return plantuml_code


def save_plantuml_code(plantuml_code, output_file):
    """Сохранение PlantUML кода в файл"""
    with open(output_file, "w") as file:
        file.write(plantuml_code)


def main(config_file):
    config = load_config(config_file)

    repo_path = config["repo_path"]
    starting_commit_hash = config["starting_commit_hash"]

    # Построение графа коммитов
    commit_graph = get_commit_graph(repo_path, starting_commit_hash)

    # Генерация PlantUML кода
    plantuml_code = generate_plantuml_graph(commit_graph, repo_path)

    # Сохранение кода в файл
    save_plantuml_code(plantuml_code, "graph.puml")
    print("PlantUML код сохранён в файл graph.puml")


if __name__ == "__main__":
    config_file = "config.ini"  # Имя конфигурационного файла
    main(config_file)
