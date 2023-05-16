# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Pisces'
copyright = '2023, Jonathan MacCarthy'
author = 'Jonathan MacCarthy'
release = 'v0.4.2'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


templates_path = ['_templates']
exclude_patterns = []

extensions = [
        "myst_parser",
        "autodoc2",
        # "sphinx.ext.autodoc",
        "sphinx.ext.viewcode",
        # "numpydoc",
        ]
autodoc2_render_plugin = "myst"
autodoc2_packages = [
     {
         "path": "../../pisces",
         "exclude_dirs": ["commands"],
     },
]
suppress_warnings = [
    "autodoc2.*",  # suppress all
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_static_path = ['_static']
html_css_files = [
    'css/custom.css',
]
html_theme_options = {
    "repository_url": "https://github.com/LANL-seismoacoustics/pisces",
    "use_repository_button": True,
    "show_navbar_depth": 2,
    "logo": {
        "image_light": "_static/LANL Logo Ultramarine.png",
        "image_dark": "_static/LANL Logo White.png",
    }
}