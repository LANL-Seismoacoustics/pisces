
# Installation

Requires:

* NumPy
* SciPy
* ObsPy
* SQLAlchemy>=2
* Click

For Oracle database connections, install the appropriate SQLAlchemy DBAPI
driver separately; the development environment includes `oracledb` for testing.

There are multiple ways Pisces can be installed.

Install from [PyPI](https://pypi.python.org/pypi):
```bash
pip install pisces
```

Optionally, include a plugin to read the [`e1`](https://github.com/LANL-Seismoacoustics/e1) data format:
```bash
pip install pisces[e1]
```

Install current main from GitHub:
```bash
pip install git+https://github.com/LANL-seismoacoustics/pisces
```
