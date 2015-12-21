"""
intervaltree: A mutable, self-balancing interval tree for Python 2 and 3.
Queries may be by point, by range overlap, or by range envelopment.

Distribution logic

Note that "python setup.py test" invokes pytest on the package. With appropriately
configured setup.cfg, this will check both xxx_test modules and docstrings.

Copyright 2013-2015 Chaim-Leib Halbert

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from __future__ import absolute_import
import os
import errno
import sys
import subprocess
from warnings import warn
from setuptools import setup
from setuptools.command.test import test as TestCommand

import re

from utils import fs
from utils import doc

## CONFIG
target_version = '2.1.1'
create_rst = True


def development_version_number():
    p = subprocess.Popen('git describe'.split(), stdout=subprocess.PIPE)
    git_describe = p.communicate()[0].strip()
    release, build, commitish = git_describe.split('-')
    result = "{0}b{1}".format(release, build)
    return result

is_dev_version = 'PYPI' in os.environ and os.environ['PYPI'] == 'pypitest'
if is_dev_version:
    version = development_version_number()
else:  # This is a RELEASE version
    version = target_version

print("Version: " + version)
if is_dev_version:
    print("This is a DEV version")
    print("Target: %s\n" % target_version)
else:
    print("!!!>>> This is a RELEASE version <<<!!!\n")


## PyTest
# This is a plug-in for setuptools that will invoke py.test
# when you run python setup.py test
class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest  # import here, because outside the required eggs aren't loaded yet
        sys.exit(pytest.main(self.test_args))


def get_rst():
    if os.path.isdir('pyandoc/pandoc') and os.path.islink('pandoc'):
        print("Generating README.rst from README.md and CHANGELOG.md")
        return generate_rst()
    elif os.path.isfile('README.rst'):
        print("Reading README.rst")
        return read_file('README.rst')
    else:
        warn("No README.rst found!")
        print("Reading README.md")
        data = ''.join([
            read_file('README.md'),
            '\n',
            read_file('CHANGELOG.md'),
        ])
        return data


## Convert README to rst for PyPI
def generate_rst():
    """Converts Markdown to RST for PyPI"""
    md = fs.read_file("README.md")

    md = pypi_sanitize_markdown(md)
    rst = markdown2rst(md)
    rst = pypi_prepare_rst(rst)

    changes_md = pypi_sanitize_markdown(fs.read_file("CHANGELOG.md"))
    changes_rst = markdown2rst(changes_md)
    rst += "\n" + changes_rst

    # Write it
    if create_rst:
        fs.update_file('README.rst', rst)
    else:
        fs.rm_f('README.rst')

    return rst


def markdown2rst(md):
    """Convert markdown to rst format using pandoc. No other processing."""
    # import here, because outside it might not used
    try:
        import pandoc
    except ImportError as e:
        raise
    else:
        pandoc.PANDOC_PATH = 'pandoc'  # until pyandoc gets updated

    doc = pandoc.Document()
    doc.markdown_github = md
    rst = doc.rst

    return rst


## Sanitizers
def pypi_sanitize_markdown(md):
    """Prepare markdown for conversion to PyPI rst"""
    md = chop_markdown_header(md)
    md = remove_markdown_links(md)

    return md


def pypi_prepare_rst(rst):
    """Add a notice that the rst was auto-generated"""
    head = """\
.. This file is automatically generated by setup.py from README.md and CHANGELOG.md.

"""
    rst = head + rst

    return rst


def chop_markdown_header(md):
    """
    Remove empty lines and travis-ci header from markdown string.
    :param md: input markdown string
    :type md: str
    :return: simplified markdown string data
    :rtype: str
    """
    md = md.splitlines()
    while not md[0].strip() or md[0].startswith('[!['):
        md = md[1:]
    md = '\n'.join(md)
    return md


def remove_markdown_links(md):
    """PyPI doesn't like links, so we remove them."""
    # named links, e.g. [hello][url to hello] or [hello][]
    md = re.sub(
        r'\[((?:[^\]]|\\\])+)\]'    # link text
        r'\[((?:[^\]]|\\\])*)\]',   # link name
        '\\1',
        md
    )

    # url links, e.g. [example.com](http://www.example.com)
    md = re.sub(
        r'\[((?:[^\]]|\\\])+)\]'    # link text
        r'\(((?:[^\]]|\\\])*)\)',   # link url
        '\\1',
        md
    )

    return md


## Run setuptools
setup(
    name='intervaltree',
    version=version,
    install_requires=['sortedcontainers'],
    description='Editable interval tree data structure for Python 2 and 3',
    long_description=get_rst(),
    classifiers=[  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries',
        'Topic :: Text Processing :: General',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Text Processing :: Markup',
    ],
    keywords="interval-tree data-structure intervals tree",  # Separate with spaces
    author='Chaim-Leib Halbert, Konstantin Tretyakov',
    author_email='chaim.leib.halbert@gmail.com',
    url='https://github.com/chaimleib/intervaltree',
    download_url='https://github.com/chaimleib/intervaltree/tarball/' + version,
    license="Apache License, Version 2.0",
    packages=["intervaltree"],
    include_package_data=True,
    zip_safe=True,
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    entry_points={}
)
