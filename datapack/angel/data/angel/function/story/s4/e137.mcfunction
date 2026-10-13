scoreboard players set #force angel.story 0
data modify storage angel:story lead.ritsuko set value {id:"ritsuko",x:"3015.5",y:"54.0",z:"160.5",speed:"0.2"}
scoreboard players set #f.lead_ritsuko angel.story 1
scoreboard players set #f.lp_ritsuko angel.story 0
function angel:cast/look {id:"ritsuko",mode:"ahead"}
function angel:cast/walk {id:"ritsuko",x:3015.5,y:54.0,z:160.5,speed:0.2}
kill @e[tag=angel.cp_misato]
summon minecraft:marker 3004.5 54.0 161.5 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_1"]}
summon minecraft:marker 3006.548 54.0 160.684 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_2"]}
summon minecraft:marker 3008.597 54.0 159.868 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_3"]}
summon minecraft:marker 3010.645 54.0 159.052 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_4"]}
data modify storage angel:story cq.misato set value [{x:"3012.693",y:"54.0",z:"158.237",speed:"0.2"}]
scoreboard players set #f.cq_misato angel.story 1
scoreboard players set #ckn_misato angel.story 0
scoreboard players set #ckx0_misato angel.story 0
scoreboard players set #ckz0_misato angel.story 0
scoreboard players set #arrived_misato angel.cast 1
scoreboard players set #step angel.story 138
function angel:story/s4/e138
