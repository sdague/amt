#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'appdirs',
    'requests'
]

test_requirements = [
    'mock'
    # TODO: put package test requirements here
]

setup(
    name='amt',
    version='0.4.0',
    description="Tools for interacting with Intel's AMT",
    long_description=readme + '\n\n' + history,
    author="Sean Dague",
    author_email='sean@dague.net',
    url='https://github.com/sdague/amt',
    packages=[
        'amt',
    ],
    package_dir={'amt':
                 'amt'},
    scripts=['bin/amtctrl'],
    include_package_data=True,
    install_requires=requirements,
    license="Apache",
    zip_safe=False,
    keywords='amt',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
