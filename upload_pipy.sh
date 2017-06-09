rm -rf astrosimon.egg-info
rm -rf build
rm -rf dist
python setup.py register -r pypi
python setup.py sdist upload -r pypi