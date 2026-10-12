# called after a landed core hit with the counter at its limit.  Not during the pause after the core cracked (the player's window): try again at the next hit
execute if score #st angel.fight matches 5 if score #sl angel.fight matches 80.. run return 0
execute if score #st angel.fight matches 9..10 run return 0
function angel:fight/backoff_start
