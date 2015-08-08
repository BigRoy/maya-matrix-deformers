import math
import maya.OpenMaya as om

from matrix_deform.lib import MatrixDeform


class MatrixWave(MatrixDeform):
    """The matrix deformation by the non-linear wave algorithm."""

    # default
    id = om.MTypeId(0x0010A52D)
    pluginNodeTypeName = "matrixWave"

    def isAbstractClass(self):
        return False

    @classmethod
    def nodeInitialize(cls):
        super(cls, cls).nodeInitialize()
        nAttr = om.MFnNumericAttribute()

        # Attribute: curvature
        cls.aAmplitude = nAttr.create("amplitude", "amplitude",
                                      om.MFnNumericData.kDouble, 0.0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        nAttr.setSoftMin(-5)
        nAttr.setSoftMax(5)
        cls.addAttribute(cls.aAmplitude)

        # Attribute: wavelength
        cls.aWavelength = nAttr.create("wavelength", "wavelength",
                                       om.MFnNumericData.kDouble, 1.0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        nAttr.setMin(0.000001)
        nAttr.setSoftMin(0.1)
        nAttr.setSoftMax(10.0)
        cls.addAttribute(cls.aWavelength)

        # Attribute: offset
        cls.aOffset = nAttr.create("offset", "offset",
                                   om.MFnNumericData.kDouble, 0.0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        nAttr.setSoftMin(-10)
        nAttr.setSoftMax(10)
        cls.addAttribute(cls.aOffset)

        # Attribute: dropoff
        cls.aDropoff = nAttr.create("dropoff", "dropoff",
                                    om.MFnNumericData.kDouble, 0.0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        nAttr.setMin(-1.0)
        nAttr.setMax(1.0)
        cls.addAttribute(cls.aDropoff)

        # Attribute: minRadius
        cls.aMinRadius = nAttr.create("minRadius", "minRadius",
                                      om.MFnNumericData.kDouble, 0.0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        nAttr.setMin(0)
        nAttr.setSoftMax(10)
        cls.addAttribute(cls.aMinRadius)

        # Attribute: curvature
        cls.aMaxRadius = nAttr.create("maxRadius", "maxRadius",
                                      om.MFnNumericData.kDouble, 1.0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        nAttr.setMin(0)
        nAttr.setSoftMax(10)
        cls.addAttribute(cls.aMaxRadius)

        cls.attributeAffects(cls.aAmplitude, cls.outMatrix)
        cls.attributeAffects(cls.aWavelength, cls.outMatrix)
        cls.attributeAffects(cls.aOffset, cls.outMatrix)
        cls.attributeAffects(cls.aDropoff, cls.outMatrix)
        cls.attributeAffects(cls.aMinRadius, cls.outMatrix)
        cls.attributeAffects(cls.aMaxRadius, cls.outMatrix)

    def deformMatrix(self, datablock, deformMat, mat, envelope):

        amplitude = datablock.inputValue(self.aAmplitude).asDouble()
        if amplitude == 0.0:
            return mat  # Nothing changed so return the inMatrix

        minRadius = datablock.inputValue(self.aMinRadius).asDouble()
        maxRadius = datablock.inputValue(self.aMaxRadius).asDouble()
        if minRadius >= maxRadius:
            return mat

        wavelength = datablock.inputValue(self.aWavelength).asDouble()
        offset = datablock.inputValue(self.aOffset).asDouble()
        dropoff = datablock.inputValue(self.aDropoff).asDouble()

        # Get the point to deform in deformSpace
        invDeformMat = deformMat.inverse()
        localMat = mat * invDeformMat

        transformationMatrix = om.MTransformationMatrix(localMat)
        pt = transformationMatrix.getTranslation(
            om.MSpace.kWorld)  # this is actually in deformSpace

        # -- Calculate the new point after the bend
        x = pt.x
        y = pt.y
        z = pt.z

        # Distance from the center in x and z of the wave is the sample point
        # on the wave algorithm
        sampleRadius = math.sqrt((x * x) + (z * z))

        # Use the min-max range
        radius = sampleRadius
        outsideRange = False
        if radius < minRadius:
            radius = minRadius
            outsideRange = True
        elif radius > maxRadius:
            radius = maxRadius
            outsideRange = True

        if outsideRange:
            # outsideRange would have no new orientation since it's not
            # being deformed on the curve
            return mat

        # Calculate amplitude of point (w/ dropoff)
        pointAmplitude = amplitude
        radiusRangePercentage = (radius - minRadius) / (maxRadius - minRadius)

        currentDropoff = 1.0
        if dropoff:
            if dropoff > 0.0:
                currentDropoff = 1 - (dropoff * radiusRangePercentage)
            elif dropoff < 0.0:
                currentDropoff = 1 - (dropoff * (1 - radiusRangePercentage))
        if currentDropoff != 1.0:
            pointAmplitude *= currentDropoff

        wavePoint = radius + offset
        frequency = 1.0 / wavelength

        # y = y + a * (sin(u*sqrt(x^2+y^2)+t))
        y += math.sin(wavePoint * frequency) * pointAmplitude

        newPt = om.MVector(x, y, z)

        # Adjust the matrix's position
        transformationMatrix.setTranslation(newPt, om.MSpace.kWorld)
        newLocalMat = transformationMatrix.asMatrix()

        # Calculate rotation to the matrix
        # Use the jacobian matrix method (2) from:
        # http://http.developer.nvidia.com/GPUGems/gpugems_ch42.html
        # The jacobian matrix is the orientation matrix we need.
        # (3x3 matrix)
        # Maya magically only supports 4x4 matrix. All we need to do
        # to convert is add the extra row as an identity row.
        # As the extra row really only defines 'translate' in most
        # scenarios (no deformation in this case).

        # To keep this easy we only take the jacobian matrix from the core
        # function of a wave deformer. Then apply the 'dropoff' amount by
        # blending the jacobian matrix with the identity matrix to the
        # amount of the dropoff
        u = frequency
        l = offset
        distance = sampleRadius

        a = (math.cos((u * distance) + l)/distance) * u * x
        b = (math.cos((u * distance) + l)/distance) * u * z

        jacobianMatrix4x4 = [1.0, 0.0, 0.0, 0.0,
                             a, 1.0, b, 0.0,
                             0.0, 0.0, 1.0, 0.0,
                             0.0, 0.0, 0.0, 1.0]

        # create MMatrix from list
        orientationMatrix = om.MMatrix()
        om.MScriptUtil.createMatrixFromList(jacobianMatrix4x4,
                                            orientationMatrix)

        if dropoff:
            # create MTransformationMatrix from MMatrix
            # get the weighted matrix (by currentDropoff)
            orientationMatrix = om.MTransfomationMatrix(
                orientationMatrix).asMatrix(currentDropoff)

            # TODO: Weight the matrix

        newLocalMat = orientationMatrix * newLocalMat

        newMat = newLocalMat * deformMat  # Back to worldSpace
        return newMat