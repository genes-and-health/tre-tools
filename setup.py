import os

from setuptools import find_namespace_packages, setup

with open(os.path.join("tretools", "VERSION")) as f:
    version = f.read().strip()

setup(
    name="tretools",
    version=version,
    packages=find_namespace_packages(exclude=["tests"]),
    include_package_data=True,
    url="https://github.com/genes-and-health/tre-tools",
    description="Tools for working with the Genes and Health Trusted Research Environment",
    author="Caroline Morton",
    author_email="c.morton@qmul.ac.uk",
    python_requires=">=3.8",
    install_requires=["polars == 0.19.9", "setuptools"],
)
