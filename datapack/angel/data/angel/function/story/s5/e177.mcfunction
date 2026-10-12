scoreboard players set #force angel.story 0
function angel:cast/pose {id:"rei",pose:"standing"}
function angel:cast/pose {id:"rei",pose:"sitting"}
execute at @a[limit=1] run particle minecraft:dust{color:[0.62,0.04,0.04],scale:1.3} ~ ~1.0 ~ 0.22 0.15 0.22 0 14 force
execute at @a[limit=1] run playsound minecraft:item.armor.equip_leather master @a ~ ~ ~ 0.6 0.9 0.5
scoreboard players set #step angel.story 178
function angel:story/s5/e178
