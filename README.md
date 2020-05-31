cura-xwipe
==========

A Cura postprocessing plugin for running a nozzle cleaner during prints on the X axis arm of a 3D printer outside the bed area.

# Installation
Move XGantryWipe.py to the Cura /plugins/PostProcessingPlugin/scripts/ folder

# Use
In Cura Extensions > Post Processing > Modify G Code
Click Add a Script
Click XGantryWipe

# Method
This plugin removes the software endstop so it's possible to go beyond the bed measurement on the X gantry. This allows a nozzle cleaning brush to be positioned in the overflow area of the X gantry that can wiped between layers.

# Credits
This plugin's code was copied from this forum entry on Ultimaker [Kin's Ultimaker Community Wipe Plugin](https://community.ultimaker.com/topic/15655-how-to-make-a-plugin-anyone-have-a-plugin-to-do-x-action-every-layer-like-a-nozzle-wipe/)
