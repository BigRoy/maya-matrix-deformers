import sys
import math

import maya.OpenMaya as om
import maya.OpenMayaAnim as omAnim
import maya.OpenMayaMPx as omMPx


class MatrixDeform(omMPx.MPxNode):
    """The abstract base class for Matrix deformation nodes."""
    # default
    id = om.MTypeId(0x0010A52B)
    pluginNodeTypeName = "matrixDeform"

    def __init__(self):
        omMPx.MPxNode.__init__(self)

    def isAbstractClass(self):
        return True

    @classmethod
    def creator(cls):
        return omMPx.asMPxPtr(cls())

    @classmethod
    def nodeInitialize(cls):

        nAttr = om.MFnNumericAttribute()

        # Attr: envelope
        cls.envelope = nAttr.create("envelope", "env",
                                    om.MFnNumericData.kFloat, 1.0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        nAttr.setSoftMin(0)
        nAttr.setSoftMax(1)
        cls.addAttribute(cls.envelope)

        mAttr = om.MFnMatrixAttribute()

        # Attr: inMatrix
        cls.inMatrix = mAttr.create("inMatrix", "inMat",
                                    om.MFnMatrixAttribute.kDouble)
        mAttr.setHidden(False)
        mAttr.setKeyable(False)
        cls.addAttribute(cls.inMatrix)

        # Attr: inDeformerMatrix
        cls.inDeformMatrix = mAttr.create("inDeformerMatrix", "inDeformMat",
                                          om.MFnMatrixAttribute.kDouble)
        mAttr.setHidden(False)
        mAttr.setKeyable(False)
        cls.addAttribute(cls.inDeformMatrix)

        # Attr: outMatrix
        cls.outMatrix = mAttr.create("outMatrix", "outMatrix",
                                     om.MFnMatrixAttribute.kDouble)
        mAttr.setKeyable(False)
        mAttr.setWritable(False)
        mAttr.setHidden(False)
        cls.addAttribute(cls.outMatrix)

        # Attribute Affects
        cls.attributeAffects(cls.inMatrix, cls.outMatrix)
        cls.attributeAffects(cls.inDeformMatrix, cls.outMatrix)
        cls.attributeAffects(cls.envelope, cls.outMatrix)

    def compute(self, plug, datablock):

        if plug == self.outMatrix:

            # Get input values
            inMat = datablock.inputValue(self.inMatrix).asMatrix()
            env = datablock.inputValue(self.envelope).asFloat()

            # If envelope is zero then just pass through inMatrix to outMatrix
            if env == 0.0:
                datablock.outputValue(self.outMatrix).setMatrix(inMat)
                return

            deformMat = datablock.inputValue(self.inDeformMatrix).asMatrix()

            # Calculate the deformed matrix (allow the children nodes to
            # implement that)
            outMat = self.deformMatrix(datablock, deformMat, inMat, env)

            # Set the deformed matrix
            # deformedMatrix = om.MMatrix()
            #outMat = inMat
            datablock.outputValue(self.outMatrix).setMMatrix(outMat)
            return

    def deformMatrix(self, datablock, deformMat, mat, envelope):
        """Return the deformed matrix"""
        raise NotImplementedError("The node's deformMatrix method should be "
                                  "implemented on inherited nodes.")


