$data modify storage angel:cast gm set value {x:$(x),y:$(y),z:$(z),speed:$(speed)}
execute as @e[tag=angel.gurney_root,limit=1] at @s run function angel:cast/gm_begin with storage angel:cast gm
