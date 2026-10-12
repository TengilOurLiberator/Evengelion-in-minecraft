function angel:story/snd/stop_bed
schedule clear angel:story/snd/bed_car_interior/loop
stopsound @a ambient angel:amb.car_interior
execute at @a[limit=1] run playsound angel:amb.car_interior ambient @a ~ ~ ~ 0.35 1.0 1.0
schedule function angel:story/snd/bed_car_interior/ramp_in20/s1 20t
