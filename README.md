# maya-matrix-deformers
A set of Maya nodes to deform a transformation matrix by the algorithms used in non-linear deformers or approximate it for arbitrary deformers.

*Note: This is not ready for production in its current stage. It's a draft
implementation!*

In version 0.0.1 the *matrixBend* should be completely functional and the
*matrixWave* should be close to completion, but is there solely to show how
the algorithm is supposed to be implemented.

With version 0.1.0 the approximation deformer will also be included together
with the finished *matrixWave* deformer.
Coming soon.

### Use cases

#### Deformer stacking after each other

If you want to define a transform for a deformed point it's great if you can
push the original matrix through the same deformation. For example you could
stack two bend deformers in a chain where the second one's orientation is
deformed by the first. This way you can animate both deformers and keep a
consistent hierarchy of deformations.

#### Using the approximation deformers

**(TODO)**
> I've used this technique in the past, but will have to rewrite the code from
  C++ to Maya Python API to fit it into this package.

Maya's particles can be deformed by deformers, but will not deform its 
orientation. A workaround for approximating the changes to the matrix that this
particles receives from a deformer is to create a placeholder mesh for each 
particles' matrix and push that through a deformer. After the deformation the 
'matrix mesh' can be used as the required data for our deformed points.