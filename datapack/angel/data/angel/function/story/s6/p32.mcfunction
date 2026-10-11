scoreboard players remove #sleep angel.story 1
execute if score #sleep angel.story matches ..0 run function angel:story/s6/x32
execute if score #step angel.story matches 32 if score #force angel.story matches 1 run function angel:story/s6/x32
