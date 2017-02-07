# Contributing

Please contribute! Every little bit helps, and credit will always be given. 

# Ways to Contribute

* Filing an Issue  
    https://github.com/jkmacc-LANL/pisces/issues
* Bug Reports
    - Detailed steps to reproduce the bug.  
    - Your operating system name and version.
    - Any details about your local setup that might be helpful in troubleshooting.  
* Feature Request
    - Explain in detail how it would work.
    - Keep the scope as narrow as possible, to make it easier to implement.
    - Remember that this is a volunteer-driven project, and that contributions are welcome :)
* Submit a Pull Request
* Write Documentation  
    https://jkmacc-lanl.github.io/pisces/

# How to Submit a Pull Request

Here's how to set up `pisces` for local development and contributing changes.
Please see the project Wiki for a description of the git branching model.

1. If you don't yet have collaborator permissions, fork the `pisces` repo on GitHub.
2. Clone the repo locally.
    * On a GitHub fork:
    ```
    $ git clone git@github.com:your_name_here/pisces.git
    ```
    * On a different remote, use the appropriate URL.

3. Install your local copy into an environment for isolated development.
    * using `virtualenv` (assuming you have `virtualenvwrapper` installed):
    ```
    $ mkvirtualenv pisces
    $ cd pisces/
    $ pip install obspy lxml Click
    $ pip install -e .
    ```
    * using `conda`
    ```
    $ conda create -n pisces -c obspy obspy lxml Click
    $ cd pisces/
    $ pip install -e .
    ```

4. Create a branch for local development.  
**Note**: if you're an internal developer, start from the `next_internal` branch
    * For new functionality:
    ```
    $ git checkout -b name-of-your-bugfix-or-feature origin/next
    ```
    * For fixes and reorganizations:
    ```
    $ git checkout -b name-of-your-bugfix-or-feature origin/master
    ```

5. Commit your changes and push your branch to the remote.
    ```
    $ git add <the_file_you_changed> <other_files_you_changed>
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature
    ```

6. Submit a pull/merge request through the repository website.
