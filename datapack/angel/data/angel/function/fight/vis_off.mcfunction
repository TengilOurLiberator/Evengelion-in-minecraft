# the fight is over (won or lost): nothing of either state is left standing
kill @e[type=minecraft:block_display,tag=angel.shield]
kill @e[type=minecraft:block_display,tag=angel.hot]
scoreboard players set #vs angel.fight 0
scoreboard players set #vuln angel.fight 0
