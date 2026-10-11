execute as @a[limit=1] at @s anchored eyes unless entity @e[tag=angel.prompt,limit=1] positioned ^ ^-0.2 ^1.7 run function angel:story/prompt/put
execute as @a[limit=1] at @s anchored eyes if entity @e[tag=angel.prompt,limit=1] unless entity @e[tag=angel.prompt,distance=..2.8,limit=1] positioned ^ ^-0.2 ^1.7 run function angel:story/prompt/put
