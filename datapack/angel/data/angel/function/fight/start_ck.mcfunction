# function angel:fight/start_ck   (as the pending giant, from restart_ck_go)
function angel:fight/stop_quiet
execute unless score #test angel.fight matches 1 run tag @a remove angel.giant
execute if entity @s[type=minecraft:player] run tag @s add angel.giant
execute unless entity @e[tag=angel.giant] run tag @a[limit=1] add angel.giant
execute if entity @s[tag=angel.pending] run tag @s add angel.giant
tag @e[tag=angel.pending] remove angel.pending
execute as @e[tag=angel.giant] run function angel:fight/become_giant
scoreboard players add #attempt angel.fight 1
scoreboard players set #gh angel.fight 100
scoreboard players set #ch angel.fight 42
scoreboard players set #phase angel.fight 0
scoreboard players set #st angel.fight 0
scoreboard players set #t angel.fight 0
scoreboard players set #cd angel.fight 0
scoreboard players set #ginv angel.fight 0
scoreboard players set #gcalm angel.fight 0
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
scoreboard players set #wt angel.fight 320
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
scoreboard players set #barsnd angel.fight 0
scoreboard players set #wallt angel.fight 0
scoreboard players set #wgo angel.fight 0
scoreboard players set #wwait angel.fight 0
scoreboard players set #wstage angel.fight 0
scoreboard players set #shud angel.fight 0
scoreboard players set #hbt angel.fight 0
scoreboard players set #whits angel.fight 0
scoreboard players set #vs angel.fight 0
scoreboard players set #vuln angel.fight 0
scoreboard players set #vp angel.fight 0
scoreboard players set #ptcd angel.fight 0
scoreboard players set #fl angel.fight 0
scoreboard players set #blk_n angel.fight 0
scoreboard players set #blk_why angel.fight 0
scoreboard players set #blk_tot angel.fight 0
scoreboard players set #hit_n angel.fight 0
scoreboard players set #inreach angel.fight 0
scoreboard players set #ck angel.fight 1
scoreboard players set #steps angel.fight 1
scoreboard players set #ch angel.fight 22
scoreboard players set #phase angel.fight 1
scoreboard players reset * angel.barks
scoreboard players set #7_01 angel.barks 1
scoreboard players set #7_02 angel.barks 1
scoreboard players set #7_03 angel.barks 1
scoreboard players set #7_04 angel.barks 1
scoreboard players set #7_05 angel.barks 1
scoreboard players set #7_06 angel.barks 1
scoreboard players set #7_07 angel.barks 1
scoreboard players set #7_08 angel.barks 1
data modify storage angel:fight q set value []
data modify storage angel:fight played set value []
kill @e[tag=angel.fight]
summon minecraft:marker 1160.0 64.0 160.0 {Tags:["angel.fight","angel.origin"]}
summon minecraft:marker 1160.0 64.0 160.0 {Tags:["angel.fight","angel.ckpos"]}
data modify entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos set value [1160.0d,64.0d,160.0d]
execute store result entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos[0] double 0.1 run scoreboard players get #ckgx angel.fight
execute store result entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos[1] double 0.1 run scoreboard players get #ckgy angel.fight
execute store result entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos[2] double 0.1 run scoreboard players get #ckgz angel.fight
tp @e[tag=angel.giant] @e[type=minecraft:marker,tag=angel.ckpos,limit=1]
execute store result entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos[0] double 0.1 run scoreboard players get #ckmx angel.fight
execute store result entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos[1] double 0.1 run scoreboard players get #ckmy angel.fight
execute store result entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos[2] double 0.1 run scoreboard players get #ckmz angel.fight
execute at @e[type=minecraft:marker,tag=angel.ckpos,limit=1] rotated 0 0 run function angel:angel/summon {height:30}
tag @e[tag=angel.mon] add angel.fight
kill @e[type=minecraft:marker,tag=angel.ckpos]
rotate @e[type=minecraft:marker,tag=angel.root,limit=1] facing entity @e[tag=angel.giant,limit=1] feet
function angel:angel/sync
execute as @e[tag=angel.giant] at @s run rotate @s facing entity @e[type=minecraft:marker,tag=angel.root,limit=1] feet
execute as @e[tag=angel.giant,type=minecraft:player] at @s run rotate @s ~ 20
execute as @e[tag=angel.giant] run effect clear @s minecraft:blindness
execute as @e[tag=angel.giant] run effect clear @s minecraft:slowness
bossbar set angel:fight/giant players @e[tag=angel.giant,type=minecraft:player]
bossbar set angel:fight/angel players @e[tag=angel.giant,type=minecraft:player]
bossbar set angel:fight/angel name {"text":"ANGEL","color":"red"}
bossbar set angel:fight/wrap players
bossbar set angel:fight/giant visible true
bossbar set angel:fight/angel visible true
bossbar set angel:fight/wrap visible false
bossbar set angel:fight/giant color green
bossbar set angel:fight/wrap color red
scoreboard players set #run angel.fight 1
# the same state as the moment the core cracked (core_crack: phase 2, the hunched pause, barks 7.12 and 7.13)
function angel:fight/core_crack
