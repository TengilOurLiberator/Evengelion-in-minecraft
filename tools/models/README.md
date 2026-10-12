# tools/models: custom item models for the vehicles

Builds the roadster, the rail wagon and the VTOL (and its wreck) as item models of the resource pack, and the previewer that lets you look at them
without the game.  `tools/story/models.py` shows them on `item_display` entities (`MODELS = "custom"`; `"boxes"` or `ANGEL_MODELS=boxes` brings the old
block-display boxes back).

```
cd D:\angel-attack\tools
$py = "D:\voice-assistant\.venv\Scripts\python.exe"
& $py -m models.build [car|wagon|vtol|all]     # paint textures, write models + item definitions into pack\angel-resources, validate
& $py -m models.validate                        # validate what is in the pack
& $py -m models.shots car [--only exterior|cockpit]   # exterior views and the passenger's eye views -> work\shots\models
& $py -m models.view car --eye 6 3 7 --at 0 .6 0 --fov 50 --out x.png [--door -62] [--roll 90] [--only nose,tub] [--hide tail]
& $py -m models.view vtol|wagon ...             # the same for the other vehicles
```

## What 26.3 does (read from the client jar, `versions\26.3\26.3.jar`)

* **Item model selection.** An `item_display` shows an item stack; the stack's `minecraft:item_model` component names an item model definition:
  `item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"angel:car_nose"}}` loads `assets/angel/items/car_nose.json`
  (`{"model":{"type":"minecraft:model","model":"angel:item/car_nose"}}`), which loads the block-style model `assets/angel/models/item/car_nose.json`.
  The command syntax checker of `build_story.py --check` accepts the summon commands.
* **Textures.** `textures/item/*.png` (the `items` atlas has a `directory` source `item`); a model names them `angel:item/<name>`.  Whether a quad is cut-out
  or translucent is decided per quad from the texels of its uv rectangle (`FaceBakery.computeMaterialTransparency`).
* **Element limits.** `from`/`to` between -16 and 32 (`CuboidModelElement.MIN_EXTENT/MAX_EXTENT`): a model is at most 3 blocks wide, high and long
  around its centre.  Rotation is `{"origin":[..], "x":..,"y":..,"z":.., "rescale":false}` (Euler, `rotationZYX(z, y, x)`: x first, then y, then z, verified
  by running JOML) or the old `{"origin", "axis", "angle"}`; **angles are free**, there is no 22.5 degree restriction any more, and the one-axis rule is gone
  with the Euler form.  Per element `light_emission` 0..15 (full-bright lamps) and `shade_direction_override`; per face `uv` [u0,v0,u1,v1] in 0..16,
  `rotation`, `cullface`, `tintindex`.  Faces are drawn one-sided like a block display's (the previewer culls the backs; not checked in the game).
* **What an item display does to a model** (`DisplayRenderer$ItemDisplayRenderer.submitInner`, `ItemTransform.apply`): the transformation, then a half turn
  about +y, then translate(-0.5): the model's centre (8, 8, 8) sits at the entity's origin and the model is seen from behind.  `mdl.py` therefore writes
  `model_x = 8 - 16 (x - cx)`, `model_z = 8 - 16 (z - cz)`: authoring is in rig space, a part displayed at scale 1 only needs its centre as translation.
  With no `display` entry there is no extra transform for the `none` context.

## Layout

| file | role |
|---|---|
| `mdl.py` | `Sheet` (texture sheets, shelf packer, edge padding), `Model`/`Elem` (cuboids in rig space), JSON + item definition writer, validator |
| `shapes.py` | `Bld`: mirrored building, oriented boxes, lofted surfaces made of thin tilted slabs (curved bodywork), rings and discs (round things from rotated slabs) |
| `paint.py`, `car_paint.py` | position-driven painters: paint, chrome, leather, tread, dials, plates ... (a painter sees the rig-space position of every texel, so neighbouring panels match) |
| `car.py`, `wagon.py`, `vtol.py` | the vehicles: `build_car()` etc. return a `Vehicle` with models and `PartSpec`s |
| `preview.py`, `shots.py`, `view.py` | the software renderer (reads the written JSON and PNGs), standard views, single views |
| `build.py`, `validate.py` | writers and checks |

Models are listed in `Vehicle.models`; `build` removes the vehicle's old files first, so renames never leave strays in the pack.
