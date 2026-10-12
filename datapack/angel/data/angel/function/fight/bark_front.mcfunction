# like bark, but the line goes to the FRONT of the queue (the wrap's 7.14: the countdown waits for it)
$execute if score #$(id) angel.barks matches 1 run return 0
$scoreboard players set #$(id) angel.barks 1
$data modify storage angel:fight q prepend value {id:"$(id)"}
