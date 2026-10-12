function angel:cast/pose {id:"rei",pose:"standing"}
tp @e[type=minecraft:mannequin,tag=angel.rei,limit=1] 3096.0 54.0 77.4 180 0
function angel:cast/pose {id:"rei",pose:"lying"}
execute at @a[limit=1] run playsound angel:sfx.dust_fall master @a ~ ~ ~ 0.8 1.0 1.0
