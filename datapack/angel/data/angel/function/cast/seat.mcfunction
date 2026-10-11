$kill @e[type=minecraft:armor_stand,tag=angel.seat,tag=$(tag)]
$summon minecraft:armor_stand ~ ~ ~ {Tags:["angel.cast","angel.seat","$(tag)","angel.new"],Marker:1b,Invisible:1b,NoGravity:1b,Silent:1b,Invulnerable:1b}
tp @e[type=minecraft:armor_stand,tag=angel.new] ~ ~ ~ ~ 0
tag @e[type=minecraft:armor_stand,tag=angel.new] remove angel.new
