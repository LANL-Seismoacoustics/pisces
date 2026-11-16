# Contributing

## Python environment

Pisces can be developed with any Python environment, including `venv`, `conda`,
or `pixi` (preferred, see final section). The commands below use a virtual
environment and pip, and are the canonical development instructions. From the
repository root:

```bash
python -m venv .venv
. .venv/bin/activate                 # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The project also works in a conda environment. To use the equivalent
development environment, copy the following into a file such as
`environment-dev.yml`:

```yaml
name: pisces-dev
channels:
  - conda-forge
dependencies:
  - python>=3.11
  - numpy
  - obspy>=1.4.1
  - scipy
  - sqlalchemy>=2
  - click
  - oracledb
  - e1
  - pytest
  - myst-parser
  - pydata-sphinx-theme
  - sphinx
  - sphinx-book-theme
  - sphinx-click
  - numpydoc
  - sphinx-autobuild
  - pip
  - pip:
      - -e . --no-deps
```

Create it with `conda env create -f environment-dev.yml` and activate it with
`conda activate pisces-dev`. The Pixi environment is the primary development
setup, but this example keeps Conda-based development equivalent.

## Tests

Run the test suite with pytest:

```bash
pytest -v
```

## Documentation

From the repository root, change into `docs/` and generate API sources and
build the HTML documentation with the Sphinx commands directly:

```bash
cd docs
sphinx-build -M clean source build
rm -rf source/apidocs
sphinx-apidoc -d 2 -Mef -t templates -o source/apidocs ../pisces
cat source/_cli.rst >> source/apidocs/pisces.commands.rst
sphinx-build -M html source build
```

For a live-reloading documentation server, run this from `docs/`:

```bash
sphinx-autobuild source build
```

If Make is installed, the [`docs/Makefile`](docs/Makefile) provides equivalent
shortcuts. Run these Make commands from inside `docs/`:

```bash
make clean
make apidocs
make html
make livehtml
```

## Pixi (optional, preferred)

Pixi is the preferred way to reproduce the project’s development and CI
environments, but it is not required for contributors. After installing Pixi,
set up the default development environment with:

```bash
pixi install
```

The Pixi tasks run the same commands above without requiring Make:

```bash
pixi run pytest
pixi run docs-clean
pixi run docs-apidocs
pixi run docs-html
pixi run docs-serve
```

The `py311`, `py312`, `py313`, and `py314` environments provide the same
development environment with a fixed Python version for testing. For optional
interactive development, the `jupyter` environment also provides IPython and
JupyterLab:

```bash
pixi shell -e jupyter
```

These Pixi environments are for developing the checkout. To use a released
Pisces package, install it with pip or add `pisces` to your own Pixi project.
