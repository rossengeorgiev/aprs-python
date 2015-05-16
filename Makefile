# Makefile for APRS module

define HELPBODY
Available commands:

	make help       - this thing.
	make init       - install python dependancies
	make test       - run tests and coverage
	make pylint     - code analysis
	make build      - pylint + test

endef

verbosity=1

export HELPBODY
help:
	@echo "$$HELPBODY"

init:
	pip install -r req.txt

test:
	rm -f aprslib/*.pyc
	nosetests --verbosity $(verbosity) --with-coverage --cover-package=aprslib

pylint:
	pylint -r n -f colorized aprslib || true

build: pylint test

clean:
	rm -rf dist aprs.egg-info aprslib/*.pyc test/*.pyc .coverage

dist: clean
	python setup.py sdist

upload: dist
	python setup.py register -r pypi
	twine upload -r pypi dist/*
