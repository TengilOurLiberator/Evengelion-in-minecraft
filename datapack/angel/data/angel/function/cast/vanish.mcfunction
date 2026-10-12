ride @s dismount
effect clear @s
data merge entity @s {DeathTime:19s,Tags:["angel.gone"],NoGravity:1b,Silent:1b}
execute at @s run tp @s ~ -2000 ~
kill @s
