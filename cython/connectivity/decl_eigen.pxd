cdef extern from "Eigen/Dense" namespace "Eigen":
    cdef cppclass Vector3d:
        Vector3d() except +
        Vector3d(double c0, double c1, double c2) except +
        double& element "operator()"(int index)