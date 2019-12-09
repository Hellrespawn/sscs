import setuptools

import sol

name = sol.__name__
username = "Hellrespawn"
description = "Template for Python projects."
version = sol.__version__

try:
    with open("README.md", "r") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = description

setuptools.setup(
    name=f"{name}-{username}",
    version=version,
    author="Stef Korporaal",
    author_email="stefkorporaal@gmail.com",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=f"https://github.com/Hellrespawn/{name}",
    packages=setuptools.find_packages(),
    install_requires=["blessed", "mutagen"],
    classifiers=["Programming Language :: Python :: 3",],
    entry_points={
        "console_scripts": [
            f"stodo = sol.cli.stodo:main",
            f"sscs = sol.cli.sscs:main",

        ]
    },
)
