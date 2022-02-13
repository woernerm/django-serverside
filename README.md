# Django-Serverside
![build](data/badges/build.svg)
![test](data/badges/test.svg)
![coverage](data/badges/test_coverage.svg)
![doc coverage](data/badges/doc_coverage.svg)
![vulnerabilities](data/badges/vulnerabilities.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This is an app for [Django](https://www.djangoproject.com/) that allows you to create
database users directly from Django's admin interface. This is useful for data science
applications. For example, allowing privileged users to query data using analysis tools
like [Matlab](www.mathworks.com) or 
[Excel](https://www.microsoft.com/de-de/microsoft-365/excel). They can then use SQL for
advanced database queries for scientific analysis.  

## Installation
The project is an early development phase. It is not yet available in the
[Python Package Index](https://pypi.org/). However, you can install it from github
using:
```Shell
python -m pip install git+https://github.com/woernerm/django-serverside.git
```