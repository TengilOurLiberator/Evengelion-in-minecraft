# function angel:fight/bark {id:"7_04"}: queues a line, once per attempt
$execute if score #$(id) angel.barks matches 1 run return 0
$scoreboard players set #$(id) angel.barks 1
$data modify storage angel:fight q append value {id:"$(id)"}
