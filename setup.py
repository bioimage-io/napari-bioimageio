"""Set up the bioimageio.napari package."""
import json
from pathlib import Path

from setuptools import find_packages, setup

DESCRIPTION = "Describe the bioimageio.napari."

ROOT_DIR = Path(__file__).parent.resolve()
README_FILE = ROOT_DIR / "README.md"
LONG_DESCRIPTION = README_FILE.read_text(encoding="utf-8")
VERSION_FILE = ROOT_DIR / "bioimageio.napari" / "VERSION"
VERSION = json.loads(VERSION_FILE.read_text())["version"]

REQUIRES = ['bioimageio.core','PyYAML']

setup(
    name="bioimageio.napari",
    version=VERSION,
    url="https://github.com/imjoy-team/bioimageio.napari",
    author="ImJoy-Team",
    author_email="imjoy.team@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license="MIT",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
    install_requires=REQUIRES,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet",
    ],
)
