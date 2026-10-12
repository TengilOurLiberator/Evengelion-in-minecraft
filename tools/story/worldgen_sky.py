"""Sky and weather for each set: the story calls the world generator's own function `angel:world/sky_<set>` (outskirts 6000, city 18000,
geofront 6000, hq 6000): it sets the world clock, pauses it and clears the weather, and moves nobody.  (`angel:world/enter_<set>` does the same
and also teleports the player, turning his head to the set's start direction; the story never does that.)  Each set has its own biome whose sky and
fog colours are multiplied by the world clock, so the clock value is the world generator's business, not the story's: there is no tick table here.

The functions come with the world build (tools/world); until the datapack has them a call is a silent no-op in the game, and the checker counts
`angel:world/...` as external, so `--check` does not depend on them.  Scene 7's dawn runs the clock itself (`time of angel:day rate ...`) from the
city's night and hands back with `rate 1.0` and `sky("hq")` when the ending returns to the cage.
"""
SETS = ("outskirts", "city", "geofront", "hq")


def sky(set_name):
    if set_name not in SETS:
        raise ValueError(f"no sky function for set {set_name!r}")
    return [f"function angel:world/sky_{set_name}"]
