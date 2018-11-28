#!/usr/bin/env python2.7

import versioneer
from setuptools import find_packages, setup

import pkg_utils

_conf = dict(
    name='osaro-amazing-git',
    url='https://github.com/osaroai/amazing-git.git',
    author='Osaro',
    author_email='ops@osaro.com',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    include_package_data=True,
    entry_points=dict(
        console_scripts=[
            'git-remote-s3=amazing_git.__main__:main',
        ])
)

_conf.update(pkg_utils.setup_requirements(combine=False))

if __name__ == '__main__':
    setup(**_conf)
