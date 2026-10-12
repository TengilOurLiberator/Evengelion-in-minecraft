function angel:story/ob/bearing
scoreboard players set #ob.low angel.story 0
execute if score #ob.gf angel.story matches 1 as @a[limit=1] at @s anchored eyes positioned ^ ^-0.4 ^2.0 if entity @e[tag=angel.char,distance=..1.5] run scoreboard players set #ob.low angel.story 1
execute if score #ob.gf angel.story matches 16 as @a[limit=1] at @s anchored eyes positioned ^ ^-6.4 ^32.0 if entity @e[tag=angel.char,distance=..24.0] run scoreboard players set #ob.low angel.story 1
kill @e[tag=angel.ob_line]
execute if score #ob.low angel.story matches 0 if score #ob.gf angel.story matches 1 as @a[limit=1] at @s anchored eyes positioned ^ ^-0.4 ^2.0 run function angel:story/ob/ld/root
execute if score #ob.low angel.story matches 1 if score #ob.gf angel.story matches 1 as @a[limit=1] at @s anchored eyes positioned ^ ^-1.0 ^1.8 run function angel:story/ob/ld/root
execute if score #ob.low angel.story matches 0 if score #ob.gf angel.story matches 16 as @a[limit=1] at @s anchored eyes positioned ^ ^-6.4 ^32.0 run function angel:story/ob/ld/root
execute if score #ob.low angel.story matches 1 if score #ob.gf angel.story matches 16 as @a[limit=1] at @s anchored eyes positioned ^ ^-16.0 ^28.8 run function angel:story/ob/ld/root
scoreboard players operation #ob.line angel.story = #ob.secs angel.story
execute unless score #ctl angel.story matches 1 run function angel:story/ob/bd/root
scoreboard players add #ob.rn angel.story 1
