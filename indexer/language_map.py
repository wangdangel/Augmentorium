import os

# Path to the tree_sitter_language_pack bindings directory
BINDINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    ".venv", "Lib", "site-packages", "tree_sitter_language_pack", "bindings"
)

# Broad mapping of file extensions to language names (expand as needed)
EXTENSION_LANGUAGE_CANDIDATES = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "c_sharp",
    ".sh": "bash",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".markdown": "markdown",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".m": "objc",
    ".mm": "objc",
    ".pl": "perl",
    ".r": "r",
    ".scala": "scala",
    ".lua": "lua",
    ".dart": "dart",
    ".sql": "sql",
    ".xml": "xml",
    ".toml": "toml",
    ".ini": "ini",
    ".vim": "vim",
    ".vue": "vue",
    ".svelte": "svelte",
    ".scss": "scss",
    ".less": "less",
    ".hcl": "hcl",
    ".tf": "terraform",
    ".proto": "proto",
    ".asm": "asm",
    ".bat": "batch",
    ".ps1": "powershell",
    ".erl": "erlang",
    ".ex": "elixir",
    ".exs": "elixir",
    ".elm": "elm",
    ".clj": "clojure",
    ".cljs": "clojure",
    ".groovy": "groovy",
    ".f90": "fortran",
    ".f95": "fortran",
    ".f03": "fortran",
    ".f08": "fortran",
    ".f": "fortran",
    ".fs": "fsharp",
    ".fsx": "fsharp",
    ".ml": "ocaml",
    ".mli": "ocaml_interface",
    ".v": "verilog",
    ".sv": "verilog",
    ".vhd": "vhdl",
    ".vhdl": "vhdl",
    ".zig": "zig",
    ".nim": "nim",
    ".jl": "julia",
    ".coffee": "coffee",
    ".purs": "purescript",
    ".hs": "haskell",
    ".hx": "haxe",
    ".rkt": "racket",
    ".scm": "scheme",
    ".lisp": "commonlisp",
    ".lsp": "commonlisp",
    ".bib": "bibtex",
    ".tex": "latex",
    ".org": "org",
    ".rst": "rst",
    ".bat": "batch",
    ".ps1": "powershell",
    ".cfg": "ini",
    ".conf": "ini",
    ".csv": "csv",
    ".tsv": "tsv",
    ".psv": "psv",
    ".po": "po",
    ".ron": "ron",
    ".ronn": "ron",
    ".pgn": "pgn",
    ".gd": "gdscript",
    ".gdscript": "gdscript",
    ".qml": "qmljs",
    ".qmljs": "qmljs",
    ".prisma": "prisma",
    ".smithy": "smithy",
    ".sol": "solidity",
    ".smt2": "smt2",
    ".wgsl": "wgsl",
    ".yuck": "yuck",
    ".uxntal": "uxntal",
    ".typ": "typst",
    ".mermaid": "mermaid",
    ".astro": "astro",
    ".bicep": "bicep",
    ".capnp": "capnp",
    ".clar": "clarity",
    ".cmake": "cmake",
    ".dockerfile": "dockerfile",
    ".dtd": "dtd",
    ".fish": "fish",
    ".gleam": "gleam",
    ".glsl": "glsl",
    ".hack": "hack",
    ".hcl": "hcl",
    ".janet": "janet",
    ".kdl": "kdl",
    ".latex": "latex",
    ".linkerscript": "linkerscript",
    ".llvm": "llvm",
    ".magik": "magik",
    ".make": "make",
    ".meson": "meson",
    ".ninja": "ninja",
    ".nix": "nix",
    ".odin": "odin",
    ".pas": "pascal",
    ".pem": "pem",
    ".pony": "pony",
    ".psv": "psv",
    ".puppet": "puppet",
    ".qmldir": "qmldir",
    ".ron": "ron",
    ".smithy": "smithy",
    ".sparql": "sparql",
    ".starlark": "starlark",
    ".svelte": "svelte",
    ".tablegen": "tablegen",
    ".tcl": "tcl",
    ".thrift": "thrift",
    ".twig": "twig",
    ".ungrammar": "ungrammar",
    ".v": "verilog",
    ".wgsl": "wgsl",
    ".xcompose": "xcompose",
    ".yuck": "yuck",
    ".zig": "zig",
}

def get_available_languages():
    langs = set()
    if os.path.exists(BINDINGS_PATH):
        for fname in os.listdir(BINDINGS_PATH):
            if fname.endswith('.pyd') and not fname.startswith('__'):
                langs.add(os.path.splitext(fname)[0])
    return langs

# Build the dynamic mapping at import time
AVAILABLE_LANGUAGES = get_available_languages()
EXTENSION_TO_LANGUAGE = {
    ext: lang for ext, lang in EXTENSION_LANGUAGE_CANDIDATES.items()
    if lang in AVAILABLE_LANGUAGES
}