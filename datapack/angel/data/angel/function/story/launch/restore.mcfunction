# angel:story/launch/restore: everything scenes 6 and 7 can leave on the player and in the world (called by story/halt)
execute as @a run function angel:story/launch/reset_player
time of angel:day rate 1.0
stopsound @a * angel:sfx.launch
stopsound @a * angel:sfx.launch_roar
stopsound @a * angel:sfx.launch_charge
stopsound @a * angel:sfx.fluid_fill
stopsound @a * angel:sfx.contact
stopsound @a * angel:sfx.sync_rise
stopsound @a * angel:sfx.hatch_close
stopsound @a * angel:sfx.bridge_slide
stopsound @a * angel:sfx.bolt_1
stopsound @a * angel:sfx.bolt_2
stopsound @a * angel:sfx.bolt_3
stopsound @a * angel:sfx.launch_arrive
execute if score #run angel.fight matches 1 run function angel:fight/stop_quiet
bossbar set angel:fight/giant players
bossbar set angel:fight/angel players
bossbar set angel:fight/wrap players
execute if score #l.cage angel.story matches 1 if loaded 3096 60 100 run function angel:story/launch/cage_off
kill @e[tag=angel.launch]
execute as @a if entity @s[x=3000,y=8,z=0,dx=20,dy=148,dz=20] run tp @s 3009.0 4.0 9.0
execute as @a if entity @s[x=3088,y=57,z=56,dx=18,dy=22,dz=16] run tp @s 3096.5 54.0 72.5
