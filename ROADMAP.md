# TODO


## finish and clean FDSN format support

1. [ ] complete `inventory.py`. merge Inventory creation branch from cgammans
2. [ ] better integrate instrument response file format reading/writing.  look at api_ideas.md for possible organization.
3. [ ] Add deeper layers (amplitudes, picks, etc.) to `catalog.py`.  May need improvements in `events.py`
4. [ ] integrate the above changes into `fdsn.py:Client`
5. [ ] clean/simplify logic in `catalog.py`.

## Better table querying API

6. [ ] Current `filter_*` functions in `events.py`, `stations.py`, and `waveforms.py` don't compose as elegantly as I'd like.  

## IO submodules API improvements/changes/deprecations

7. [ ] needs a better internal API and a plugin system
8. [ ] should contain instrument response file code.  see `api_ideas.md`
9. [ ] `io.sac` has redundant and unoptimized code.  should rely more on obspy.io.sac functionality.



## Misc

10. [ ] Move to pyproject.toml and setuptools for project management.
11. [ ] Move to pixi and use pyproject.toml for developement.
    - use a "dev" pixi environment with a pixi.toml, and don't use pixi "features" to define it.  define dev directly.
12. [x] Move `test_events.py` fixtures to `conftest.py`
13. [ ] Add tests in `test_events.py` that look for cartesian joins when cascading filter function outputs.
14. [ ] Replace event test data in `test_fdsn.py` with event data fixture in `conftest.py`, or AI generated data
15. [ ] Adding type hints
16. [ ] linting with ruff
