# How to build the API docs and put them into the mkdocs pages.

1. Make sure the package is visible to your python

```bash
export PYTHONPATH=~/python/pisces/
```

Also make sure you've installed numpydoc: `pip install numpydoc`


2. Automatically build the API .rst source files

This command will overwrite `conf.py` and `Makefile`:
```bash
sphinx-apidoc -d 2 -f -F -E -e -A 'Jonathan MacCarthy' -V 0.2 -H pisces -o . ~/python/pisces/pisces ~/python/pisces/pisces/io/flatfile.py
```

This command will not:
```bash
sphinx-apidoc -f -e -E -A 'Jonathan MacCarthy' -V 0.2.1 -H pisces -o . ~/python/pisces/pisces ~/python/pisces/pisces/io/flatfile.py
```


3. Add numpydoc to bottom of extension list in `conf.py`

```python
extensions = [                                                                                      
  1     'sphinx.ext.autodoc',                                                                           
  2     'sphinx.ext.viewcode',                                                                          
  3     'sphinx.ext.intersphinx',                                                                       
  4     'sphinx.ext.autosummary',                                                                       
  5     'numpydoc'                                                                                      
  6 ]    
```

4. Remove .rst files for modules you don't want to be documented.

Add this to Contents in index.rst:

```
.. toctree::                                                                                           
   :maxdepth: 4                                                                                        
                                                                                                       
   pisces    
```


4. Make the html and move it into the mkdocs 'api' folder, overwriting its `index.html`.

```bash
#make clean
make html
cp -r _build/html/* ~/python/pisces/docs/html/api/
```

