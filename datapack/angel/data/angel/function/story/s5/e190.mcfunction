scoreboard players set #force angel.story 0
function angel:story/snd/stop_music
function angel:story/snd/stop_loop
function angel:story/snd/stop_bed
execute if score #f.alarm angel.story matches 1 run execute at @a[limit=1] run playsound angel:sfx.alarm_cut master @a ~ ~ ~ 1.0 1.0 1.0
scoreboard players set #step angel.story 191
function angel:story/s5/e191
