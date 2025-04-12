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

if __name__ == "__main__":
    unittest.main()