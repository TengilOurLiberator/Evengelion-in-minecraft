scoreboard players set #force angel.story 0
data modify storage angel:story lead.ritsuko set value {id:"ritsuko",x:"3096.5",y:"54.0",z:"139.0",speed:"0.2"}
scoreboard players set #f.lead_ritsuko angel.story 1
scoreboard players set #f.lp_ritsuko angel.story 0
function angel:cast/look {id:"ritsuko",mode:"ahead"}
function angel:cast/walk {id:"ritsuko",x:3096.5,y:54.0,z:139.0,speed:0.2}
kill @e[tag=angel.cp_misato]
summon minecraft:marker 3095.4 54.0 146.8 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_51"]}
summon minecraft:marker 3095.5 54.0 146.2 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_52"]}
summon minecraft:marker 3095.5 54.0 142.7 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_53"]}
data modify storage angel:story cq.misato set value [{x:"3095.5",y:"54.0",z:"146.2",speed:"0.2"},{x:"3095.5",y:"54.0",z:"142.7",speed:"0.2"},{x:"3094.5",y:"54.0",z:"142.2",speed:"0.2"}]
scoreboard players set #f.cq_misato angel.story 1
scoreboard players set #ckn_misato angel.story 0
scoreboard players set #ckx0_misato angel.story 0
scoreboard players set #ckz0_misato angel.story 0
scoreboard players set #arrived_misato angel.cast 1
scoreboard players set #step angel.story 12
function angel:story/s5/e12
