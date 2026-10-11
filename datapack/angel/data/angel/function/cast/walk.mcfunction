$data modify storage angel:cast walk.$(id) set value {id:"$(id)",x:$(x),y:$(y),z:$(z),speed:$(speed)}
$execute as @e[type=minecraft:mannequin,tag=angel.$(id),limit=1] at @s run function angel:cast/walk1 with storage angel:cast walk.$(id)
