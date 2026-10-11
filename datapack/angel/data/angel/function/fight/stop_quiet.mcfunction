# cleans up everything of the fight except the player's scale
scoreboard players set #run angel.fight 0
scoreboard players set #phase angel.fight 0
schedule clear angel:fight/fx_fade
schedule clear angel:fight/fx_clear
schedule clear angel:fight/restart_go
function angel:angel/remove
kill @e[tag=angel.fight]
bossbar set angel:fight/giant players
bossbar set angel:fight/angel players
bossbar set angel:fight/wrap players
bossbar set angel:fight/giant visible false
bossbar set angel:fight/angel visible false
bossbar set angel:fight/wrap visible false
execute as @e[tag=angel.giant] run effect clear @s minecraft:slowness
execute as @e[tag=angel.giant] run effect clear @s minecraft:blindness
