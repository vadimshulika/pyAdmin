# Добавьте пути к коду, чтобы Sphinx видел ваш пакет
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))  # Путь к корню проекта

# Включите поддержку Google-style docstrings
extensions = [
    'sphinx.ext.autodoc',      # Автогенерация из docstrings
    'sphinx.ext.napoleon',     # Поддержка Google-style
]

# Укажите тему (например, 'alabaster' или 'sphinx_rtd_theme')
html_theme = 'alabaster'