$data modify storage angel:fight played append value {id:"$(id)"}
$function angel:fight/say/$(id)
# the line has begun (the wrap's countdown waits for #began_7_14)
$scoreboard players set #began_$(id) angel.barks 1
data remove storage angel:fight q[0]
scoreboard players set #gap angel.fight 10
