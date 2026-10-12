# angel:music.decision_loop: 13.85s, repeats until stopped (it follows angel:music.decision, 103.85s)
execute at @a[limit=1] run playsound angel:music.decision_loop music @a ~ ~ ~ 0.75 1.0 1.0
schedule function angel:story/snd/music_decision/chain 277t
