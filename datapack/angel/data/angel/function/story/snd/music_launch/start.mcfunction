function angel:story/snd/stop_music
execute at @a[limit=1] run playsound angel:music.launch music @a ~ ~ ~ 0.7 1.0 1.0
schedule function angel:story/snd/music_launch/chain 1466t
