from setuptools import setup

setup(
    name = 'invokust',
    version = '0.43',
    author = 'Max Williams',
    author_email = 'futuresharks@gmail.com',
    url = 'https://github.com/FutureSharks/invokust',
    download_url  =  'https://github.com/FutureSharks/invokust/archive/0.41.tar.gz',
    license = 'GPLv2',
    description = 'A small wrapper for locust to allow load testing on AWS Lambda',
    scripts = ['invokr.py'],
    packages = [
        'invokust',
        'invokust.aws_lambda',
    ],
    install_requires = [
        'locustio==0.8a2',
        'boto3',
        'pyzmq',
        'numpy'
    ],
    keywords = ['testing', 'loadtest', 'lamba', 'locust'],
    classifiers = [
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Testing :: Traffic Generation',
        'Programming Language :: Python :: 3.6'
    ],
)
