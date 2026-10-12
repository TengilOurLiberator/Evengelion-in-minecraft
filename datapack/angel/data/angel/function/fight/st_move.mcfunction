scoreboard players add #nav angel.fight 1
# (holding its ground after a back-off: it does not advance)
execute if score #nav angel.fight matches 10.. unless score #hold angel.fight matches 1 run function angel:fight/nav
execute unless score #walking angel.mon matches 1 if score #odd angel.fight matches 0 run function angel:fight/face_giant
execute if score #cd angel.fight matches ..0 run function angel:fight/choose
execute if score #hold angel.fight matches 1 run function angel:fight/hold_tick
