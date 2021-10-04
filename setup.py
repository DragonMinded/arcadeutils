import os
from setuptools import setup  # type: ignore


setup(
    name='arcadeutils',
    version='0.1.1',
    description='Collection of utilities written in Python for working with various arcade binaries.',
    long_description='Collection of utilities written in Python for working with various arcade binaries.',
    author='DragonMinded',
    license='Public Domain',
    url='https://github.com/DragonMinded/arcadeutils',
    package_data={"arcadeutils": ["py.typed"]},
    packages=[
        'arcadeutils',
    ],
    install_requires=[
    ],
    python_requires=">=3.6",
)
