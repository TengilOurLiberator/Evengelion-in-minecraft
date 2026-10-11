scoreboard players set #walking angel.mon 0
scoreboard players set #arrived angel.walk 1
execute if score #foot angel.mon matches 0..1 run function angel:angel/fx_foot
# on a real arrival (a target reached, not a stand-off) snap onto it; stand-offs keep their place
execute if data storage angel:mon {walk:{stop:0.0d}} at @e[type=minecraft:marker,tag=angel.target,limit=1] run tp @e[type=minecraft:marker,tag=angel.root,limit=1] ~ ~ ~
scoreboard players set #dur angel.mon 24
function angel:angel/sync
function angel:angel/pose_idle
