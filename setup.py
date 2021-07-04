from setuptools import setup  # type: ignore


setup(
    name='arcadeutils',
    version='0.1',
    description='Collection of utilities written in Python for working with various arcade binaries.',
    author='DragonMinded',
    license='Public Domain',
    package_data={"arcadeutils": ["py.typed"]},
    packages=[
        'arcadeutils',
    ],
    install_requires=[
        req for req in open('requirements.txt').read().split('\n') if len(req) > 0
    ],
)
