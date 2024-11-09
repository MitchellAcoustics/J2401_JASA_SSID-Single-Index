# Repo for "A framework for creating context-dependent soundscape perception indices" submitted to JASA

![Website](https://img.shields.io/website?url=https%3A%2F%2Fdrandrewmitchell.com%2FJ2401_JASA_SSID-Single-Index%2F) This paper is published as a standalone website including the full text, code, and data. You can view it [here](https://drandrewmitchell.com/J2401_JASA_SSID-Single-Index/).

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5550005.svg)](https://doi.org/10.5281/zenodo.5550005)


[![Quarto Publish](https://github.com/MitchellAcoustics/J2401_JASA_SSID-Single-Index/actions/workflows/publish.yml/badge.svg)](https://github.com/MitchellAcoustics/J2401_JASA_SSID-Single-Index/actions/workflows/publish.yml)

`notebooks` contains the Jupyter notebooks used to generate the figures in the paper.

The Quarto manuscript is written and rendered from `index.qmd`, which embeds code outputs from the notebooks. The manuscript is rendered to the `manuscript` folder.

## Reproducing

This repository uses both Python and R code. R functions are implemented within Python using `rpy2`. Upon cloning the repository, you can recreate the Python environment from the `requirements.lock` and `requirements-dev.lock` files, generated by [Rye](https://rye.astral.sh/). The simplest way to do this is to install Rye and use `rye sync`, then activate the venv with `source .venv/bin/activate`. You will need to have R already installed locally, and any needed R packages will be automatically installed when running the notebook.

Alternatively, we provide a Docker configuration contained under `.devcontainer` that can be used to run the notebooks. This should create a completely reproducible container with everything included. This can also be used by [VSCode](https://code.visualstudio.com/docs/devcontainers/containers) or Github Containers to open the repository in a container.
