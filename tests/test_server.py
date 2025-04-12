import unittest
from utils.text_preprocessing import preprocess_text, DEFAULT_STOPWORDS

class TestQueryPreprocessing(unittest.TestCase):
    def test_lowercase_and_whitespace(self):
        text = "  This   is   a   TEST.  "
        expected = "this is a test."
        self.assertEqual(preprocess_text(text), expected)

    def test_code_blocks_and_inline_code_preserved(self):
        text = "# Heading\nSome text. `inline_code()` and\n```\ndef foo():\n    pass\n```\n"
        # Comments and docstrings are not present, so all code should be preserved, markdown not stripped
        expected = "# heading some text. `inline_code()` and ``` def foo(): pass ```"
        # Normalize whitespace and lowercase, but keep code and markdown
        self.assertEqual(preprocess_text(text), expected)

    def test_comment_and_docstring_removal(self):
        text = '"""Docstring"""\n# Comment\nCode line\n// JS comment\n/* block comment */'
        expected = "code line"
        self.assertEqual(preprocess_text(text), expected)

    def test_stopword_removal(self):
        text = "This is a test of the stopword removal system."
        expected = "test stopword removal system."
        self.assertEqual(
            preprocess_text(text, remove_stopwords_flag=True, stopwords=DEFAULT_STOPWORDS),
            expected
        )

    def test_markdown_not_stripped(self):
        text = "# Heading\nSome text with [link](url) and ![img](url)"
        # Only lowercase and whitespace normalization, markdown remains
        expected = "# heading some text with [link](url) and ![img](url)"
        self.assertEqual(preprocess_text(text), expected)

    def test_identical_for_document_and_query(self):
        doc = "## Title\nSome code: `x = 1` # comment"
        query = "## Title\nSome code: `x = 1` # comment"
        # Should be identical after preprocessing (no stopword removal)
        self.assertEqual(preprocess_text(doc), preprocess_text(query))

    def test_stopword_removal_configurable(self):
        text = "This is a test of the stopword removal system."
        with_stop = preprocess_text(text, remove_stopwords_flag=True)
        without_stop = preprocess_text(text, remove_stopwords_flag=False)
        self.assertNotEqual(with_stop, without_stop)

if __name__ == "__main__":
    unittest.main()