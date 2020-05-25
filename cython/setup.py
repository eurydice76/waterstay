import glob
import os
import sys

from Cython.Distutils import build_ext

from distutils.core import setup, Extension
from distutils.sysconfig import get_config_vars

import numpy

if 'linux' in sys.platform:
    (opt,) = get_config_vars('OPT')
    os.environ['OPT'] = " ".join(flag for flag in opt.split() if flag != '-Wstrict-prototypes')

INCLUDE_DIR = [numpy.get_include()]

EXTENSIONS = [Extension('connectivity',
                        include_dirs=INCLUDE_DIR,
                        sources=["connectivity/connectivity.pyx"],
                        language="c++",
                        extra_compile_args=["-std=c++11"],
                        extra_link_args=["-std=c++11"]),
              ]

setup(name="waterstay_extensions",
      version="0.0.0",
      ext_modules=EXTENSIONS,
      cmdclass={'build_ext': build_ext})