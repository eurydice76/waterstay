import numpy as np

from distutils.core import Extension, setup
from Cython.Distutils import build_ext

ext_modules = [Extension(name="atoms_in_shell",
                         sources=["atoms_in_shell.pyx"],
                         include_dirs=[np.get_include()])]


setup(cmdclass={'build_ext': build_ext}, ext_modules=ext_modules,)
