function angel:cast/remove_all
function angel:cast/gurney_remove
execute positioned 3094.5 54.0 76.5 rotated 180.0 0 run function angel:cast/summon {id:"misato"}
execute positioned 3098.5 54.0 76.5 rotated 180.0 0 run function angel:cast/summon {id:"ritsuko"}
execute positioned 3107.0 63.0 53.75 rotated 29.2 0 run function angel:cast/summon {id:"gendo"}
function angel:cast/scale {id:"gendo",scale:2.0}
function angel:cast/look {id:"misato",mode:"player"}
function angel:cast/look {id:"ritsuko",mode:"player"}
function angel:cast/look {id:"gendo",mode:"player"}
function angel:story/launch/cage_lights_on
