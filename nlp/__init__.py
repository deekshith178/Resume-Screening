"""NLP resume intake package.

This package contains multiple implementations and helpers around resume
parsing and normalization. To keep imports lightweight (and avoid loading
heavy models like SBERT on simple `import nlp`), submodules are imported
explicitly where needed instead of being re-exported here.
"""

__all__: list[str] = []
