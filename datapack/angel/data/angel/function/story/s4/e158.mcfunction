scoreboard players set #force angel.story 0
data modify storage angel:story lead.ritsuko set value {id:"ritsuko",x:"3096.5",y:"54.0",z:"150.0",speed:"0.2"}
scoreboard players set #f.lead_ritsuko angel.story 1
scoreboard players set #f.lp_ritsuko angel.story 0
function angel:cast/look {id:"ritsuko",mode:"ahead"}
function angel:cast/walk {id:"ritsuko",x:3096.5,y:54.0,z:150.0,speed:0.2}
kill @e[tag=angel.cp_misato]
summon minecraft:marker 3091.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_44"]}
summon minecraft:marker 3093.25 54.0 159.55 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_45"]}
summon minecraft:marker 3095.5 54.0 159.5 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_46"]}
summon minecraft:marker 3095.55 54.0 157.5 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_47"]}
data modify storage angel:story cq.misato set value [{x:"3095.5",y:"54.0",z:"159.5",speed:"0.2"},{x:"3095.6",y:"54.0",z:"155.5",speed:"0.2"}]
scoreboard players set #f.cq_misato angel.story 1
scoreboard players set #ckn_misato angel.story 0
scoreboard players set #ckx0_misato angel.story 0
scoreboard players set #ckz0_misato angel.story 0
scoreboard players set #arrived_misato angel.cast 1
scoreboard players set #step angel.story 159
function angel:story/s4/e159
