#!/usr/bin/env python3
import os
from setuptools import setup, find_packages
here = os.path.abspath(os.path.dirname(__file__))

NAME = 'socmap'
DESCRIPTION = 'Build maps of Twitter communities'
URL = 'https://github.com/DaylightingSociety/socmap'
EMAIL = 'socmap@daylightingsociety.org'
AUTHOR = 'Daylighting Society'
VERSION = '0.1.0'

install_requires = [
	"tweepy",
	"networkx",
	"jsonpickle",
	]

setup(
	name=NAME,
	version=VERSION,
	description=DESCRIPTION,
	author=AUTHOR,
	author_email=EMAIL,
	url=URL,
	install_requires=install_requires
)
