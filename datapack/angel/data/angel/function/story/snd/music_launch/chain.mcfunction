# angel:music.launch_loop: 26.65s, repeats until stopped (it follows angel:music.launch, 73.30s)
execute at @a[limit=1] run playsound angel:music.launch_loop music @a ~ ~ ~ 0.7 1.0 1.0
schedule function angel:story/snd/music_launch/chain 533t
