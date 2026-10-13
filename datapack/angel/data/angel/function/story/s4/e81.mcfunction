scoreboard players set #force angel.story 0
function angel:cast/stop {id:"misato"}
tp @e[type=minecraft:mannequin,tag=angel.misato,limit=1] 3013.8 107.0 158.3
tp @a[limit=1] 3018.5 107.0 160.5
function angel:cast/look {id:"misato",mode:"player"}
scoreboard players set #step angel.story 82
function angel:story/s4/e82
