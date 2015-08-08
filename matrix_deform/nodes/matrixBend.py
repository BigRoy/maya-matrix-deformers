import math
import maya.OpenMaya as om

from matrix_deform.lib import MatrixDeform


class MatrixBend(MatrixDeform):
    """The matrix deformation by the non-linear bend algorithm."""

    # default
    id = om.MTypeId(0x0010A52C)
    pluginNodeTypeName = "matrixBend"

    def isAbstractClass(self):
        return False

    @classmethod
    def nodeInitialize(cls):
        super(cls, cls).nodeInitialize()
        nAttr = om.MFnNumericAttribute()

        # Attribute: curvature
        cls.aCurvature = nAttr.create("curvature", "curvature",
                                      om.MFnNumericData.kDouble, 0.0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        nAttr.setSoftMin(-180)
        nAttr.setSoftMax(180)
        cls.addAttribute(cls.aCurvature)

        # Attribute: lowBound
        cls.aLowBound = nAttr.create("lowBound", "low",
                                     om.MFnNumericData.kDouble, -1.0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        nAttr.setSoftMin(-10)
        nAttr.setMax(0)
        cls.addAttribute(cls.aLowBound)

        # Attribute: highBound
        cls.aHighBound = nAttr.create("highBound", "high",
                                      om.MFnNumericData.kDouble, 1.0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        nAttr.setMin(0)
        nAttr.setSoftMax(10)
        cls.addAttribute(cls.aHighBound)

        # Attribute: asDegrees
        cls.aAsDegrees = nAttr.create("asDegrees", "degrees",
                                      om.MFnNumericData.kBoolean, 1.0)
        cls.addAttribute(cls.aAsDegrees)

        cls.attributeAffects(cls.aCurvature, cls.outMatrix)
        cls.attributeAffects(cls.aLowBound, cls.outMatrix)
        cls.attributeAffects(cls.aHighBound, cls.outMatrix)
        cls.attributeAffects(cls.aAsDegrees, cls.outMatrix)

    def deformMatrix(self, datablock, deformMat, mat, envelope):
        curvature = datablock.inputValue(self.aCurvature).asDouble()
        if curvature == 0.0:
            return mat  # Nothing changed so return the inMatrix

        lowBound = datablock.inputValue(self.aLowBound).asDouble()
        highBound = datablock.inputValue(self.aHighBound).asDouble()
        if lowBound >= highBound:
            return mat

        # Get the point to deform in deformSpace
        invDeformMat = deformMat.inverse()
        localMat = mat * invDeformMat

        # This is actually in deformSpace
        transformationMatrix = om.MTransformationMatrix(localMat)
        pt = transformationMatrix.getTranslation(om.MSpace.kWorld)

        # If at exact zero then it won't bend at all. (Odds that this
        # happens are small!)
        if pt.y == 0.0:
            return mat

        asDegrees = datablock.inputValue(self.aAsDegrees).asBool()
        if asDegrees:
            curvature *= (math.pi / 180.0)

        # Calculate the new point after the bend
        x = pt.x
        y = pt.y

        r = 1 / curvature  # bend radius
        # yr = y / r                     # bend at point y
        y_limited = y
        if y > highBound:
            y_limited = highBound
        elif y < lowBound:
            y_limited = lowBound

        yr = y_limited * curvature  # yr = y /r

        c = math.cos(math.pi - yr)
        s = math.sin(math.pi - yr)
        px = (r * c) + r - (x * c)
        py = (r * s) - (x * s)

        if y > highBound:
            py += -c * (y - highBound)
            px += s * (y - highBound)
        elif y < lowBound:
            py += -c * (y - lowBound)
            px += s * (y - lowBound)

        newPt = om.MVector(px, py, pt.z)

        # -- Calculate rotation to the matrix
        # yr is the rotation around the z-axis, so this one is easy!
        eulerRot = om.MEulerRotation(om.MVector(0, 0, -yr))
        # Rotate the matrix around the z-axis (in pre-transform space)
        transformationMatrix.rotateBy(eulerRot, om.MSpace.kPreTransform)

        # Adjust the matrix
        transformationMatrix.setTranslation(newPt, om.MSpace.kWorld)
        newLocalMat = transformationMatrix.asMatrix()
        newMat = newLocalMat * deformMat  # Back to worldSpace

        return newMat