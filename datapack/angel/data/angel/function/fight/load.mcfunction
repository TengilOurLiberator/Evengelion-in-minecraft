# objectives, constants, bossbars (all idempotent)
scoreboard objectives add angel.mon dummy
scoreboard objectives add angel.walk dummy
scoreboard objectives add angel.fight dummy
scoreboard objectives add angel.barks dummy
scoreboard objectives add angel.story dummy
scoreboard players set #2 angel.mon 2
scoreboard players set #2 angel.fight 2
scoreboard players set #16 angel.fight 16
bossbar add angel:fight/giant {"text":"UNIT-01","color":"green"}
bossbar add angel:fight/angel {"text":"ANGEL","color":"red"}
bossbar add angel:fight/wrap {"text":"SELF-DESTRUCT","color":"dark_red"}
bossbar set angel:fight/giant max 100
bossbar set angel:fight/angel max 42
bossbar set angel:fight/wrap max 320
bossbar set angel:fight/giant color green
bossbar set angel:fight/angel color red
bossbar set angel:fight/angel style notched_10
bossbar set angel:fight/wrap color red
bossbar set angel:fight/wrap style notched_20
execute unless data storage angel:fight q run data modify storage angel:fight q set value []
execute unless data storage angel:fight played run data modify storage angel:fight played set value []
execute unless score #run angel.fight matches 1 run scoreboard players set #run angel.fight 0
