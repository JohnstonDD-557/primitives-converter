# coding:utf-8

#####################################################################
# imports

import math
from mathutils import Matrix,Euler

#####################################################################
# xzy2matrix
def xzy2matrix(loc,eul,scale):
    #eul = Euler((0.0, math.radians(45.0), 0.0), 'XYZ')
    mat = Matrix.LocRotScale(loc, eul, scale)
    # print(mat)
    return mat

#####################################################################
# matrix2xzy
def matrix2xzy(mat):
    loc, rot, sca = mat.decompose()
    degrees = tuple(math.degrees(-a) for a in rot.to_euler())
    rotation = Euler((math.radians(degrees[0]), math.radians(degrees[1]), math.radians(degrees[2])), 'XYZ')
    mat_rot = rotation.to_matrix()
    # print(mat_rot)
    # print("\nDegrees:",degrees[0],degrees[1],degrees[2])
    # print("\n",loc, rot, sca)
    return rotation,sca
