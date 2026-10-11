scoreboard players add #nav angel.fight 1
execute if score #nav angel.fight matches 10.. run function angel:fight/nav
execute unless score #walking angel.mon matches 1 if score #odd angel.fight matches 0 run function angel:fight/face_giant
execute if score #cd angel.fight matches ..0 run function angel:fight/choose
