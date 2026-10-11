scoreboard players set #force angel.story 0
data modify storage angel:story lead.ritsuko set value {id:"ritsuko",x:"3096.5",y:"54.0",z:"100.0",speed:"0.15"}
scoreboard players set #f.lead_ritsuko angel.story 1
scoreboard players set #f.lp_ritsuko angel.story 0
function angel:cast/look {id:"ritsuko",mode:"ahead"}
function angel:cast/walk {id:"ritsuko",x:3096.5,y:54.0,z:100.0,speed:0.15}
scoreboard players set #step angel.story 24
function angel:story/s5/e24
