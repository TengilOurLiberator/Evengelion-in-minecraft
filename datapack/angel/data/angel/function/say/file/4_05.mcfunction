# 4.05 BASE (8.67s) Paging Doctor Ritsuko Akagi, Technical Division One. Doctor Akagi, please contact Captain Katsuragi of Operations at once.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 177
scoreboard players set #line angel.story 405
scoreboard players set #live angel.story 0
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.4_05 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Paging Doctor Ritsuko Akagi, Technical Division One. Doctor Akagi, please contact Captain Katsuragi of Operations at once.", "color": "gray"}
