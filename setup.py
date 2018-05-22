# -*- coding:utf-8 -*-
import os
import re
try:
    from setuptools import setup, find_packages
except:
    from distutils.core import setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `__init__.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


AUTHOR = "cn"

AUTHOR_EMAIL = "cnaafhvk@foxmail.com"

URL = "https://www.github.com/ShichaoMa/star_builder"

NAME = "star-builder"

DESCRIPTION = "enhance apistar web framework. "

try:
    LONG_DESCRIPTION = open("README.rst").read()
except UnicodeDecodeError:
    LONG_DESCRIPTION = open("README.rst", encoding="utf-8").read()

KEYWORDS = "apistar"

LICENSE = "MIT"

PACKAGES = ["star_builder"]

setup(
    name=NAME,
    version=get_version("star_builder"),
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
    ],
    keywords=KEYWORDS,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    entry_points={
        'console_scripts': [
            'apistar-create = star_builder:main',
        ],
    },
    license=LICENSE,
    packages=PACKAGES,
    install_requires=["apistar"],
    include_package_data=True,
    zip_safe=True,
)