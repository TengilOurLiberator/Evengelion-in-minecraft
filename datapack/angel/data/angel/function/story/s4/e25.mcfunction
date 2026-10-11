scoreboard players set #force angel.story 0
data modify storage angel:story lead.misato set value {id:"misato",x:"3109.5",y:"131.0",z:"160.5",speed:"0.15"}
scoreboard players set #f.lead_misato angel.story 1
scoreboard players set #f.lp_misato angel.story 0
function angel:cast/look {id:"misato",mode:"ahead"}
function angel:cast/walk {id:"misato",x:3109.5,y:131.0,z:160.5,speed:0.15}
scoreboard players set #step angel.story 26
function angel:story/s4/e26
