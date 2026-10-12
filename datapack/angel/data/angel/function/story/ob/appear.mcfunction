scoreboard players set #ob.shown angel.story 1
scoreboard players set #ob.np angel.story 0
scoreboard players set #ob.rn angel.story 0
scoreboard players set #ob.bl angel.story -1
execute if score #ob.wp angel.story matches 1 at @e[tag=angel.ob_target,limit=1] run function angel:story/ob/wp_spawn
execute if score #ob.snd angel.story matches 1 run function angel:story/ob/chime
execute if score #ob.nl angel.story matches 1 run function angel:story/ob/line
