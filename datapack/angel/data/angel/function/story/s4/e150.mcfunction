scoreboard players set #force angel.story 0
data modify storage angel:story lead.ritsuko set value {id:"ritsuko",x:"3096.5",y:"54.0",z:"160.5",speed:"0.2"}
scoreboard players set #f.lead_ritsuko angel.story 1
scoreboard players set #f.lp_ritsuko angel.story 0
function angel:cast/look {id:"ritsuko",mode:"ahead"}
function angel:cast/walk {id:"ritsuko",x:3096.5,y:54.0,z:160.5,speed:0.2}
kill @e[tag=angel.cp_misato]
summon minecraft:marker 3055.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_26"]}
summon minecraft:marker 3057.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_27"]}
summon minecraft:marker 3059.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_28"]}
summon minecraft:marker 3061.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_29"]}
summon minecraft:marker 3063.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_30"]}
summon minecraft:marker 3065.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_31"]}
summon minecraft:marker 3067.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_32"]}
summon minecraft:marker 3069.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_33"]}
summon minecraft:marker 3071.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_34"]}
summon minecraft:marker 3073.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_35"]}
summon minecraft:marker 3075.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_36"]}
summon minecraft:marker 3077.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_37"]}
summon minecraft:marker 3079.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_38"]}
summon minecraft:marker 3081.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_39"]}
summon minecraft:marker 3083.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_40"]}
summon minecraft:marker 3085.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_41"]}
summon minecraft:marker 3087.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_42"]}
summon minecraft:marker 3089.0 54.0 159.6 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_43"]}
data modify storage angel:story cq.misato set value [{x:"3091.0",y:"54.0",z:"159.6",speed:"0.2"}]
scoreboard players set #f.cq_misato angel.story 1
scoreboard players set #ckn_misato angel.story 0
scoreboard players set #ckx0_misato angel.story 0
scoreboard players set #ckz0_misato angel.story 0
scoreboard players set #arrived_misato angel.cast 1
scoreboard players set #step angel.story 151
function angel:story/s4/e151
