schedule clear angel:story/snd/bed_car_interior/loop
stopsound @a ambient angel:amb.car_interior
schedule clear angel:story/snd/bed_cicadas/loop
stopsound @a ambient angel:amb.cicadas
schedule clear angel:story/snd/bed_geofront/loop
stopsound @a ambient angel:amb.geofront
schedule clear angel:story/snd/bed_town_empty/loop
stopsound @a ambient angel:amb.town_empty
schedule clear angel:story/snd/bed_tunnel/loop
stopsound @a ambient angel:amb.tunnel
schedule clear angel:story/snd/bed_hq/loop
# (the incoming bed's earlier copies, if any, are stopped by the ramp's steps)
schedule clear angel:story/snd/bed_plug/loop
stopsound @a ambient angel:amb.hq
execute at @a[limit=1] run playsound angel:amb.hq ambient @a ~ ~ ~ 0.275 1.0 1.0
stopsound @a ambient angel:amb.plug
execute at @a[limit=1] run playsound angel:amb.plug ambient @a ~ ~ ~ 0.3 1.0 1.0
schedule function angel:story/snd/bed_plug/ramp_in12_out_hq12/s1 12t
