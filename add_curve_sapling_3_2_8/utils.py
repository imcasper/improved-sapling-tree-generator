# -*- coding: utf-8 -*-

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

print("version 3 imported")

from mathutils import *
from math import pi, sin, degrees, radians, atan2, cos, acos
from random import random

tau = 2 * pi

# Initialise the split error and axis vectors
splitError = 0.0
zAxis = Vector((0, 0, 1))
yAxis = Vector((0, 1, 0))
xAxis = Vector((1, 0, 0))

# This function determines the actual number of splits at a given point using the global error
def splits(n):
    global splitError
    nEff = round(n + splitError, 0)
    splitError -= (nEff - n)
    return int(nEff)

def splits2(n):
    r = random()
    if r < n:
        return 1
    else:
        return 0

def splits3(n):
    ni = int(n)
    nf = n - int(n)
    r = random()
    if r < nf:
        return ni + 1
    else:
        return ni + 0

# Determine the declination from a given quaternion
def declination(quat):
    tempVec = zAxis.copy()
    tempVec.rotate(quat)
    tempVec.normalize()
    return degrees(acos(tempVec.z))

# Determines the angle of upward rotation of a segment due to attractUp
def curveUp(attractUp, quat, curveRes):
    tempVec = yAxis.copy()
    tempVec.rotate(quat)
    tempVec.normalize()
    dec = radians(declination(quat))
    curveUpAng = attractUp*dec*abs(tempVec.z)/curveRes
    if (-dec + curveUpAng) < -pi:
        curveUpAng = -pi + dec
    if (dec - curveUpAng) < 0:
        curveUpAng = dec
    return curveUpAng

# Evaluate a bezier curve for the parameter 0<=t<=1 along its length
def evalBez(p1, h1, h2, p2, t):
    return ((1-t)**3)*p1 + (3*t*(1-t)**2)*h1 + (3*(t**2)*(1-t))*h2 + (t**3)*p2

# Evaluate the unit tangent on a bezier curve for t
def evalBezTan(p1, h1, h2, p2, t):
    return ((-3*(1-t)**2)*p1 + (-6*t*(1-t) + 3*(1-t)**2)*h1 + (-3*(t**2) + 6*t*(1-t))*h2 + (3*t**2)*p2).normalized()

# round down bone number
def roundBone(bone, step):
    bone_i = bone[:-3]
    bone_n = int(bone[-3:])
    bone_n = int(bone_n / step) * step
    return bone_i + str(bone_n).rjust(3, '0')

# Convert a list of degrees to radians
def toRad(list):
    return [radians(a) for a in list]

def anglemean(a1, a2, fac):
    x1 = sin(a1)
    y1 = cos(a1)
    x2 = sin(a2)
    y2 = cos(a2)
    x = x1 + (x2 - x1) * fac
    y = y1 + (y2 - y1) * fac
    return atan2(x, y)

# convert quat to use declination without rotation
def convertQuat(quat):
    adir = zAxis.copy()
    adir.rotate(quat)
    dec = radians(declination(quat))
    axis = Vector((-adir[1], adir[0], 0))
    return Matrix.Rotation(dec, 3, axis)
