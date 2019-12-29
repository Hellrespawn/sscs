import setuptools

import sol

NAME = sol.__name__
USERNAME = "Hellrespawn"
DESCRIPTION = "Template for Python projects."
VERSION = sol.__version__

try:
    with open("README.md", "r") as fh:
        LONG_DESCRIPTION = fh.read()
except FileNotFoundError:
    LONG_DESCRIPTION = DESCRIPTION

setuptools.setup(
    name=f"{NAME}-{USERNAME}",
    version=VERSION,
    author="Stef Korporaal",
    author_email="stefkorporaal@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url=f"https://github.com/Hellrespawn/{NAME}",
    packages=setuptools.find_packages(),
    install_requires=["cliapp-Hellrespawn"],
    classifiers=["Programming Language :: Python :: 3"],
    entry_points={
        "console_scripts": [
            f"stodo = sol.cli.stodo.stodo:main",
            f"sscs = sol.cli.sscs:main",
        ]
    },
)
