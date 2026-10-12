scoreboard players set #force angel.story 0
data modify storage angel:story lead.ritsuko set value {id:"ritsuko",x:"3096.5",y:"54.0",z:"135.5",speed:"0.15"}
scoreboard players set #f.lead_ritsuko angel.story 1
scoreboard players set #f.lp_ritsuko angel.story 0
function angel:cast/look {id:"ritsuko",mode:"ahead"}
function angel:cast/walk {id:"ritsuko",x:3096.5,y:54.0,z:135.5,speed:0.15}
data modify storage angel:story lead.misato set value {id:"misato",x:"3094.5",y:"54.0",z:"138.7",speed:"0.15"}
scoreboard players set #f.lead_misato angel.story 1
scoreboard players set #f.lp_misato angel.story 0
function angel:cast/look {id:"misato",mode:"ahead"}
function angel:cast/walk {id:"misato",x:3094.5,y:54.0,z:138.7,speed:0.15}
scoreboard players set #step angel.story 14
function angel:story/s5/e14
