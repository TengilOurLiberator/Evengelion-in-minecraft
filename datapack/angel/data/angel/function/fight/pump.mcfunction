# plays the next queued line when nothing is being said
execute if score #gap angel.fight matches 1.. run scoreboard players remove #gap angel.fight 1
execute if score #gap angel.fight matches 1.. run return 0
execute if score #talking angel.story matches 1 run return 0
execute unless data storage angel:fight q[0] run return 0
function angel:fight/bark_play with storage angel:fight q[0]
