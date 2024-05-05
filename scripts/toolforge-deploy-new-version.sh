#!/usr/bin/env bash
set -ex
toolforge build start https://gitlab.wikimedia.org/toolforge-repos/matchandsplit.git
cd matchandsplit
toolforge webservice restart
toolforge jobs delete mascelery
toolforge jobs load jobs.yaml