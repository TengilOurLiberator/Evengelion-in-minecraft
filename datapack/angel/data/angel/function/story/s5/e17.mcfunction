scoreboard players set #force angel.story 0
function angel:cast/look {id:"ritsuko",mode:"player"}
scoreboard players set #f.lp_ritsuko angel.story 0
data modify storage angel:story space.ritsuko set value {id:"ritsuko",x:"3096.5",y:"54.0",z:"125.4",speed:"0.12"}
scoreboard players set #f.sp_ritsuko angel.story 1
data modify storage angel:story space.misato set value {id:"misato",x:"3094.5",y:"54.0",z:"128.6",speed:"0.12"}
scoreboard players set #f.sp_misato angel.story 1
scoreboard players set #step angel.story 18
function angel:story/s5/e18
