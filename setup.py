from setuptools import setup
import asyncsleepiq

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='asyncsleepiq',
      packages=['asyncsleepiq'],
      package_data={'asyncsleepiq': ['py.typed']},
      version=asyncsleepiq.__version__,
      description='ASync SleepIQ API',
      long_description=readme(),
      long_description_content_type="text/markdown",
      url='http://github.com/kbickar/asyncsleepiq',
      author='Keilin Bickar',
      author_email='trumpetgod@gmail.com',
      license='MIT',
      install_requires=[
          'aiohttp;python_version>="3.7"',
      ],
      classifiers = [
          'Programming Language :: Python :: 3',
      ],
)
