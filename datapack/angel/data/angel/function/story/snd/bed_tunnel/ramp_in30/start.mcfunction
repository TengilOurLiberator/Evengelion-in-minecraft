function angel:story/snd/stop_bed
schedule clear angel:story/snd/bed_tunnel/loop
stopsound @a ambient angel:amb.tunnel
execute at @a[limit=1] run playsound angel:amb.tunnel ambient @a ~ ~ ~ 0.175 1.0 1.0
schedule function angel:story/snd/bed_tunnel/ramp_in30/s1 15t
