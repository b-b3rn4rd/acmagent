import os
import io
import acmagent
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='acmagent',
    version=acmagent.VERSION,
    description='ACM agent - automates ACM certificates',
    long_description=long_description,
    url='https://github.com/b-b3rn4rd/acmagent',
    author='Bernard Baltrusaitis',
    test_suite="tests",
    tests_require=['mock'],
    author_email='bernard@runawaylover.info',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Environment :: Console'
    ],
    keywords='acm aws ssl certificates',
    packages=find_packages(exclude=['docs', 'tests']),
    install_requires=[
        'boto3>=1.4.4',
        'botocore>=1.5.34,<2.0.0',
        'beautifulsoup4>=4.5.3',
        'PyYAML>=3.12',
        'requests>=2.13.0',
    ],
    package_data={
        'acmagent': ['*.json']
    },
    entry_points={
        'console_scripts': [
            'acmagent = acmagent.cli:main'
        ]
    }
)
