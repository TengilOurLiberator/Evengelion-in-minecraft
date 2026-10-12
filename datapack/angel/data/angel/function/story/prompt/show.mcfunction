function angel:story/prompt/place
execute at @a[limit=1] run playsound angel:sfx.speak_chime master @a ~ ~ ~ 0.6 1.0 0.5
execute if score #placed angel.story matches 0 run function angel:story/prompt/bar
