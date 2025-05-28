import os
import sys

# -- Project information -----------------------------------------------------
project = 'pyAdmin'
copyright = '2025, Shulika Vadim'
author = 'Shulika Vadim'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]
sys.path.insert(0, os.path.abspath('../../'))

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_title = 'pyAdmin Documentation'
html_short_title = 'pyAdmin'
html_theme_options = {
    'collapse_navigation': False,
    'sticky_navigation': True,
}



