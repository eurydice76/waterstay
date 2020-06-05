import fnmatch
import glob
import os
import sys

from distutils.util import convert_path
from distutils.sysconfig import get_config_vars
from setuptools import Extension, setup

from Cython.Distutils import build_ext as cython_build_ext

import numpy as np


def find_packages(path, base=None, exclude=None):

    packages = []

    for root, _, files in os.walk(path):
        if "__init__.py" in files:
            if base is not None:
                root = root.replace(path, base)
            package = root.replace(os.sep, ".")
            packages.append(package)

    return packages


EXCLUDE = ('*.py', '*.pyc', '*$py.class', '*~', '.*', '*.bak', '*.so', '*.pyd')

EXCLUDE_DIRECTORIES = ('__pycache__', 'CVS', '_darcs', 'build', '.svn', '.git', 'dist')


def find_package_data(where='.', package='', exclude=EXCLUDE, exclude_directories=EXCLUDE_DIRECTORIES, only_in_packages=True, show_ignored=False):

    out = {}
    stack = [(convert_path(where), '', package, only_in_packages)]
    while stack:
        where, prefix, package, only_in_packages = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatch.fnmatchcase(name, pattern)
                            or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            print("Directory %s ignored by pattern %s" % (fn, pattern))
                        break
                if bad_name:
                    continue
                if (os.path.isfile(os.path.join(fn, '__init__.py')) and not prefix):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                    stack.append((fn, '', new_package, False))
                else:
                    stack.append((fn, prefix + name + '/', package, only_in_packages))
            elif package or not only_in_packages:
                # is a file
                bad_name = False
                for pattern in exclude:
                    if (fnmatch.fnmatchcase(name, pattern)
                            or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            print("File %s ignored by pattern %s" % (fn, pattern))
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix+name)

    return out

#################################
# Packages section
#################################


package_info = {}
exec(open("src/__pkginfo__.py").read(), {}, package_info)

package = find_packages(path="src", base="waterstay")

package_data = find_package_data(where='src', package='waterstay')

#################################
# Scripts section
#################################

scripts = glob.glob(os.path.join('scripts','*'))

#################################
# Extensions section
#################################

INCLUDE_DIR = [np.get_include()]

if 'linux' in sys.platform:
    (opt,) = get_config_vars('OPT')
    os.environ['OPT'] = " ".join(flag for flag in opt.split() if flag != '-Wstrict-prototypes')

EXTENSIONS = [Extension('waterstay.extensions.connectivity',
                        include_dirs=INCLUDE_DIR,
                        sources=[os.path.join("cython", 'connectivity', 'connectivity.pyx')],
                        language="c++",
                        extra_compile_args=["-std=c++11"],
                        extra_link_args=["-std=c++11"]),
              Extension('waterstay.extensions.atoms_in_shell',
                        include_dirs=INCLUDE_DIR,
                        sources=[os.path.join("cython", 'atoms_in_shell', 'atoms_in_shell.pyx')])]

CMDCLASS = {'build_ext': cython_build_ext}

#################################
# The setup section
#################################

with open('requirements.txt','r') as fin:
	deps = fin.readlines()

setup(name="waterstay",
      version=package_info["__version__"],
      description=package_info["__description__"],
      long_description=package_info["__long_description__"],
      author=package_info["__author__"],
      author_email=package_info["__author_email__"],
      maintainer=package_info["__maintainer__"],
      maintainer_email=package_info["__maintainer_email__"],
      license=package_info["__license__"],
      install_requires=deps,
      packages=package,
      package_data=package_data,
      package_dir={"waterstay": "src"},
      ext_modules=EXTENSIONS,
      cmdclass=CMDCLASS,
      platforms=['Unix', 'Windows'],
      scripts=scripts)
