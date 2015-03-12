# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''


setup(
    name="yadic",
    version="0.1.12.4",
    license='MIT',
    description=read('DESCRIPTION'),
    author="Aleksey Pirogov",
    author_email="tempor@inbox.ru",
    url="https://bitbucket.org/astynax/yadic",
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    long_description=read('README'),
)
