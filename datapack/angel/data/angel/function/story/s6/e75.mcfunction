scoreboard players set #force angel.story 0
scoreboard players set #ride angel.story 0
ride @a[limit=1] dismount
kill @e[tag=angel.lseat]
kill @e[tag=angel.lcock]
function angel:story/launch/eyes_off
function angel:cast/remove_all
function angel:cast/gurney_remove
forceload remove 3056 16
forceload remove 3056 32
forceload remove 3056 48
forceload remove 3056 64
forceload remove 3056 80
forceload remove 3056 96
forceload remove 3056 112
forceload remove 3056 128
forceload remove 3072 16
forceload remove 3072 32
forceload remove 3072 48
forceload remove 3072 64
forceload remove 3072 80
forceload remove 3072 96
forceload remove 3072 112
forceload remove 3072 128
forceload remove 3088 16
forceload remove 3088 32
forceload remove 3088 48
forceload remove 3088 64
forceload remove 3088 80
forceload remove 3088 96
forceload remove 3088 112
forceload remove 3088 128
forceload remove 3104 16
forceload remove 3104 32
forceload remove 3104 48
forceload remove 3104 64
forceload remove 3104 80
forceload remove 3104 96
forceload remove 3104 112
forceload remove 3104 128
forceload remove 3120 16
forceload remove 3120 32
forceload remove 3120 48
forceload remove 3120 64
forceload remove 3120 80
forceload remove 3120 96
forceload remove 3120 112
forceload remove 3120 128
function angel:story/snd/bed_hq/start
stopsound @a * angel:sfx.bolt_1
stopsound @a * angel:sfx.bolt_2
stopsound @a * angel:sfx.bolt_3
stopsound @a * angel:sfx.bridge_slide
stopsound @a * angel:sfx.contact
stopsound @a * angel:sfx.sync_rise
forceload add 2992 -16
forceload add 2992 0
forceload add 2992 16
forceload add 3008 -16
forceload add 3008 0
forceload add 3008 16
forceload add 3024 -16
forceload add 3024 0
forceload add 3024 16
scoreboard players set #step angel.story 76
function angel:story/s6/e76
