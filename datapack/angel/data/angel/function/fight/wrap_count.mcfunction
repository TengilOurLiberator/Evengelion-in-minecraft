# only while the countdown runs.  Bell beeps in the last 5 s (two a second)
execute if score #wt angel.fight matches ..100 if score #t angel.fight matches 10 run function angel:fight/wrap_beep
execute if score #wt angel.fight matches ..100 if score #t angel.fight matches 20.. run function angel:fight/wrap_beep
execute if score #t angel.fight matches 20.. run scoreboard players set #t angel.fight 0
# a heartbeat that quickens: the pause between beats is 6 + wt/16 ticks (26 at the start, 6 at the end)
scoreboard players add #hbt angel.fight 1
scoreboard players operation #hbp angel.fight = #wt angel.fight
scoreboard players operation #hbp angel.fight /= #16 angel.fight
scoreboard players add #hbp angel.fight 6
execute if score #hbt angel.fight >= #hbp angel.fight run function angel:fight/wrap_beat
# a ring of red light closes round the giant as the time runs down
execute if score #t angel.fight matches 0 run function angel:fight/wrap_ring
execute if score #t angel.fight matches 5 run function angel:fight/wrap_ring
execute if score #t angel.fight matches 10 run function angel:fight/wrap_ring
execute if score #t angel.fight matches 15 run function angel:fight/wrap_ring
# the squeeze: the tight pose for the last wrap_tight_at ticks (not while it is shuddering from a hit)
execute if score #shud angel.fight matches 0 if score #wt angel.fight matches ..160 unless score #wstage angel.fight matches 1 run function angel:fight/wrap_squeeze
execute if score #shud angel.fight matches 0 if score #wt angel.fight matches 161.. if score #wstage angel.fight matches 1 run function angel:fight/wrap_loosen
# the bar's colour: white in the last 5 s
execute if score #wt angel.fight matches ..100 run bossbar set angel:fight/wrap color white
execute if score #wt angel.fight matches 101.. run bossbar set angel:fight/wrap color red
