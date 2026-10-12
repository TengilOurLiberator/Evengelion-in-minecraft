schedule clear angel:story/snd/bed_car_interior/loop
stopsound @a ambient angel:amb.car_interior
schedule clear angel:story/snd/bed_cicadas/loop
stopsound @a ambient angel:amb.cicadas
schedule clear angel:story/snd/bed_town_empty/loop
stopsound @a ambient angel:amb.town_empty
schedule clear angel:story/snd/bed_tunnel/loop
# (the incoming bed's earlier copies, if any, are stopped by the ramp's steps)
schedule clear angel:story/snd/bed_geofront/loop
stopsound @a ambient angel:amb.tunnel
execute at @a[limit=1] run playsound angel:amb.tunnel ambient @a ~ ~ ~ 0.35 1.0 1.0
stopsound @a ambient angel:amb.geofront
execute at @a[limit=1] run playsound angel:amb.geofront ambient @a ~ ~ ~ 0.233 1.0 1.0
schedule function angel:story/snd/bed_geofront/ramp_in25_out_tunnel12/s1 17t
