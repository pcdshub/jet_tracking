#!/usr/bin/env python3
#
# PCDS Devices documentation build configuration file, created by
# sphinx-quickstart on Mon Apr  3 21:34:53 2017.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import datetime
import os
import sys

import sphinx_rtd_theme

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../")
sys.path.insert(0, module_path)

import jet_tracking  # isort: skip # noqa: E402


# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    # jquery removed in sphinx 6.0 and used in docs_versions_menu.
    # See: https://www.sphinx-doc.org/en/master/changes.html
    "sphinxcontrib.jquery",
    "docs_versions_menu",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

autosummary_generate = True

# numpydoc_class_members_toctree = True
# numpydoc_show_class_members = False

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "PCDS Jet Tracking"
year = datetime.datetime.now().year
copyright = f"{year}, SLAC National Accelerator Laboratory"
author = "SLAC National Accelerator Laboratory"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = str(jet_tracking.__version__)
# The full version, including alpha/beta/rc tags.
release = str(jet_tracking.__version__)

rtd_version = getattr(sphinx_rtd_theme, "__version__", "unknown")
print(f"Version: {version} using sphinx_rtd_theme version: {rtd_version}")
# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# The reST default role (used for this markup: `text`)
default_role = "any"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']
html_static_path = []

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = True

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "jet_trackingdoc"


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        "jet_tracking.tex",
        "PCDS Jet Tracking Documentation",
        "SLAC National Accelerator Laboratory",
        "manual",
    ),
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, "jet_tracking", "PCDS Jet Tracking Documentation", [author], 1)
]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "jet_tracking",
        "PCDS Jet Tracking Documentation",
        author,
        "jet_tracking",
        "Liquid jet positioning feedback and tracking.",
        "Miscellaneous",
    ),
]

# -- Sources of external documentation to cross-referencing----------------

intersphinx_mapping = {
    "ophyd": ("https://blueskyproject.io/ophyd", None),
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
}
