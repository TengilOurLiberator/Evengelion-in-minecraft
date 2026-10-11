"""A small stand-in set, so the compiler and the datapack can be tried before the real sets exist.

It crosses the 48-block tile edges on purpose (fences, panes and a pool run over them, a house stands on one) and
holds one of everything the placement has to get right: block states, waterlogging, a room carved out of a solid
cube with air, light blocks, set commands (a sign) and anchors.
"""
NAME = "demo"
ORIGIN = (-1000, 32, 0)
SIZE = (112, 64, 104)


def build(w):
    w.fill(0, 0, 0, 111, 0, 103, "stone")
    w.fill(0, 1, 0, 111, 2, 103, "dirt")
    w.fill(0, 3, 0, 111, 3, 103, "coarse_dirt")
    top = 4

    # a fence along z = 48 and a pane wall along x = 48: both sit exactly on a tile edge, and cross the other
    w.fill(0, top, 48, 111, top, 48, "oak_fence")
    w.fill(48, top, 5, 48, top + 2, 47, "glass_pane")
    w.fill(48, top, 49, 48, top + 2, 100, "glass_pane")

    # a stone-brick house over the x = 48 edge, hollow (air set on purpose), with a stair roof and lanterns
    x0, x1, z0, z1, h = 38, 58, 14, 34, 7
    w.fill(x0, top, z0, x1, top + h, z1, "stone_bricks")
    w.fill(x0 + 1, top + 1, z0 + 1, x1 - 1, top + h - 1, z1 - 1, "air")
    w.fill(x0 + 9, top + 1, z0, x0 + 11, top + 3, z0, "air")                     # a doorway
    for z in range(z0 - 1, z1 + 2):
        w.set(x0 - 1, top + h + 1, z, "stone_brick_stairs[facing=east,half=bottom]")
        w.set(x1 + 1, top + h + 1, z, "stone_brick_stairs[facing=west,half=bottom]")
    w.fill(x0, top + h + 1, z0 - 1, x1, top + h + 1, z0 - 1, "stone_brick_slab[type=top]")
    for x in (x0 + 4, x0 + 10, x0 + 16):
        w.set(x, top + h - 1, z0 + 10, "lantern[hanging=true]")
    w.set(x0 + 10, top + 1, z0 + 10, "light[level=12]")

    # a pool across the z = 48 edge: water held by a rim, one waterlogged stair in it
    w.fill(60, top - 1, 40, 80, top - 1, 56, "polished_andesite")
    w.fill(60, top, 40, 80, top, 56, "polished_andesite")
    w.fill(61, top, 41, 79, top, 55, "water")
    w.set(70, top, 48, "oak_stairs[facing=east,half=bottom,waterlogged=true]")

    # a solid cube with a room carved out of it by air, over the x = 96 edge
    w.fill(80, top, 62, 108, top + 20, 90, "deepslate_bricks")
    w.fill(85, top + 3, 67, 103, top + 12, 85, "air")
    w.set(94, top + 4, 76, "redstone_lamp[lit=false]")
    w.fill(90, top + 3, 67, 92, top + 5, 67, "air")

    # a few more states
    w.set(5, top, 5, "oak_log[axis=x]")
    w.set(6, top, 5, "oak_log[axis=z]")
    w.set(7, top, 5, "oak_door[facing=north,half=lower,hinge=left,open=false]")
    w.set(7, top + 1, 5, "oak_door[facing=north,half=upper,hinge=left,open=false]")
    w.set(9, top, 5, "chest[facing=south,type=single]")

    # things that need a neighbour whose tile is placed after theirs: they must survive the tile edges at x = 48, y = 48
    w.fill(48, top, 90, 48, top + 3, 90, "stone")
    w.set(47, top + 1, 90, "wall_torch[facing=west]")           # its wall is in the next tile
    w.fill(47, top, 94, 47, top + 3, 94, "stone")
    w.set(48, top + 1, 94, "wall_torch[facing=east]")           # its wall is in the earlier tile
    w.fill(9, top, 70, 13, 56, 74, "stone")
    w.set(11, 47, 72, "lantern[hanging=true]")                  # hangs from a block in the tile above
    w.fill(20, 40, 90, 20, 46, 90, "stone")
    w.set(20, 47, 90, "oak_door[facing=north,half=lower,hinge=left,open=false]")   # a door whose halves are in different tiles
    w.set(20, 48, 90, "oak_door[facing=north,half=upper,hinge=left,open=false]")

    w.anchor("start", 20.5, top, 8.5, yaw=-135.0, pitch=10.0)
    w.anchor("house_door", x0 + 10.5, top, z0 - 2, yaw=180.0)
    sx, sy, sz = w.abs(12, top, 5)
    w.command(f"setblock {sx} {sy} {sz} minecraft:gold_block")
    gx, gy, gz = w.abs(13, top, 5)
    w.command(f'setblock {gx} {gy} {gz} minecraft:oak_sign[rotation=8]{{front_text:{{messages:[{{text:"Angel"}},{{text:"Attack"}},"",""]}}}}')
    w.command(f"summon minecraft:marker {sx} {sy + 1} {sz} {{Tags:[\"angel.demo\"]}}")
