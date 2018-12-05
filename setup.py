#! /usr/bin/env python3

# Core
from setuptools import setup, find_packages

setup(
    name='canonicalwebteam.django_views',
    version='1.3.2',
    author='Canonical webteam',
    author_email='webteam@canonical.com',
    url='https://github.com/canonicalwebteam/django_views',
    packages=find_packages(),
    description=(
        "Shared Django views for use in Webteam apps"
    ),
    long_description=open('README.rst').read(),
    install_requires=[
        "mistune",
        "python-frontmatter",
        "django",
    ],
    tests_require=["Django"],
    test_suite="tests",
)
