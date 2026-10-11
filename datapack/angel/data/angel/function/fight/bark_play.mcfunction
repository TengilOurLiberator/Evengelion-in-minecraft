$data modify storage angel:fight played append value {id:"$(id)"}
$function angel:fight/say/$(id)
data remove storage angel:fight q[0]
scoreboard players set #gap angel.fight 10
