#!/usr/bin/env python

from setuptools import setup

setup(
    name="auto-selfcontrol",
    version="1.0",
    description="Small utility to schedule start and stop times of SelfControl",
    url="github.com/cmnord/auto-selfcontrol",
    long_description=open("README.md").read(),
    install_requires=["pyobjc", "pyobjc-core"],
)
