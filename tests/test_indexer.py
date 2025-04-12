import unittest
from utils.text_preprocessing import preprocess_text, DEFAULT_STOPWORDS

class TestDocumentPreprocessing(unittest.TestCase):
    def test_lowercase_and_whitespace(self):
        text = "  This   is   a   DOCUMENT.  "
        expected = "this is a document."
        self.assertEqual(preprocess_text(text), expected)

    def test_code_blocks_and_inline_code_preserved(self):
        text = "# Heading\nSome doc. `inline_code()` and\n```\ndef foo():\n    pass\n```\n"
        expected = "# heading some doc. `inline_code()` and ``` def foo(): pass ```"
        self.assertEqual(preprocess_text(text), expected)

    def test_comment_and_docstring_removal(self):
        text = '"""Docstring"""\n# Comment\nDoc line\n// JS comment\n/* block comment */'
        expected = "doc line"
        self.assertEqual(preprocess_text(text), expected)

    def test_stopword_removal_not_applied_by_default(self):
        text = "This is a test of the stopword removal system."
        expected = "this is a test of the stopword removal system."
        self.assertEqual(preprocess_text(text), expected)

    def test_markdown_not_stripped(self):
        text = "# Heading\nSome doc with [link](url) and ![img](url)"
        expected = "# heading some doc with [link](url) and ![img](url)"
        self.assertEqual(preprocess_text(text), expected)

    def test_identical_preprocessing_for_document_and_query(self):
        doc = "## Title\nSome code: `x = 1` # comment"
        query = "## Title\nSome code: `x = 1` # comment"
        self.assertEqual(preprocess_text(doc), preprocess_text(query))


import tempfile
import os
from utils.ignore_utils import load_ignore_patterns, get_ignore_spec, should_ignore
from unittest.mock import MagicMock

class TestIgnoreLogic(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to simulate a project
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = self.temp_dir.name

        # Create a mock ConfigManager
        self.config_manager = MagicMock()
        # Simulate config.yaml ignore patterns
        self.config_manager.config = {
            "indexer": {
                "ignore_patterns": [
                    "*.log",
                    "build/",
                    "tempfile.txt",
                    "nested_dir/ignored_subdir/"
                ]
            }
        }
        # Simulate method to get project ignore file path
        self.project_ignore_file = os.path.join(self.project_path, ".augmentoriumignore")
        self.config_manager.get_project_ignore_file_path.return_value = self.project_ignore_file

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_project_ignore(self, patterns):
        with open(self.project_ignore_file, "w") as f:
            for line in patterns:
                f.write(line + "\n")

    def test_ignore_patterns_from_config_yaml(self):
        # No project ignore file
        ignore_spec = get_ignore_spec(self.config_manager, self.project_path)
        # Should ignore .log files and build/ directory
        self.assertTrue(should_ignore(os.path.join(self.project_path, "error.log"), self.project_path, ignore_spec))
        self.assertTrue(should_ignore(os.path.join(self.project_path, "build", "main.py"), self.project_path, ignore_spec))
        self.assertTrue(should_ignore(os.path.join(self.project_path, "tempfile.txt"), self.project_path, ignore_spec))
        self.assertFalse(should_ignore(os.path.join(self.project_path, "main.py"), self.project_path, ignore_spec))

    def test_ignore_patterns_from_project_ignore_file(self):
        # Write project-specific ignore patterns
        self.write_project_ignore([
            "data/",
            "*.tmp",
            "keepme.txt"
        ])
        ignore_spec = get_ignore_spec(self.config_manager, self.project_path)
        # Should ignore files/dirs from project ignore file
        self.assertTrue(should_ignore(os.path.join(self.project_path, "data", "file.csv"), self.project_path, ignore_spec))
        self.assertTrue(should_ignore(os.path.join(self.project_path, "foo.tmp"), self.project_path, ignore_spec))
        self.assertTrue(should_ignore(os.path.join(self.project_path, "keepme.txt"), self.project_path, ignore_spec))
        self.assertFalse(should_ignore(os.path.join(self.project_path, "main.py"), self.project_path, ignore_spec))

    def test_ignore_both_config_and_project_file(self):
        # Write project-specific ignore patterns
        self.write_project_ignore([
            "data/",
            "*.tmp"
        ])
        ignore_spec = get_ignore_spec(self.config_manager, self.project_path)
        # Should ignore patterns from both sources
        self.assertTrue(should_ignore(os.path.join(self.project_path, "data", "file.csv"), self.project_path, ignore_spec))
        self.assertTrue(should_ignore(os.path.join(self.project_path, "foo.tmp"), self.project_path, ignore_spec))
        self.assertTrue(should_ignore(os.path.join(self.project_path, "error.log"), self.project_path, ignore_spec))
        self.assertTrue(should_ignore(os.path.join(self.project_path, "build", "main.py"), self.project_path, ignore_spec))
        self.assertFalse(should_ignore(os.path.join(self.project_path, "main.py"), self.project_path, ignore_spec))

    def test_ignore_directories_and_files(self):
        self.write_project_ignore([
            "ignore_this_dir/",
            "ignoreme.txt"
        ])
        ignore_spec = get_ignore_spec(self.config_manager, self.project_path)
        self.assertTrue(should_ignore(os.path.join(self.project_path, "ignore_this_dir", "file.py"), self.project_path, ignore_spec))
        self.assertTrue(should_ignore(os.path.join(self.project_path, "ignoreme.txt"), self.project_path, ignore_spec))
        self.assertFalse(should_ignore(os.path.join(self.project_path, "not_ignored.txt"), self.project_path, ignore_spec))

    def test_ignore_edge_cases(self):
        self.write_project_ignore([
            "nested_dir/ignored_subdir/",
            "**/deeply_ignored.txt",
            "*.bak"
        ])
        # Create nested structure
        os.makedirs(os.path.join(self.project_path, "nested_dir", "ignored_subdir"), exist_ok=True)
        with open(os.path.join(self.project_path, "nested_dir", "ignored_subdir", "deeply_ignored.txt"), "w") as f:
            f.write("test")
        ignore_spec = get_ignore_spec(self.config_manager, self.project_path)
        # Nested ignored directory
        self.assertTrue(should_ignore(os.path.join(self.project_path, "nested_dir", "ignored_subdir", "file.py"), self.project_path, ignore_spec))
        # Glob pattern
        self.assertTrue(should_ignore(os.path.join(self.project_path, "foo.bak"), self.project_path, ignore_spec))
        # Deeply nested file
        self.assertTrue(should_ignore(os.path.join(self.project_path, "nested_dir", "ignored_subdir", "deeply_ignored.txt"), self.project_path, ignore_spec))
        # Not ignored
        self.assertFalse(should_ignore(os.path.join(self.project_path, "nested_dir", "not_ignored.txt"), self.project_path, ignore_spec))

if __name__ == "__main__":
    unittest.main()