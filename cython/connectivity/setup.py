import numpy as np

from distutils.core import Extension, setup
from Cython.Distutils import build_ext

ext_modules = [Extension(name="connectivity",
                         sources=["connectivity.pyx"],
                         language="c++",
                         extra_compile_args=["-std=c++11"],
                         extra_link_args=["-std=c++11"],
                         include_dirs=[np.get_include()])]


setup(cmdclass={'build_ext': build_ext}, ext_modules=ext_modules,)
