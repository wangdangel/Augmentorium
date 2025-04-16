import re
from typing import List, Optional

# Optional: a simple stopword list (can be expanded)
DEFAULT_STOPWORDS = {
    "the", "is", "at", "which", "on", "and", "a", "an", "in", "to", "of", "for", "with", "as", "by", "that", "this", "it", "from", "or", "be", "are", "was", "were", "has", "have", "had", "but", "not", "can", "will", "would", "should", "could"
}

# No longer strip markdown or code blocks; only comments/docstrings will be removed.
def strip_markdown(text: str) -> str:
    return text

def strip_comments_and_docstrings(text: str) -> str:
    # Remove Python docstrings ("""...""" or '''...''')
    text = re.sub(r'("""|\'\'\')(.*?)(\1)', '', text, flags=re.DOTALL)
    # Remove Python single-line comments
    text = re.sub(r'#.*', '', text)
    # Remove C/C++/Java/JS block comments /* ... */
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Remove C/C++/Java/JS single-line comments //
    text = re.sub(r'//.*', '', text)
    return text

def normalize_whitespace(text: str) -> str:
    # Collapse multiple spaces/tabs/newlines, trim
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def remove_stopwords(text: str, stopwords: Optional[set] = None) -> str:
    if stopwords is None:
        stopwords = DEFAULT_STOPWORDS
    tokens = text.split()
    filtered = [t for t in tokens if t not in stopwords]
    return ' '.join(filtered)

def preprocess_text(
    text: str,
    remove_stopwords_flag: bool = False,
    stopwords: Optional[set] = None
) -> str:
    """
    Systematic preprocessing for both documents and queries.
    Steps:
      - Lowercase
      - Remove code comments and docstrings
      - Normalize whitespace
      - (Optional) Remove stopwords (for queries)
    """
    text = text.lower()
    # Do NOT strip markdown or code blocks; only remove comments/docstrings
    text = strip_markdown(text)
    text = strip_comments_and_docstrings(text)
    text = normalize_whitespace(text)
    if remove_stopwords_flag:
        text = remove_stopwords(text, stopwords)
    return text