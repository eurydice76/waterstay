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
def atoms_in_shell(cnp.ndarray[cnp.float64_t, ndim=2] coords not None,
                   cnp.ndarray[cnp.float64_t, ndim=2] cell not None,
                   cnp.ndarray[cnp.float64_t, ndim=2] rcell not None,
                   list indexes not None,
                   cnp.int32_t center,
                   cnp.float64_t radius,
                   cnp.ndarray[cnp.int32_t, ndim=1] in_shell):

    cdef double x, y, z, x_boxed, y_boxed, z_boxed, sdx, sdy, sdz, rx, ry, rz, r, r2

    cdef int i, j, idx, n_molecules, n_atoms

    cdef cnp.ndarray[cnp.float64_t, ndim=1] shell_center = coords[center,:]
    cdef cnp.ndarray[cnp.float64_t, ndim=1] shell_center_boxed = np.empty(3,dtype=np.float)

    n_molecules = len(indexes)

    r2 = radius*radius

    shell_center_boxed[0] = shell_center[0]*rcell[0,0] + shell_center[1]*rcell[0,1] + shell_center[2]*rcell[0,2]
    shell_center_boxed[1] = shell_center[0]*rcell[1,0] + shell_center[1]*rcell[1,1] + shell_center[2]*rcell[1,2]
    shell_center_boxed[2] = shell_center[0]*rcell[2,0] + shell_center[1]*rcell[2,1] + shell_center[2]*rcell[2,2]
        
    # Loop over the molecules
    for 0 <= i < n_molecules:

        # Get the number of selected atoms in molecule i
        n_atoms = len(indexes[i])

        # Loop over the selected atoms j of molecule i
        for 0 <= j < n_atoms:

            idx = indexes[i][j]

            x = coords[idx,0]
            y = coords[idx,1]
            z = coords[idx,2]

            # Convert real coordinates to box coordinates
            x_boxed = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
            y_boxed = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
            z_boxed = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]

            sdx = x_boxed - shell_center_boxed[0]
            sdy = y_boxed - shell_center_boxed[1]
            sdz = z_boxed - shell_center_boxed[2]

            # Apply the PBC to the bxx coordinates distance vector between atom j qand the center of the shell
            sdx -= round(sdx)
            sdy -= round(sdy)
            sdz -= round(sdz)

            # Convert back the box coordinates distance vector to real coordinates distance vector
            rx = sdx*cell[0,0] + sdy*cell[0,1] + sdz*cell[0,2]
            ry = sdx*cell[1,0] + sdy*cell[1,1] + sdz*cell[1,2]
            rz = sdx*cell[2,0] + sdy*cell[2,1] + sdz*cell[2,2]

            # Compute the squared norm of the distance vector in real coordinates
            r = rx*rx + ry*ry + rz*rz
    
            # If the distance is below the cutoff mark the molecule i as being in the shell
            if r < r2:
                in_shell[i] = 1
                break



