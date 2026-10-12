scoreboard objectives add angel.story dummy
execute unless score #beat angel.story matches -2147483648..2147483647 run scoreboard players set #beat angel.story 0
execute unless score #wait angel.story matches -2147483648..2147483647 run scoreboard players set #wait angel.story 0
execute unless score #speaker angel.story matches -2147483648..2147483647 run scoreboard players set #speaker angel.story 0
execute unless score #talking angel.story matches -2147483648..2147483647 run scoreboard players set #talking angel.story 0
execute unless score #lastspoke angel.story matches -2147483648..2147483647 run scoreboard players set #lastspoke angel.story 0
execute unless score #bridge_speaking angel.story matches -2147483648..2147483647 run scoreboard players set #bridge_speaking angel.story 0
execute unless score #running angel.story matches -2147483648..2147483647 run scoreboard players set #running angel.story 0
execute unless score #scene angel.story matches -2147483648..2147483647 run scoreboard players set #scene angel.story 0
execute unless score #step angel.story matches -2147483648..2147483647 run scoreboard players set #step angel.story -1
execute unless score #mv.on angel.story matches -2147483648..2147483647 run scoreboard players set #mv.on angel.story 0
execute unless score #mv.n angel.story matches -2147483648..2147483647 run scoreboard players set #mv.n angel.story 0
execute unless score #mv.limit angel.story matches -2147483648..2147483647 run scoreboard players set #mv.limit angel.story 0
execute unless score #mv.route angel.story matches -2147483648..2147483647 run scoreboard players set #mv.route angel.story 0
execute unless score #ride angel.story matches -2147483648..2147483647 run scoreboard players set #ride angel.story 0
execute unless score #timeout_s angel.story matches -2147483648..2147483647 run scoreboard players set #timeout_s angel.story 0
execute unless score #subtitles angel.story matches -2147483648..2147483647 run scoreboard players set #subtitles angel.story 0
execute unless score #line_left angel.story matches -2147483648..2147483647 run scoreboard players set #line_left angel.story 0
execute unless score #sleep angel.story matches -2147483648..2147483647 run scoreboard players set #sleep angel.story 0
execute unless score #force angel.story matches -2147483648..2147483647 run scoreboard players set #force angel.story 0
execute unless score #tick angel.story matches -2147483648..2147483647 run scoreboard players set #tick angel.story 0
execute unless score #wt angel.story matches -2147483648..2147483647 run scoreboard players set #wt angel.story -1
execute unless score #consent angel.story matches -2147483648..2147483647 run scoreboard players set #consent angel.story 0
execute unless score #c5 angel.story matches -2147483648..2147483647 run scoreboard players set #c5 angel.story 5
execute unless score #c20 angel.story matches -2147483648..2147483647 run scoreboard players set #c20 angel.story 20
execute unless score #looking angel.story matches -2147483648..2147483647 run scoreboard players set #looking angel.story 0
execute unless score #pk angel.story matches -2147483648..2147483647 run scoreboard players set #pk angel.story 0
execute unless score #line angel.story matches -2147483648..2147483647 run scoreboard players set #line angel.story 0
execute unless score #rd angel.story matches -2147483648..2147483647 run scoreboard players set #rd angel.story 0
execute unless score #placed angel.story matches -2147483648..2147483647 run scoreboard players set #placed angel.story 0
execute unless score #nagt angel.story matches -2147483648..2147483647 run scoreboard players set #nagt angel.story 0
execute unless score #nagi angel.story matches -2147483648..2147483647 run scoreboard players set #nagi angel.story 0
execute unless score #hush angel.story matches -2147483648..2147483647 run scoreboard players set #hush angel.story 0
execute unless score #present_misato angel.story matches -2147483648..2147483647 run scoreboard players set #present_misato angel.story 0
execute unless score #present_ritsuko angel.story matches -2147483648..2147483647 run scoreboard players set #present_ritsuko angel.story 0
execute unless score #present_gendo angel.story matches -2147483648..2147483647 run scoreboard players set #present_gendo angel.story 0
execute unless score #present_rei angel.story matches -2147483648..2147483647 run scoreboard players set #present_rei angel.story 0
scoreboard players set #c5 angel.story 5
scoreboard players set #c20 angel.story 20
execute unless score #running angel.story matches 1 run kill @e[tag=angel.story]
execute unless score #running angel.story matches 1 if score #hq.dirty angel.story matches 1 run function angel:story/hq/reset_all
