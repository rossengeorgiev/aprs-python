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
	pip install -r dev_requirements.txt

test:
	rm -f .coverage aprslib/*.pyc tests/*.pyc
	PYTHONHASHSEED=0 pytest --tb=short --cov-config .coveragerc --cov=aprslib tests

pylint:
	pylint -r n -f colorized aprslib || true

build: pylint test docs

.FORCE:
docs: .FORCE
	$(MAKE) -C docs html

clean:
	rm -rf dist aprs.egg-info aprslib/*.pyc test/*.pyc .coverage

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel --universal

upload: dist
	twine upload -r pypi dist/*
