from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='asyncsleepiq',
      packages=['asyncsleepiq'],
      version='0.9.0',
      description='ASync SleepIQ API',
      long_description=readme(),
      url='http://github.com/kbickar/asyncsleepiq',
      author='Keilin Bickar',
      author_email='trumpetgod@gmail.com',
      license='MIT',
      install_requires=[
          'aiohttp;python_version>="3.5"',
      ],
      classifiers = [
          'Programming Language :: Python :: 3',
      ],
)
