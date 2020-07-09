# -*- coding: utf-8 -*-

"""
gitgerrit
"""
import versioneer
from pathlib import Path
from setuptools import setup

TOOL_NAME = "gitgerrit"
CWD = Path(__file__).parent

requirements_file = CWD / "requirements.txt"
readme_file = CWD / "README.md"

# Get requirements
with requirements_file.open(encoding="utf-8") as f:
    REQUIREMENTS = f.read().splitlines()

# Get the long description from the README file
with readme_file.open(encoding="utf-8") as f:
    long_description = f.read()

CLASSIFIERS = """
Development Status :: 3 - Alpha
Operating System :: OS Independent
License :: OSI Approved :: Apache Software License
Programming Language :: Python
Programming Language :: Python :: 3
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
""".strip().splitlines()

setup(
    name=f"{TOOL_NAME.lower()}",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Command line tool to interact with gerrit change requests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=f"https://github.com/rasjani/{TOOL_NAME.lower()}",
    author="Jani Mikkonen",
    author_email="jani.mikkonen@gmail.com",
    license="Apache License 2.0",
    classifiers=CLASSIFIERS,
    install_requires=REQUIREMENTS,
    keywords="git gerrit ci",
    platforms="any",
    entry_points={"console_scripts": ["git-gerrit=gitgerrit:main"], },
    packages=[TOOL_NAME],
)
