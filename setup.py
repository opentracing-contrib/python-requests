#!/usr/bin/env python
from setuptools.command.test import test as TestCommand
from setuptools import setup, find_packages
import sys
import os


class PyTest(TestCommand):

    user_options = []

    def initialize_options(self):
        TestCommand.initialize_options(self)

    def run_tests(self):
        import pytest
        sys.exit(pytest.main('tests'))


cwd = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(cwd, 'requirements.txt')) as requirements_file:
    requirements = requirements_file.read().splitlines()

with open(os.path.join(cwd, 'README.rst')) as readme_file:
    long_description = readme_file.read()

# Keep these separated for tox extras
test_requirements = ['mock', 'pytest']
integration_test_requirements = ['docker']

setup(
    name='Requests-OpenTracing',
    version='0.0.1',
    url='http://github.com/signalfx/python-requests',
    download_url='http://github.com/signalfx/python-requests/tarball/master',
    author='SignalFx, Inc.',
    author_email='info@signalfx.com',
    description='OpenTracing support for Requests',
    long_description=long_description,
    packages=find_packages(),
    platforms='any',
    license='Apache Software License v2',
    classifiers=[
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'Natural Language :: English',
      'License :: OSI Approved :: Apache Software License',
      'Programming Language :: Python',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 2.7',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.4',
      'Programming Language :: Python :: 3.5',
      'Programming Language :: Python :: 3.6',
    ],
    install_requires=requirements,
    tests_require=test_requirements + integration_test_requirements,
    extras_require=dict(
        unit_tests=test_requirements,
        integration_tests=test_requirements + integration_test_requirements
    ),
    cmdclass=dict(test=PyTest)
)
