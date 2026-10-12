stopsound @a ambient angel:amb.cicadas
execute at @a[limit=1] run playsound angel:amb.cicadas ambient @a ~ ~ ~ 0.35 1.0 1.0
stopsound @a ambient angel:amb.town_empty
execute at @a[limit=1] run playsound angel:amb.town_empty ambient @a ~ ~ ~ 0.35 1.0 1.0
schedule function angel:story/snd/bed_mix_cicadas_town_empty/ramp_in32/s2 16t
