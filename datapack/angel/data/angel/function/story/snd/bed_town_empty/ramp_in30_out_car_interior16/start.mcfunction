schedule clear angel:story/snd/bed_cicadas/loop
stopsound @a ambient angel:amb.cicadas
schedule clear angel:story/snd/bed_car_interior/loop
# (the incoming bed's earlier copies, if any, are stopped by the ramp's steps)
schedule clear angel:story/snd/bed_town_empty/loop
stopsound @a ambient angel:amb.car_interior
execute at @a[limit=1] run playsound angel:amb.car_interior ambient @a ~ ~ ~ 0.35 1.0 1.0
stopsound @a ambient angel:amb.town_empty
execute at @a[limit=1] run playsound angel:amb.town_empty ambient @a ~ ~ ~ 0.175 1.0 1.0
schedule function angel:story/snd/bed_town_empty/ramp_in30_out_car_interior16/s1 15t
