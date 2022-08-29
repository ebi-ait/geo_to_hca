TOOL_NAME := geo_to_hca
SRC_FILES := $(shell find $(TOOL_NAME) -name \*.py -print)

.PHONY: setup
setup:
	pip install -r requirements-dev.txt

dist: setup.py $(SRC_FILES)
	python setup.py sdist

publish: dist
	twine  upload \
		--verbose \
		--comment "release $(TOOL_NAME)" \
		dist/*

clean:
	rm -rf dist/ output/ *.egg-info/