schedule clear angel:story/snd/bed_car_interior/loop
stopsound @a ambient angel:amb.car_interior
schedule clear angel:story/snd/bed_cicadas/loop
stopsound @a ambient angel:amb.cicadas
schedule clear angel:story/snd/bed_geofront/loop
stopsound @a ambient angel:amb.geofront
schedule clear angel:story/snd/bed_hq/loop
stopsound @a ambient angel:amb.hq
schedule clear angel:story/snd/bed_town_empty/loop
stopsound @a ambient angel:amb.town_empty
schedule clear angel:story/snd/bed_tunnel/loop
stopsound @a ambient angel:amb.tunnel
schedule clear angel:story/snd/bed_plug/loop
# (the incoming bed's earlier copies, if any, are stopped by the ramp's steps)
schedule clear angel:story/snd/bed_lake/loop
stopsound @a ambient angel:amb.plug
execute at @a[limit=1] run playsound angel:amb.plug ambient @a ~ ~ ~ 0.3 1.0 1.0
stopsound @a ambient angel:amb.lake
execute at @a[limit=1] run playsound angel:amb.lake ambient @a ~ ~ ~ 0.3 1.0 1.0
schedule function angel:story/snd/bed_lake/ramp_in15_out_plug15/s1 15t
