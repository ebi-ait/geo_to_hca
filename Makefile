setup:
	pip install -r requirements-dev.txt

dist:
	python setup.py sdist

publish:
	twine upload dist/*

clean:
	rm -rf dist/ output/ *.egg-info/