scoreboard players set #bo angel.fight 0
scoreboard players set #st angel.fight 9
scoreboard players set #t angel.fight 0
scoreboard players set #locked angel.fight 0
scoreboard players set #bar angel.fight 1
scoreboard players set #barp angel.fight 0
scoreboard players set #hold angel.fight 0
scoreboard players set #hold_t angel.fight 0
scoreboard players set #blockcd angel.fight 0
scoreboard players set #barsnd angel.fight 0
function angel:angel/stop_walking
scoreboard players set #dur angel.mon 6
function angel:angel/pose_stagger
stopsound @a * angel:sfx.beam_charge
function angel:fight/backoff_aim
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.hurt hostile @a ~ ~ ~ 8 0.6
# the barrier goes up: the octagon flares at the core (and keeps pulsing until the hold ends)
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~2.25 ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/wall_flash
bossbar set angel:fight/angel name {"text":"ANGEL  -  barrier up, it is falling back","color":"red"}
