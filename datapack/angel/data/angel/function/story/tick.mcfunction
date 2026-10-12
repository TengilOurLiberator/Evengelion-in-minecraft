function angel:story/t_line
execute unless score #running angel.story matches 1 run return 0
execute unless entity @a[limit=1] run return 0
scoreboard players add #tick angel.story 1
function angel:story/mover
function angel:story/t_ride
function angel:story/t_inv
function angel:story/t_prompt
function angel:story/ob/tick
execute if score #scene angel.story matches 1 run function angel:story/s1/poll
execute if score #scene angel.story matches 2 run function angel:story/s2/poll
execute if score #scene angel.story matches 3 run function angel:story/s3/poll
execute if score #scene angel.story matches 4 run function angel:story/s4/poll
execute if score #scene angel.story matches 5 run function angel:story/s5/poll
execute if score #scene angel.story matches 6 run function angel:story/s6/poll
execute if score #scene angel.story matches 7 run function angel:story/s7/poll
function angel:story/t_fx
