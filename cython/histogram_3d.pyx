import cython
cimport numpy as cnp 

import numpy as np


cdef extern from "math.h":

    double floor(double x)
    double ceil(double x)
    double sqrt(double x)

cdef inline double round(double r):
    return floor(r + 0.5) if (r > 0.0) else ceil(r - 0.5)

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def histogram_3d(cnp.ndarray[cnp.float64_t, ndim=2] coords,
                 cnp.ndarray[cnp.float64_t, ndim=2] lower_bounds,
                 cnp.ndarray[cnp.float64_t, ndim=2] upper_bounds,
                 int n_bin_x,
                 int n_bin_y,
                 int n_bin_z):

    cdef int n_frames

    cdef float dx, dy, dz

    cdef cnp.ndarray[cnp.float64_t, ndim=1] min_coord, max_coord

    cdef cnp.ndarray[cnp.int32_t, ndim=3] histogram

    histogram = np.zeros((n_bin_x,n_bin_y,n_bin_z),dtype=np.int32)

    n_frames = coords.shape[0]

    # Loop over the frames
    for 0 <= i < n_frames:

        min_coord = lower_bounds[i,:] - np.finfo(np.float).eps
        max_coord = upper_bounds[i,:] + np.finfo(np.float).eps

        dx = (max_coord[0] - min_coord[0])/n_bin_x
        dy = (max_coord[1] - min_coord[1])/n_bin_y
        dz = (max_coord[2] - min_coord[2])/n_bin_z

        bin_x = int((coords[i,0] - min_coord[0])/dx)
        bin_y = int((coords[i,1] - min_coord[1])/dy)
        bin_z = int((coords[i,2] - min_coord[2])/dz)

        if bin_x < 0 or bin_x >= n_bin_x:
            continue

        if bin_y < 0 or bin_y >= n_bin_y:
            continue

        if bin_z < 0 or bin_z >= n_bin_z:
            continue

        histogram[bin_x, bin_y, bin_z] += 1


    return ((dx, dy, dz), histogram)

