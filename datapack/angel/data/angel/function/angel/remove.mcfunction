# function angel:angel/remove   (everything of the monster; also stops its loops)
schedule clear angel:angel/walk_tick
schedule clear angel:angel/anim_tick
schedule clear angel:angel/die_2
schedule clear angel:angel/die_3
scoreboard players set #walking angel.mon 0
scoreboard players set #loop angel.mon 0
kill @e[tag=angel.mon]
