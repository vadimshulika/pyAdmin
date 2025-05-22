import os
import sys

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

sys.path.insert(0, os.path.abspath('../../'))

html_theme = 'sphinx_rtd_theme'