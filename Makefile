SHELL := /bin/bash
verbosity=1

help:
	@echo "Usage:"
	@echo " make help      -- display this help"
	@echo " make install   -- install requirements and set up the database"
	@echo " make test      -- run tests"
	@echo " make paint     -- run imperial-painter at 127.0.0.1:8000"

install:
	pip install -r requirements.txt
	if [ `psql -t -c "SELECT COUNT(1) FROM pg_catalog.pg_database WHERE datname = 'painter'"` -eq 0 ]; then \
		psql  -c "CREATE DATABASE painter"; \
	fi
	python manage.py migrate

test:
	@coverage run manage.py test --keepdb --verbosity=$(verbosity)
	@coverage report -m

paint:
	@python manage.py runserver
