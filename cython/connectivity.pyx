# distutils: language = c++

from decl_eigen cimport Vector3d
from libcpp.map cimport map
from libcpp.set cimport set
cimport numpy as cnp

from connectivity_octree cimport ConnectivityOctree

# Create a Cython extension type which holds a C++ instance
# as an attribute and create a bunch of forwarding methods
# Python extension type.
cdef class PyConnectivity:
    # Hold a C++ instance which we're wrapping
    cdef ConnectivityOctree c_octree

    def __cinit__(self, cnp.ndarray[double,ndim=1] lb, cnp.ndarray[double,ndim=1] ub, int depth, int maxStorage, int maxDepth):
        cdef Vector3d lower = Vector3d(lb[0],lb[1],lb[2])
        cdef Vector3d upper = Vector3d(ub[0],ub[1],ub[2])
        self.c_octree = ConnectivityOctree(lower,upper,depth,maxStorage,maxDepth)

    def add_point(self, int index, cnp.ndarray[double,ndim=1] point, double radius):
        cdef Vector3d pt = Vector3d(point[0],point[1],point[2])
        return self.c_octree.addPoint(index,pt,radius)

    def find_collisions(self, tolerance):
        cdef map[int,set[int]] collisions
        self.c_octree.findCollisions(collisions, tolerance)
        return collisions

    def get_neighbour(self, cnp.ndarray[double,ndim=1] point):
        cdef Vector3d pt = Vector3d(point[0],point[1],point[2])
        cdef int idx
        self.c_octree.getNeighbour(pt,idx)
        return idx

