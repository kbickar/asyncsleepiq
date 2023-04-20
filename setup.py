from setuptools import setup


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="asyncsleepiq",
    packages=["asyncsleepiq", "asyncsleepiq.fuzion"],
    package_data={"asyncsleepiq": ["py.typed"]},
    version="{{VERSION_PLACEHOLDER}}",
    description="ASync SleepIQ API",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="http://github.com/kbickar/asyncsleepiq",
    author="Keilin Bickar",
    author_email="trumpetgod@gmail.com",
    license="MIT",
    install_requires=[
        'aiohttp;python_version>="3.7"',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
)
