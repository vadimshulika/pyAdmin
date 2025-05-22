from setuptools import setup, find_packages

setup(
    name="pyAdmin",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["psutil"],
    python_requires=">=3.8",
)