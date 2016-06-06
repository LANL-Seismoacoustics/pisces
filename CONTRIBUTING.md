# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given. 

You can contribute in many ways:


# Filing an Issue

Report bugs or feature requests at https://github.com/jkmacc-LANL/pisces/issues.

## Bug Report
If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

## Feature Request
If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)


# Submit a Pull Request

We love contributions!


## Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.


## Implement Features

Look through the GitHub issues for features. Anything tagged with "feature"
is open to whoever wants to implement it.

## Write Documentation

Pisces could always use more documentation, whether as part of the 
official Pisces docs, in docstrings, or even on the web in blog posts,
articles, and such.


# Get Started!

Ready to contribute? Here's how to set up `pisces` for local development.

1. Fork the `pisces` repo on GitHub.
2. Clone your fork locally:

    $ git clone git@github.com:your_name_here/pisces.git

3. Install your local copy into an environment
   
   * virtualenv: assuming you have virtualenvwrapper installed, this is how you set up your fork for local development:

```
    $ mkvirtualenv pisces
    $ cd pisces/
    $ pip install -e .
```

   * conda: assuming you have conda installed, this is how you set up your fork for local development:

```
    $ conda create -n pisces
    $ cd pisces/
    $ pip install -e .
```

4. Create a branch for local development::

```
    $ git checkout -b name-of-your-bugfix-or-feature
```
   
   Now you can make your changes locally.

5. Commit your changes and push your branch to GitHub:

```
    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature
```

6. Submit a pull request through the GitHub website.
