import unittest
import tempfile
import shutil
from pathlib import Path
import zlib
from unittest.mock import patch, mock_open
from Script2 import (
    load_config,  # Функция для загрузки конфигурации из INI-файла
    read_git_object,  # Чтение объекта Git по хэшу
    get_commit_data,  # Извлечение данных о коммите (родители и сообщение)
    get_commit_graph,  # Построение графа коммитов
    generate_plantuml_graph,  # Генерация PlantUML-кода для графа
    save_plantuml_code,  # Сохранение PlantUML-кода в файл
)


class TestGitTools(unittest.TestCase):
    def setUp(self):
        """
        Настройка окружения для тестов:
        Создание временного репозитория с минимальной структурой Git.
        """
        # Создаем временный каталог для репозитория
        self.repo_dir = tempfile.mkdtemp()
        self.git_dir = Path(self.repo_dir) / ".git"
        self.objects_dir = self.git_dir / "objects"

        # Создаем необходимые директории .git и objects
        self.git_dir.mkdir()
        self.objects_dir.mkdir(parents=True)

        # Создаем файл HEAD с указанием текущей ветки
        self.head_path = self.git_dir / "HEAD"
        self.head_path.write_text("ref: refs/heads/main", encoding="utf-8")

        # Создаем папку для веток refs/heads и файл main для текущей ветки
        refs_dir = self.git_dir / "refs" / "heads"
        refs_dir.mkdir(parents=True)
        self.main_ref = refs_dir / "main"

        # Добавляем тестовый коммит в директорию objects
        self.commit_hash = "1234567890abcdef1234567890abcdef12345678"
        self.parent_hash = "fedcba0987654321fedcba0987654321fedcba09"

        # Данные для родительского коммита
        parent_commit_data = (
            "tree abcdef1234567890abcdef1234567890abcdef12\n"
            "author Parent Author <parent@example.com> 1695584200 +0000\n"
            "committer Parent Author <parent@example.com> 1695584200 +0000\n\n"
            "Parent commit\n"
        )
        # Сжимаем данные родительского коммита
        parent_compressed_data = zlib.compress(parent_commit_data.encode("utf-8"))
        parent_object_dir = self.objects_dir / self.parent_hash[:2]
        parent_object_dir.mkdir()
        parent_object_file = parent_object_dir / self.parent_hash[2:]
        with open(parent_object_file, "wb") as f:
            f.write(parent_compressed_data)

        # Данные для текущего коммита
        commit_data = (
            f"tree abcdef1234567890abcdef1234567890abcdef12\n"
            f"parent {self.parent_hash}\n"
            "author Test Author <test@example.com> 1695584200 +0000\n"
            "committer Test Author <test@example.com> 1695584200 +0000\n\n"
            "Initial commit\n"
        )
        # Сжимаем данные текущего коммита
        compressed_data = zlib.compress(commit_data.encode("utf-8"))
        object_dir = self.objects_dir / self.commit_hash[:2]
        object_dir.mkdir()
        object_file = object_dir / self.commit_hash[2:]
        with open(object_file, "wb") as f:
            f.write(compressed_data)

    def tearDown(self):
        """Очистка окружения после тестов: удаление временного репозитория."""
        shutil.rmtree(self.repo_dir)

    def test_load_config(self):
        """Тест: Загрузка конфигурации из INI-файла."""
        with patch(
                "builtins.open",
                mock_open(read_data="[settings]\nrepo_path=/repo/path\nstarting_commit_hash=12345678")
        ):
            config = load_config("dummy.ini")
            self.assertEqual(config["repo_path"], "/repo/path")
            self.assertEqual(config["starting_commit_hash"], "12345678")

    def test_read_git_object(self):
        """Тест: Чтение объекта Git из временного репозитория."""
        data = read_git_object(self.repo_dir, self.commit_hash)
        self.assertIn("Initial commit", data)  # Проверка сообщения коммита
        self.assertIn(f"parent {self.parent_hash}", data)  # Проверка наличия родителя

    def test_get_commit_data(self):
        """Тест: Извлечение данных коммита (родителей и сообщения)."""
        parents, message = get_commit_data(self.repo_dir, self.commit_hash)
        self.assertEqual(parents, [self.parent_hash])  # Проверка родительского коммита
        self.assertEqual(message, "Initial commit")  # Проверка сообщения коммита

    def test_get_commit_graph(self):
        """
        Тестирует построение графа коммитов.
        """
        graph = get_commit_graph(self.repo_dir, self.commit_hash)
        # Ожидаем, что граф будет включать коммит и его родителя
        expected_graph = {
            self.commit_hash: [self.parent_hash],
            self.parent_hash: []  # Родительский коммит без родителей
        }
        self.assertEqual(graph, expected_graph)  # Граф содержит корректные данные

    def test_generate_plantuml_graph(self):
        """Тест: Генерация PlantUML-кода для графа коммитов."""
        graph = {self.commit_hash: [self.parent_hash]}  # Пример графа
        plantuml_code = generate_plantuml_graph(graph, self.repo_dir)
        self.assertIn("@startuml", plantuml_code)  # Начало UML-кода
        self.assertIn(self.commit_hash, plantuml_code)  # Проверка на наличие текущего коммита
        self.assertIn(self.parent_hash, plantuml_code)  # Проверка на наличие родительского коммита

    def test_save_plantuml_code(self):
        """Тест: Сохранение PlantUML-кода в файл."""
        plantuml_code = "@startuml\n@enduml"  # Пример кода
        output_file = Path(self.repo_dir) / "output.puml"  # Путь к файлу
        save_plantuml_code(plantuml_code, output_file)
        self.assertTrue(output_file.exists())  # Проверка существования файла
        with open(output_file, "r", encoding="utf-8") as f:
            saved_code = f.read()
        self.assertEqual(saved_code, plantuml_code)  # Проверка содержимого файла


if __name__ == "__main__":
    unittest.main()
