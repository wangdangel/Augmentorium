from setuptools import setup, find_packages

setup(
    name="augmentorium",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "watchdog>=2.1.0",
        "chromadb>=0.4.0",
        "tree_sitter>=0.20.0",
        "pyyaml>=6.0",
        "flask>=2.0.0",
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
        "numpy>=1.20.0",
        "tqdm>=4.62.0",
    ],
    entry_points={
    "console_scripts": [
        "augmentorium-indexer=augmentorium.indexer:main",
        "augmentorium-server=augmentorium.server:main",
        "augmentorium-setup=augmentorium.scripts.setup_project:main",
        "augmentorium-grammars=augmentorium.scripts.manage_grammars:main",  # Add this line
    ],
},
    python_requires=">=3.8",
    author="Augmentorium Team",
    author_email="example@example.com",
    description="A code-aware RAG system for LLM access to codebases",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/augmentorium",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
