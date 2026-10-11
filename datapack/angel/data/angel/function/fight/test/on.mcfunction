# an armor stand stands in for the player: it is the giant. Drive the fight with the test/ functions.
kill @e[tag=angel.test]
scoreboard players set #test angel.fight 1
summon minecraft:armor_stand 1160.0 64.0 160.0 {Tags:["angel.giant","angel.test"],Invulnerable:1b,ShowArms:1b}
