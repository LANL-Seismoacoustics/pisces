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

The project also works in a conda environment. For example, create an
optional `environment-dev.yml` with:

```yaml
name: pisces-dev
channels:
  - conda-forge
dependencies:
  - python>=3.11
  - obspy>=1.4.1
  - sqlalchemy>=2
  - click>=8.5,<9
  - oracledb>=26,<27
  - pytest<10
  - myst-parser<6
  - pydata-sphinx-theme<0.24
  - sphinx>=7,<9
  - sphinx-book-theme<2
  - sphinx-click<7
  - numpydoc<2
  - sphinx-autobuild<2026
  - ipython<10
  - e1
  - pip
  - pip:
      - -e ".[dev]"
```

Create it with `conda env create -f environment-dev.yml` and activate it with
`conda activate pisces-dev`. The file is an example rather than a repository
requirement; the repository does not maintain a second environment file.

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
set up the development environment with:

```bash
pixi install -e dev
```

The Pixi tasks run the same commands above without requiring Make:

```bash
pixi run -e dev pytest
pixi run -e dev docs-clean
pixi run -e dev docs-apidocs
pixi run -e dev docs-html
pixi run -e dev docs-serve
```
