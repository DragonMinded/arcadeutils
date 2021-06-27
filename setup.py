from setuptools import setup


setup(
    name='arcadeutils',
    version='0.1',
    description='Collection of utilities written in Python for working with various arcade binaries.',
    author='DragonMinded',
    license='Public Domain',
    packages=[
        'arcadeutils',
    ],
    install_requires=[
        req for req in open('requirements.txt').read().split('\n') if len(req) > 0
    ],
)
