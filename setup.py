import setuptools

import sol as project

name = project.__name__
username = "Hellrespawn"
description = "Template for Python projects."
version = project.__version__

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
    entry_points={"console_scripts": [f"{name} = {name}.__main__:main"]},
)
