# angel:amb.town_empty: 50.0s
execute at @a[limit=1] run playsound angel:amb.town_empty ambient @a ~ ~ ~ 0.7 1.0 1.0
schedule function angel:story/snd/bed_town_empty/loop 1000t
