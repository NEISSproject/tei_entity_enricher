# Copyright 2021 The neiss authors. All Rights Reserved.
#
# This file is part of TEIEntityEnricher.
#
# tfaip is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# tfaip is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# tfaip. If not, see http://www.gnu.org/licenses/.
# ==============================================================================
from setuptools import setup, find_packages
import os
from TEIEntityEnricher import __version__

this_dir = os.path.dirname(os.path.realpath(__file__))


setup(
    name='TEIEntityEnricher',
    version=__version__,
    packages=find_packages(exclude=['test/*']),
    license='GPL-v3.0',
    long_description=open(os.path.join(this_dir, "README.md")).read(),
    long_description_content_type="text/markdown",
    author="Planet AI GmbH",
    author_email="admin@planet-ai.de",
    url="https://github.com/Planet-AI-GmbH/tf2_aip_base",
    download_url='https://github.com/Planet-AI-GmbH/tf2_aip_base/archive/{}.tar.gz'.format(__version__),
    entry_points={
        'console_scripts': [
            'ntee-start=TEIEntityEnricher.scripts.ntee:run',
        ],
    },
    python_requires='>=3.7',
    install_requires=open(os.path.join(this_dir, "requirements.txt")).read().split('\n'),
    keywords=['ner', 'tei', 'gui'],
    data_files=[('', [os.path.join(this_dir, "requirements.txt")])],
)
