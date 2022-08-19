SRC_FILES := $(shell find geo_to_hca -name \*.py -print)

.PHONY: setup
setup:
	pip install -r requirements-dev.txt

dist: setup.py $(SRC_FILES)
	python setup.py sdist

publish:
	twine upload dist/*

clean:
	rm -rf dist/ output/ *.egg-info/