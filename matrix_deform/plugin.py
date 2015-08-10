import maya.OpenMayaMPx as omMPx
import maya.cmds as mc

from matrix_deform.lib import MatrixDeform
from matrix_deform.nodes.matrixBend import MatrixBend
from matrix_deform.nodes.matrixWave import MatrixWave
from matrix_deform.nodes.matrixTwist import MatrixTwist

nodes = [MatrixDeform, MatrixBend, MatrixWave, MatrixTwist]


# initializePlugin
def initializePlugin(obj):
    plugin = omMPx.MFnPlugin(obj, "Roy Nieterau", "0.1")

    # Register nodes
    for node in nodes:
        try:
            plugin.registerNode(node.pluginNodeTypeName,
                                node.id,
                                node.creator,
                                node.nodeInitialize)
        except RuntimeError, e:
            mc.warning("Can't register plug-in node "
                       "{0}: {1}".format(node.pluginNodeTypeName, e))


# uninitializePlugin
def uninitializePlugin(obj):
    plugin = omMPx.MFnPlugin(obj)

    # Deregister nodes
    for node in nodes:
        try:
            plugin.deregisterNode(node.id)
        except RuntimeError, e:
            mc.warning("Can't deregister plug-in node "
                       "{0}: {1}".format(node.pluginNodeTypeName, e))
