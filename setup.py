import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="imperial-painter",
    version="1.0.0",
    include_package_data=True,
    packages=setuptools.find_packages(),

    install_requires=[
        'django>=1.11.20',
        'django-extensions>=2.1.6',
        'django-jsonfield>=1.1.0',
        'dj_database_url>=0.3.0',
        'lxml>=4.3.3',
        'openpyxl>=2.6.2',
        'psycopg2>=2.8.1',
    ],

    author="Adam Thomas",
    author_email="sortoflikechess@gmail.com",
    description="A tool for generating prototype cards from Excel files and Django templates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adam-thomas/imperial-painter",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)