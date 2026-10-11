scoreboard players add #mv.n angel.story 1
execute if score #mv.route angel.story matches 1 run function angel:story/m/slide_in/root
execute if score #mv.route angel.story matches 2 run function angel:story/m/to_ridge/root
execute if score #mv.route angel.story matches 3 run function angel:story/m/to_gate/root
execute if score #mv.route angel.story matches 4 run function angel:story/m/gate_to_wagon/root
execute if score #mv.route angel.story matches 5 run function angel:story/m/geofront_ride/root
