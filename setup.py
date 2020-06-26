"""
Benchmarking for the ISCC library.
"""
from setuptools import find_packages, setup

dependencies = ["click", "isbnlib", "pymarc", "sqlitedict", "lxml"]

setup(
    name="isccbench",
    version="0.1.0",
    license="BSD",
    description="Benchmarking for the ISCC library.",
    long_description=__doc__,
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    install_requires=dependencies,
    entry_points={"console_scripts": ["iscc-bench = iscc_bench.cli:main",],},
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX",
        "Operating System :: MacOS",
        "Operating System :: Unix",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
