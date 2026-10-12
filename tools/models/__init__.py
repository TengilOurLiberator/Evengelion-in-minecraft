"""Custom item models for the story's vehicles (car, rail wagon, VTOL aircraft) for Minecraft Java 26.3.

How it works (all verified against the 26.3 client jar, see README.md in this folder):

* a display part is an `item_display` entity whose stack carries `minecraft:item_model: "angel:<name>"`; the pack's
  `assets/angel/items/<name>.json` points at the block-style model `assets/angel/models/item/<name>.json`;
* a model is a list of cuboid elements (from/to in -16..32 model units, i.e. 3 blocks) with free rotation (`x`/`y`/`z` Euler
  angles about an origin, no 22.5 degree restriction in 26.3), per-face UVs and an optional `light_emission`;
* textures live in `assets/angel/textures/item/` (the `items` atlas picks up the `item` directory), generated here with numpy and pillow;
* authoring is done in RIG space (+x left, +y up, +z forward, blocks); `mdl.py` converts to the item model frame (an item display
  rotates its model 180 degrees about y and centres it) so that a part's translation is simply its centre.

Run from `D:\\angel-attack\\tools` with the project's python (the package must be imported as `models` from there, or as a
package loaded by path from tools/story/models.py):

    python -m models.build              # paint the textures, write the models and item definitions into the pack, validate
    python -m models.validate           # validate what is in the pack
    python -m models.shots              # previews from outside and from the passenger's eye
"""
