execute as @a[limit=1] at @s anchored eyes unless entity @e[tag=angel.prompt_main,limit=1] positioned ^ ^-0.3 ^2.0 run function angel:story/prompt/put
execute as @a[limit=1] at @s anchored eyes if entity @e[tag=angel.prompt_main,limit=1] unless entity @e[tag=angel.prompt_main,distance=..3.4,limit=1] positioned ^ ^-0.3 ^2.0 run function angel:story/prompt/put
