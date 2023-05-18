# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Pisces'
copyright = '2023, Jonathan MacCarthy'
author = 'Jonathan MacCarthy'
release = 'v0.4.2'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

sys.path.insert(0, os.path.abspath('../../pisces'))

# sphinx-apidoc -f -o source/ ../pisces/
# You should see rst files created in the docs/source/ folder

templates_path = ['_templates']
exclude_patterns = ['_cli.rst']

extensions = [
        "sphinx.ext.autodoc",
        "sphinx.ext.autosummary",
        "sphinx.ext.viewcode",
        "sphinx_click",
        "myst_parser",
        # "autodoc2",
        "numpydoc",
        ]
autosummary_generate = False
suppress_warnings = ["myst.header"]
# autodoc2_render_plugin = "myst"
# autodoc2_packages = [
#      {
#          "path": "../../pisces",
#          "exclude_dirs": ["commands"],
#      },
# ]
# suppress_warnings = [
#     "autodoc2.*",  # suppress all
# ]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_static_path = ['_static']
html_css_files = [
    'css/custom.css',
]
html_theme_options = {
    "home_page_in_toc": True,
    "repository_url": "https://github.com/LANL-seismoacoustics/pisces",
    "use_repository_button": True,
    "show_navbar_depth": 2,
    "use_fullscreen_button": False,
    "logo": {
        "image_light": "_static/LANL Logo Ultramarine.png",
        "image_dark": "_static/LANL Logo White.png",
    }
}
html_favicon = "_static/LANL Logo Ultramarine globe.png"