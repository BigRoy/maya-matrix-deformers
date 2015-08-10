
from .version import *


def load():
    """Load the plug-in from the package.

    To allow Maya the read the plug-in file correctly the `matrix_deform`
    package should be importable.
    """
    import os
    import maya.cmds as mc
    directory = os.path.dirname(__file__)
    plugin = os.path.join(directory, 'plugin.py')
    mc.loadPlugin(plugin, quiet=True)