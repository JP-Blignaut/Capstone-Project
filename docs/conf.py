import os
import sys
sys.path.insert(0, os.path.abspath('../news_addiction'))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Capstone Project'
copyright = '2025, Jacques Blignaut'
author = 'Jacques Blignaut'
release = '00.00.01'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc",
              "sphinx.ext.viewcode",
              "sphinx.ext.napoleon"
            ]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Napoleon settings -------------------------------------------------------
# These control how Google/NumPy docstrings are parsed and displayed

napoleon_google_docstring = True      # Enable support for Google-style docstrings
napoleon_numpy_docstring = False      # Disable NumPy-style if you only use Google
napoleon_use_param = True
napoleon_use_rtype = True


# Point Django to your settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "news_addiction.settings")

# Initialize Django so autodoc can import models, urls, etc.
import django
django.setup()
