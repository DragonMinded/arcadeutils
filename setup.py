import os
from setuptools import setup  # type: ignore


with open(os.path.join("arcadeutils", "README.md"), "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name='arcadeutils',
    version='0.1.10',
    description='Collection of utilities written in Python for working with various arcade binaries.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='DragonMinded',
    author_email='dragonminded@dragonminded.com',
    license='Public Domain',
    url='https://github.com/DragonMinded/arcadeutils',
    package_data={"arcadeutils": ["py.typed", "README.md"]},
    packages=[
        'arcadeutils',
    ],
    install_requires=[
        'typing-extensions',
    ],
    python_requires=">=3.6",
)
