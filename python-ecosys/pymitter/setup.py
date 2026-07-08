# coding: utf-8


import os
from setuptools import setup

import pymitter


this_dir = os.path.dirname(os.path.abspath(__file__))

keywords = [
    "event",
    "emitter",
    "eventemitter",
    "wildcard",
    "node",
    "nodejs",
]

classifiers = [
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Development Status :: 5 - Production/Stable",
    "Operating System :: OS Independent",
    "License :: OSI Approved :: BSD License",
    "Intended Audience :: Developers",
]

# read the readme file
with open(os.path.join(this_dir, "README.md"), "r") as f:
    long_description = f.read()

# load installation requirements
with open(os.path.join(this_dir, "requirements.txt"), "r") as f:
    install_requires = [line.strip() for line in f.readlines() if line.strip()]

setup(
    name=pymitter.__name__,
    version=pymitter.__version__,
    author=pymitter.__author__,
    author_email=pymitter.__author_email__,
    description=pymitter.__doc__.strip().split("\n")[0].strip(),
    license=pymitter.__license__,
    url=pymitter.__contact__,
    keywords=keywords,
    classifiers=classifiers,
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4",
    zip_safe=False,
    py_modules=[pymitter.__name__],
)
