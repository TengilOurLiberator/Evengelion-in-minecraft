scoreboard players set #force angel.story 0
function angel:story/snd/stop_bed
execute at @a[limit=1] run playsound angel:sfx.launch master @a ~ ~ ~ 2.0 1.0 1.0
effect give @a minecraft:levitation 12 6 true
scoreboard players set #l.y angel.story 0
execute positioned 1160.0 64.0 50.0 rotated 0 0 run function angel:angel/summon {height:30}
scoreboard players set #step angel.story 89
function angel:story/s6/e89
