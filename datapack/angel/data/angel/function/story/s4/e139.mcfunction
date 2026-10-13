scoreboard players set #force angel.story 0
data modify storage angel:story lead.ritsuko set value {id:"ritsuko",x:"3060.5",y:"54.0",z:"160.5",speed:"0.2"}
scoreboard players set #f.lead_ritsuko angel.story 1
scoreboard players set #f.lp_ritsuko angel.story 0
function angel:cast/look {id:"ritsuko",mode:"ahead"}
function angel:cast/walk {id:"ritsuko",x:3060.5,y:54.0,z:160.5,speed:0.2}
kill @e[tag=angel.cp_misato]
summon minecraft:marker 3012.693 54.0 158.237 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_5"]}
summon minecraft:marker 3014.693 54.0 158.487 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_6"]}
summon minecraft:marker 3016.693 54.0 158.737 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_7"]}
summon minecraft:marker 3018.693 54.0 158.987 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_8"]}
summon minecraft:marker 3020.693 54.0 159.237 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_9"]}
summon minecraft:marker 3022.693 54.0 159.487 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_10"]}
summon minecraft:marker 3024.693 54.0 159.737 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_11"]}
summon minecraft:marker 3026.714 54.0 159.727 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_12"]}
summon minecraft:marker 3028.734 54.0 159.718 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_13"]}
summon minecraft:marker 3030.755 54.0 159.709 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_14"]}
summon minecraft:marker 3032.775 54.0 159.7 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_15"]}
summon minecraft:marker 3034.796 54.0 159.691 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_16"]}
summon minecraft:marker 3036.816 54.0 159.682 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_17"]}
summon minecraft:marker 3038.836 54.0 159.673 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_18"]}
summon minecraft:marker 3040.857 54.0 159.664 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_19"]}
summon minecraft:marker 3042.877 54.0 159.655 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_20"]}
summon minecraft:marker 3044.898 54.0 159.646 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_21"]}
summon minecraft:marker 3046.918 54.0 159.636 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_22"]}
summon minecraft:marker 3048.939 54.0 159.627 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_23"]}
summon minecraft:marker 3050.959 54.0 159.618 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_24"]}
summon minecraft:marker 3052.98 54.0 159.609 {Tags:["angel.story","angel.cp","angel.cp_misato","angel.cpi_25"]}
data modify storage angel:story cq.misato set value [{x:"3024.693",y:"54.0",z:"159.737",speed:"0.2"},{x:"3055.0",y:"54.0",z:"159.6",speed:"0.2"}]
scoreboard players set #f.cq_misato angel.story 1
scoreboard players set #ckn_misato angel.story 0
scoreboard players set #ckx0_misato angel.story 0
scoreboard players set #ckz0_misato angel.story 0
scoreboard players set #arrived_misato angel.cast 1
scoreboard players set #step angel.story 140
function angel:story/s4/e140
