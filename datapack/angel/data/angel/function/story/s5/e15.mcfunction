scoreboard players set #force angel.story 0
data modify storage angel:story lead.ritsuko set value {id:"ritsuko",x:"3096.5",y:"54.0",z:"128.0",speed:"0.2"}
scoreboard players set #f.lead_ritsuko angel.story 1
scoreboard players set #f.lp_ritsuko angel.story 0
function angel:cast/look {id:"ritsuko",mode:"ahead"}
function angel:cast/walk {id:"ritsuko",x:3096.5,y:54.0,z:128.0,speed:0.2}
kill @e[tag=angel.cp_misato]
summon minecraft:marker 3094.5 54.0 138.7 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_55"]}
summon minecraft:marker 3094.5 54.0 136.2 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_56"]}
summon minecraft:marker 3094.5 54.0 133.7 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_57"]}
data modify storage angel:story cq.misato set value [{x:"3094.5",y:"54.0",z:"131.2",speed:"0.2"}]
scoreboard players set #f.cq_misato angel.story 1
scoreboard players set #ckn_misato angel.story 0
scoreboard players set #ckx0_misato angel.story 0
scoreboard players set #ckz0_misato angel.story 0
scoreboard players set #arrived_misato angel.cast 1
scoreboard players set #step angel.story 16
function angel:story/s5/e16
