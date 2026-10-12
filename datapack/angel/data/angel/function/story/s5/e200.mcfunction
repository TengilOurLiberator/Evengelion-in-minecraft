scoreboard players set #force angel.story 0
function angel:story/hq/booth_off
data modify storage angel:story lead.ritsuko set value {id:"ritsuko",x:"3096.5",y:"54.0",z:"125.0",speed:"0.15"}
scoreboard players set #f.lead_ritsuko angel.story 1
scoreboard players set #f.lp_ritsuko angel.story 0
function angel:cast/look {id:"ritsuko",mode:"ahead"}
function angel:cast/walk {id:"ritsuko",x:3096.5,y:54.0,z:125.0,speed:0.15}
scoreboard players set #step angel.story 201
function angel:story/s5/e201
