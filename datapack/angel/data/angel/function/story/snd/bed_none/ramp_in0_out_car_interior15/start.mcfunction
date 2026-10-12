schedule clear angel:story/snd/bed_cicadas/loop
stopsound @a ambient angel:amb.cicadas
schedule clear angel:story/snd/bed_town_empty/loop
stopsound @a ambient angel:amb.town_empty
schedule clear angel:story/snd/bed_car_interior/loop
# (the incoming bed's earlier copies, if any, are stopped by the ramp's steps)
stopsound @a ambient angel:amb.car_interior
execute at @a[limit=1] run playsound angel:amb.car_interior ambient @a ~ ~ ~ 0.35 1.0 1.0
schedule function angel:story/snd/bed_none/ramp_in0_out_car_interior15/s1 15t
