scoreboard players set #force angel.story 0
data modify storage angel:story lead.ritsuko set value {id:"ritsuko",x:"3098.5",y:"54.0",z:"76.5",speed:"0.15"}
scoreboard players set #f.lead_ritsuko angel.story 1
scoreboard players set #f.lp_ritsuko angel.story 0
function angel:cast/look {id:"ritsuko",mode:"ahead"}
function angel:cast/walk {id:"ritsuko",x:3098.5,y:54.0,z:76.5,speed:0.15}
scoreboard players set #step angel.story 31
function angel:story/s5/e31
