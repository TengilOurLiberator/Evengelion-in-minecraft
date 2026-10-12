# function angel:fight/start   (as the player, who has just arrived at city.launch_top)
function angel:fight/stop_quiet
execute unless score #test angel.fight matches 1 run tag @a remove angel.giant
execute if entity @s[type=minecraft:player] run tag @s add angel.giant
execute unless entity @e[tag=angel.giant] run tag @a[limit=1] add angel.giant
execute if entity @s[tag=angel.pending] run tag @s add angel.giant
tag @e[tag=angel.pending] remove angel.pending
execute as @e[tag=angel.giant] run function angel:fight/become_giant
scoreboard players add #attempt angel.fight 1
scoreboard players set #gh angel.fight 100
scoreboard players set #ch angel.fight 60
scoreboard players set #phase angel.fight 0
scoreboard players set #st angel.fight 0
scoreboard players set #t angel.fight 0
scoreboard players set #cd angel.fight 0
scoreboard players set #ginv angel.fight 0
scoreboard players set #gcalm angel.fight 0
scoreboard players set #hitcd angel.fight 0
scoreboard players set #cd09 angel.fight 0
scoreboard players set #steps angel.fight 0
scoreboard players set #it angel.fight 0
scoreboard players set #nav angel.fight 99
scoreboard players set #t20 angel.fight 0
scoreboard players set #pt angel.fight 0
scoreboard players set #gap angel.fight 0
scoreboard players set #bt angel.fight 40
scoreboard players set #locked angel.fight 0
scoreboard players set #sl angel.fight 30
scoreboard players set #wt angel.fight 400
scoreboard players set #dmg angel.fight 0
scoreboard players set #blocked1 angel.fight 0
scoreboard players set #destroy angel.fight 1
scoreboard players set #bo angel.fight 0
scoreboard players set #bar angel.fight 0
scoreboard players set #barp angel.fight 0
scoreboard players set #hold angel.fight 0
scoreboard players set #hold_t angel.fight 0
scoreboard players set #hb angel.fight 0
scoreboard players set #blockcd angel.fight 0
scoreboard players set #sparkcd angel.fight 0
scoreboard players set #wallt angel.fight 0
scoreboard players reset * angel.barks
data modify storage angel:fight q set value []
data modify storage angel:fight played set value []
kill @e[tag=angel.fight]
summon minecraft:marker 1160.0 64.0 160.0 {Tags:["angel.fight","angel.origin"]}
execute positioned 1160.0 64.0 50.0 rotated 0 0 run function angel:angel/summon {height:30}
tag @e[tag=angel.mon] add angel.fight
function angel:angel/core_stage {stage:0}
bossbar set angel:fight/giant players @e[tag=angel.giant,type=minecraft:player]
bossbar set angel:fight/angel players @e[tag=angel.giant,type=minecraft:player]
bossbar set angel:fight/angel name {"text":"ANGEL","color":"red"}
bossbar set angel:fight/wrap players
bossbar set angel:fight/giant visible true
bossbar set angel:fight/angel visible true
bossbar set angel:fight/wrap visible false
bossbar set angel:fight/giant color green
function angel:fight/bark {id:"7_01"}
function angel:fight/bark {id:"7_02"}
scoreboard players set #run angel.fight 1
