scoreboard players set #force angel.story 0
playsound angel:sfx.impact_above_hard master @a 3096.5 100.0 72.5 5.0 0.8 1.0
execute at @a[limit=1] run playsound angel:sfx.dust_fall master @a ~ ~ ~ 0.9 1.0 1.0
function angel:story/hq/all_off
function angel:story/hq/dust_heavy
function angel:story/hq/rings
function angel:story/snd/music_decision/start
function angel:cast/dismount {id:"rei"}
scoreboard players set #step angel.story 152
function angel:story/s5/e152
