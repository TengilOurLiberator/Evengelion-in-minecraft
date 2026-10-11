# function angel:angel/walk {x:..,y:..,z:..,speed:0.15}   sets #arrived angel.walk to 1 on arrival (0 while walking)
kill @e[type=minecraft:marker,tag=angel.target]
$summon minecraft:marker $(x) $(y) $(z) {Tags:["angel.mon","angel.target"]}
$data modify storage angel:mon walk set value {speed:$(speed),stop:0.0d}
function angel:angel/walk_go
