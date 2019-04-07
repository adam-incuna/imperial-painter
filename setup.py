import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="imperial-painter-adam-thomas",
    version="1.0.0",
    author="Adam Thomas",
    author_email="sortoflikechess@gmail.com",
    description="A tool for generating prototype cards from Excel files and Django templates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adam-thomas/imperial-painter",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)