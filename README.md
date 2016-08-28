![un-project.org](http://un-project.org/static/img/logo-large.png)
----
[un-project.org](http://un-project.org) aggregates and analyzes data from the United Nations. It is based on the [Arguman](http://arguman.org) [mapping](https://en.wikipedia.org/wiki/Argument_map) platform.

## Run un-project on your local

- Fetch repository by `git clone git@github.com:un-project/un-project.org.git`
- Make sure you have [docker](http://docker.io) and [docker-compose](https://docs.docker.com/compose/install/) installed and working
- create `settings_local.py` from `settings_local.py.ex` under `main` folder
- if you are using docker-machine or running docker on vagrant make sure you set proper addresses on `settings_local.py`
- run `docker-compose up` under main project directory where `docker-compose.yml` is

## Thanks To

[Arguman.org](http://arguman.org)