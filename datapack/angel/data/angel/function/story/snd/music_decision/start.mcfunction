function angel:story/snd/stop_music
execute at @a[limit=1] run playsound angel:music.decision music @a ~ ~ ~ 0.75 1.0 1.0
schedule function angel:story/snd/music_decision/chain 2077t
