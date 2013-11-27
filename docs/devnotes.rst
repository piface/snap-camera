#################
Development Notes
#################

Snap Camera has three main components: :class:`Camera`, the functions
in :``__init__`` that control and the camera and the modes. The camera modes
are specified as a list in :class:`Camera`. Each mode has a name and an
option object describing the functions of that mode.

Creating a new mode
===================
To create a mode you must first add it to the list of modes in
:class:`Camera`. Then define that mode's options.

A mode option must inherrit from the parent class ModeOption. The camera
will call some of the functions at different points. Inspect
:class:`CameraModeOption` for an idea on how it works.