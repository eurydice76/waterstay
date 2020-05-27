from decl_eigen cimport Vector3d
from libcpp cimport bool
from libcpp.map cimport map
from libcpp.set cimport set

cdef extern from "connectivity_octree.cpp":
    pass

# Declare the class with cdef
cdef extern from "connectivity_octree.h" namespace "Geometry":
    cdef cppclass ConnectivityOctree:
        ConnectivityOctree()
        ConnectivityOctree(const Vector3d&, const Vector3d&, int, int, int) except +
        bool addPoint(int index, const Vector3d& point, double radius)
        void findCollisions(map[int,set[int]]& collisions, double tolerance)
