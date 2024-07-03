# Match and Split tool

The match and split tool provides a GUI to initiate jobs on the server that takes existing text from Internet Archive (or other public domain sources) and automagically matches the text to split it into the correct `Page:` namespace pages.

# Local setup

## Prerequisites

- Python
- NodeJS
- Redis
- MySQL (MariaDB)

## Get it running

### Without Docker

Follow these steps to get the tool running locally
- Set environment variables by copying values from the `.env.tmpl` file into a `.env` file
- Set configuration variables by copying values from the `replica.my.cnf.tmpl` file into a `replica.my.cnf` file. These will be used to access the database.
- Install npm packages using `npm ci`
- Install python packages required for the project from the `requirements.txt` file by running the command `pip install -r requirements.txt`
  > It is recommended to create a python environment for this project before installing Python packages ([more details](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#create-and-use-virtual-environments))
- Before running the project, ensure the following are already running in the background
  - MySQL service
  - Redis service
- Then, run `./scripts/run_dev_env.sh` to see the tool on your browser at `http://0.0.0.0:8000/`

### With Docker

TBA

# Contributing

- Feel free to test the tool out and create a [ticket on phabricator](https://phabricator.wikimedia.org/project/board/7238/) if you find a bug or want to request a feature.
- If you make fixes to the project's codebase/documentation, feel free to raise a Merge Request on the [GitLab repository](https://gitlab.wikimedia.org/toolforge-repos/matchandsplit/) for the project.

