import os
from setuptools import setup, find_packages
here = os.path.abspath(os.path.dirname(__file__))

intall_requires = [
	"tweepy",
	"networkx",
	"jsonpickle",
	]

setup(name="SocMap",
	install_requires=install_requires
	)
