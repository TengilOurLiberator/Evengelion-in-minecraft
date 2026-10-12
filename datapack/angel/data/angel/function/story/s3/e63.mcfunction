scoreboard players set #force angel.story 0
scoreboard players set #ride angel.story 0
ride @a[limit=1] dismount
function angel:cast/remove {id:"misato"}
tp @a[limit=1] 2305.772 18.0 156.45
execute positioned 2305.705 18.0 154.751 rotated 87.72 0 run function angel:cast/summon {id:"misato"}
scoreboard players set #step angel.story 64
function angel:story/s3/e64
