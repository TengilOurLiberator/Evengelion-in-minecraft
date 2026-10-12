function angel:story/snd/stop_bed
schedule clear angel:story/snd/bed_town_empty/loop
stopsound @a ambient angel:amb.town_empty
execute at @a[limit=1] run playsound angel:amb.town_empty ambient @a ~ ~ ~ 0.087 1.0 1.0
schedule function angel:story/snd/bed_town_empty/ramp_in60/s1 15t
