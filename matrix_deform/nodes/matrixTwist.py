import math
import maya.OpenMaya as om

from matrix_deform.lib import MatrixDeform


class MatrixTwist(MatrixDeform):
    """The matrix deformation by the non-linear twist algorithm."""

    # default
    id = om.MTypeId(0x0010A52E)
    pluginNodeTypeName = "matrixTwist"

    def isAbstractClass(self):
        return False

    @classmethod
    def nodeInitialize(cls):
        super(cls, cls).nodeInitialize()
        nAttr = om.MFnNumericAttribute()

        # Attribute: curvature
        cls.aStartAngle = nAttr.create("startAngle", "start",
                                       om.MFnNumericData.kDouble, 0.0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        nAttr.setSoftMin(-859.437)
        nAttr.setSoftMax(859.437)
        cls.addAttribute(cls.aStartAngle)

        # Attribute: asDegrees
        cls.aEndAngle = nAttr.create("endAngle", "end",
                                     om.MFnNumericData.kDouble, 0.0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        nAttr.setSoftMin(-859.437)
        nAttr.setSoftMax(859.437)
        cls.addAttribute(cls.aEndAngle)

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

        cls.attributeAffects(cls.aStartAngle, cls.outMatrix)
        cls.attributeAffects(cls.aEndAngle, cls.outMatrix)
        cls.attributeAffects(cls.aLowBound, cls.outMatrix)
        cls.attributeAffects(cls.aHighBound, cls.outMatrix)

    def deformMatrix(self, datablock, deformMat, mat, envelope):

        startAngle = datablock.inputValue(self.aStartAngle).asDouble()
        endAngle = datablock.inputValue(self.aEndAngle).asDouble()
        if startAngle == 0.0 and endAngle == 0.0:
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

        newPt = om.MVector(pt)

        # Limit between start and end bound
        if pt.y >= highBound:
            pt.y = highBound
            if endAngle == 0.0:
                return mat

        elif pt.y < lowBound:
            pt.y = lowBound
            if startAngle == 0.0:
                return mat

        # Percentage between the bounds
        percentage = (pt.y - lowBound) / (highBound - lowBound)
        angle = (percentage * (endAngle - startAngle)) + startAngle

        # Maya does it the exact opposite way, so we reverse our angle
        angle *= -1

        # Ensure radians so consider the input values to be degrees
        angle *= (math.pi / 180.0)

        # Reference:
        # Say you want to rotate a vector or a point in 2D by `b`
        # x' = x cos b - y sin b
        # y' = x sin b + y cos b

        # Rotate the point around local y-axis by angle in 2D
        x = pt.x
        z = pt.z

        newPt.x = x * math.cos(angle) + z * math.sin(angle)
        newPt.z = x * math.sin(angle) + z * math.cos(angle)

        # Rotate around the y-axis
        eulerRot = om.MEulerRotation(om.MVector(0, angle, 0))
        # Rotate the matrix around the z-axis (in pre-transform space)
        transformationMatrix.rotateBy(eulerRot, om.MSpace.kPreTransform)

        # Adjust the matrix position with point
        transformationMatrix.setTranslation(newPt, om.MSpace.kWorld)
        newLocalMat = transformationMatrix.asMatrix()
        newMat = newLocalMat * deformMat  # Back to worldSpace

        return newMat