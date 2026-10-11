"""Where each set stands in the world. The sets are far apart; the story moves the player between them."""

# name: (origin x y z, size x y z). Local y 0 is the bottom of the set's box.
SETS = {
    "outskirts": ((0, 32, 0), (256, 128, 256)),      # station, empty street, hill road, tunnel gate
    "city": ((1000, 32, 0), (320, 160, 320)),        # the fortress city centre: where the giant fights
    "geofront": ((2000, 0, 0), (320, 144, 320)),     # the cavern, the pyramid, the car-train tunnel
    "hq": ((3000, 0, 0), (192, 160, 192)),           # corridors, the cage, the plug, the launch shaft
}
