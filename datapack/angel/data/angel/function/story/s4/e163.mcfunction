scoreboard players set #force angel.story 0
data modify storage angel:story lead.ritsuko set value {id:"ritsuko",x:"3096.5",y:"54.0",z:"143.2",speed:"0.2"}
scoreboard players set #f.lead_ritsuko angel.story 1
scoreboard players set #f.lp_ritsuko angel.story 0
function angel:cast/look {id:"ritsuko",mode:"ahead"}
function angel:cast/walk {id:"ritsuko",x:3096.5,y:54.0,z:143.2,speed:0.2}
kill @e[tag=angel.cp_misato]
summon minecraft:marker 3095.6 54.0 155.5 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_48"]}
summon minecraft:marker 3095.6 54.0 153.233 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_49"]}
summon minecraft:marker 3095.6 54.0 150.967 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_50"]}
data modify storage angel:story cq.misato set value [{x:"3095.6",y:"54.0",z:"148.7",speed:"0.2"}]
scoreboard players set #f.cq_misato angel.story 1
scoreboard players set #ckn_misato angel.story 0
scoreboard players set #ckx0_misato angel.story 0
scoreboard players set #ckz0_misato angel.story 0
scoreboard players set #arrived_misato angel.cast 1
scoreboard players set #step angel.story 164
function angel:story/s4/e164
