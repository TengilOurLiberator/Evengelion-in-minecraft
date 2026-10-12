scoreboard players set #force angel.story 0
effect clear @a minecraft:levitation
tp @a[limit=1] 1160.0 64.0 160.0 180 0
kill @e[tag=angel.lflash]
execute at @a[limit=1] anchored eyes positioned ^ ^ ^ run function angel:story/launch/flash_down
function angel:story/snd/stop_music
stopsound @a * angel:sfx.launch
stopsound @a * angel:sfx.launch_roar
stopsound @a * angel:sfx.launch_charge
execute at @a[limit=1] run playsound angel:sfx.launch_arrive master @a ~ ~ ~ 2.0 1.0 1.0
function angel:world/sky_city
scoreboard players set #step angel.story 104
function angel:story/s6/e104
