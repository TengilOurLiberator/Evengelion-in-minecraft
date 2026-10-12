scoreboard players set #force angel.story 0
function angel:cast/look {id:"ritsuko",mode:"player"}
scoreboard players set #f.lp_ritsuko angel.story 0
data modify storage angel:story space.ritsuko set value {id:"ritsuko",x:"3018.1",y:"54.0",z:"160.5",speed:"0.12"}
scoreboard players set #f.sp_ritsuko angel.story 1
data modify storage angel:story space.misato set value {id:"misato",x:"3015.293",y:"54.0",z:"158.237",speed:"0.12"}
scoreboard players set #f.sp_misato angel.story 1
scoreboard players set #step angel.story 150
function angel:story/s4/e150
