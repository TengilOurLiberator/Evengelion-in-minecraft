# stop everything the story started: timers, entities, cast, monster, forceloads, scene flags
schedule clear angel:story/fx/birds_fly
schedule clear angel:story/fx/birds_kill
schedule clear angel:story/fx/cloud_1
schedule clear angel:story/fx/cloud_2
schedule clear angel:story/fx/impact
schedule clear angel:story/fx/jolt2
schedule clear angel:story/hq/door_close_1
schedule clear angel:story/hq/door_close_2
schedule clear angel:story/hq/door_open_1
schedule clear angel:story/hq/door_open_2
schedule clear angel:story/hq/dust_b
schedule clear angel:story/hq/dust_c
schedule clear angel:story/hq/fl_booth_1
schedule clear angel:story/hq/fl_booth_2
schedule clear angel:story/hq/fl_booth_3
schedule clear angel:story/hq/fl_booth_4
schedule clear angel:story/hq/fl_far_1
schedule clear angel:story/hq/fl_far_2
schedule clear angel:story/hq/fl_far_3
schedule clear angel:story/hq/fl_hit1_1
schedule clear angel:story/hq/fl_hit1_2
schedule clear angel:story/hq/fl_hit1_3
schedule clear angel:story/hq/fl_hit1_4
schedule clear angel:story/hq/fl_hit1_5
schedule clear angel:story/hq/fl_hit2_back_1
schedule clear angel:story/hq/fl_hit2_back_2
schedule clear angel:story/hq/fl_hit2_back_3
schedule clear angel:story/hq/fl_hit2_back_4
schedule clear angel:story/hq/impact_far
schedule clear angel:story/hq/rattle
schedule clear angel:story/hq/rig_break
schedule clear angel:story/hq/rig_break_down
schedule clear angel:story/hq/rig_clear
schedule clear angel:story/hq/rig_k2
schedule clear angel:story/hq/rig_k3
schedule clear angel:story/hq/rig_k4
schedule clear angel:story/hq/ring_1
schedule clear angel:story/hq/ring_2
schedule clear angel:story/hq/ring_3
schedule clear angel:story/hq/ring_4
schedule clear angel:story/hq/side_open_1
schedule clear angel:story/s1/f_a1
schedule clear angel:story/s1/f_a2
schedule clear angel:story/s1/f_a3
schedule clear angel:story/s1/f_a4
schedule clear angel:story/s2/f_a1
schedule clear angel:story/s2/f_a10
schedule clear angel:story/s2/f_a11
schedule clear angel:story/s2/f_a12
schedule clear angel:story/s2/f_a13
schedule clear angel:story/s2/f_a14
schedule clear angel:story/s2/f_a15
schedule clear angel:story/s2/f_a16
schedule clear angel:story/s2/f_a17
schedule clear angel:story/s2/f_a18
schedule clear angel:story/s2/f_a19
schedule clear angel:story/s2/f_a2
schedule clear angel:story/s2/f_a3
schedule clear angel:story/s2/f_a4
schedule clear angel:story/s2/f_a5
schedule clear angel:story/s2/f_a6
schedule clear angel:story/s2/f_a7
schedule clear angel:story/s2/f_a8
schedule clear angel:story/s2/f_a9
schedule clear angel:story/s2/f_cleanup_air
schedule clear angel:story/s4/f_a1
schedule clear angel:story/s4/f_a2
schedule clear angel:story/s4/f_a3
schedule clear angel:story/s4/f_a4
schedule clear angel:story/s4/f_a5
schedule clear angel:story/s4/f_a6
schedule clear angel:story/s4/f_a7
schedule clear angel:story/s4/f_a8
schedule clear angel:story/s4/f_a9
schedule clear angel:story/s5/f_a1
schedule clear angel:story/s5/f_a10
schedule clear angel:story/s5/f_a11
schedule clear angel:story/s5/f_a12
schedule clear angel:story/s5/f_a13
schedule clear angel:story/s5/f_a14
schedule clear angel:story/s5/f_a15
schedule clear angel:story/s5/f_a16
schedule clear angel:story/s5/f_a17
schedule clear angel:story/s5/f_a18
schedule clear angel:story/s5/f_a19
schedule clear angel:story/s5/f_a2
schedule clear angel:story/s5/f_a20
schedule clear angel:story/s5/f_a21
schedule clear angel:story/s5/f_a22
schedule clear angel:story/s5/f_a3
schedule clear angel:story/s5/f_a4
schedule clear angel:story/s5/f_a5
schedule clear angel:story/s5/f_a6
schedule clear angel:story/s5/f_a7
schedule clear angel:story/s5/f_a8
schedule clear angel:story/s5/f_a9
schedule clear angel:story/s6/f_a1
schedule clear angel:story/s6/f_a10
schedule clear angel:story/s6/f_a11
schedule clear angel:story/s6/f_a12
schedule clear angel:story/s6/f_a13
schedule clear angel:story/s6/f_a14
schedule clear angel:story/s6/f_a15
schedule clear angel:story/s6/f_a16
schedule clear angel:story/s6/f_a17
schedule clear angel:story/s6/f_a18
schedule clear angel:story/s6/f_a19
schedule clear angel:story/s6/f_a2
schedule clear angel:story/s6/f_a20
schedule clear angel:story/s6/f_a21
schedule clear angel:story/s6/f_a22
schedule clear angel:story/s6/f_a23
schedule clear angel:story/s6/f_a24
schedule clear angel:story/s6/f_a25
schedule clear angel:story/s6/f_a26
schedule clear angel:story/s6/f_a27
schedule clear angel:story/s6/f_a28
schedule clear angel:story/s6/f_a3
schedule clear angel:story/s6/f_a4
schedule clear angel:story/s6/f_a5
schedule clear angel:story/s6/f_a6
schedule clear angel:story/s6/f_a7
schedule clear angel:story/s6/f_a8
schedule clear angel:story/s6/f_a9
schedule clear angel:story/s7/f_a1
schedule clear angel:story/s7/f_a2
schedule clear angel:story/s7/f_a3
schedule clear angel:story/s7/f_a4
schedule clear angel:story/s7/f_a5
schedule clear angel:story/s7/f_a6
kill @e[tag=angel.story]
function angel:cast/remove {id:"misato"}
function angel:cast/remove {id:"ritsuko"}
function angel:cast/remove {id:"gendo"}
function angel:cast/remove {id:"rei"}
function angel:cast/remove {id:"rei_uniform"}
function angel:cast/remove {id:"medic1"}
function angel:cast/remove {id:"medic2"}
function angel:cast/gurney_remove
function angel:story/snd/stop_all
function angel:story/launch/restore
function angel:angel/remove
forceload remove 80 112
forceload remove 80 128
forceload remove 80 144
forceload remove 96 112
forceload remove 96 128
forceload remove 96 144
forceload remove 112 112
forceload remove 112 128
forceload remove 112 144
forceload remove 160 0
forceload remove 160 16
forceload remove 160 32
forceload remove 176 0
forceload remove 176 16
forceload remove 176 32
forceload remove 192 0
forceload remove 192 16
forceload remove 192 32
forceload remove 1136 32
forceload remove 1136 48
forceload remove 1136 64
forceload remove 1136 144
forceload remove 1136 160
forceload remove 1136 176
forceload remove 1152 32
forceload remove 1152 48
forceload remove 1152 64
forceload remove 1152 144
forceload remove 1152 160
forceload remove 1152 176
forceload remove 1168 32
forceload remove 1168 48
forceload remove 1168 64
forceload remove 1168 144
forceload remove 1168 160
forceload remove 1168 176
forceload remove 2000 80
forceload remove 2000 96
forceload remove 2000 112
forceload remove 2016 80
forceload remove 2016 96
forceload remove 2016 112
forceload remove 2032 80
forceload remove 2032 96
forceload remove 2032 112
forceload remove 2992 -16
forceload remove 2992 0
forceload remove 2992 16
forceload remove 2992 128
forceload remove 2992 144
forceload remove 2992 160
forceload remove 2992 176
forceload remove 3008 -16
forceload remove 3008 0
forceload remove 3008 16
forceload remove 3008 128
forceload remove 3008 144
forceload remove 3008 160
forceload remove 3008 176
forceload remove 3024 -16
forceload remove 3024 0
forceload remove 3024 16
forceload remove 3024 128
forceload remove 3024 144
forceload remove 3024 160
forceload remove 3024 176
forceload remove 3040 -16
forceload remove 3040 0
forceload remove 3040 16
forceload remove 3040 32
forceload remove 3040 48
forceload remove 3040 64
forceload remove 3040 80
forceload remove 3040 96
forceload remove 3040 112
forceload remove 3040 128
forceload remove 3040 144
forceload remove 3040 160
forceload remove 3040 176
forceload remove 3056 16
forceload remove 3056 32
forceload remove 3056 48
forceload remove 3056 64
forceload remove 3056 80
forceload remove 3056 96
forceload remove 3056 112
forceload remove 3056 128
forceload remove 3056 144
forceload remove 3056 160
forceload remove 3056 176
forceload remove 3072 16
forceload remove 3072 32
forceload remove 3072 48
forceload remove 3072 64
forceload remove 3072 80
forceload remove 3072 96
forceload remove 3072 112
forceload remove 3072 128
forceload remove 3072 144
forceload remove 3072 160
forceload remove 3072 176
forceload remove 3088 16
forceload remove 3088 32
forceload remove 3088 48
forceload remove 3088 64
forceload remove 3088 80
forceload remove 3088 96
forceload remove 3088 112
forceload remove 3088 128
forceload remove 3088 144
forceload remove 3088 160
forceload remove 3088 176
forceload remove 3104 16
forceload remove 3104 32
forceload remove 3104 48
forceload remove 3104 64
forceload remove 3104 80
forceload remove 3104 96
forceload remove 3104 112
forceload remove 3104 128
forceload remove 3104 144
forceload remove 3104 160
forceload remove 3104 176
forceload remove 3120 16
forceload remove 3120 32
forceload remove 3120 48
forceload remove 3120 64
forceload remove 3120 80
forceload remove 3120 96
forceload remove 3120 112
forceload remove 3120 128
forceload remove 3120 144
forceload remove 3120 160
forceload remove 3120 176
forceload remove 3136 128
forceload remove 3136 144
forceload remove 3136 160
forceload remove 3136 176
forceload remove 3152 128
forceload remove 3152 144
forceload remove 3152 160
forceload remove 3152 176
forceload remove 3168 128
forceload remove 3168 144
forceload remove 3168 160
forceload remove 3168 176
forceload remove 3184 128
forceload remove 3184 144
forceload remove 3184 160
forceload remove 3184 176
scoreboard players set #wait angel.story 0
scoreboard players set #talking angel.story 0
scoreboard players set #line_left angel.story 0
scoreboard players set #mv.on angel.story 0
scoreboard players set #ride angel.story 0
scoreboard players set #consent angel.story 0
scoreboard players set #fx.air angel.story 0
scoreboard players set #fx.fall angel.story 0
scoreboard players set #fx.smoke angel.story 0
scoreboard players set #fx.wreck angel.story 0
scoreboard players set #f.alarm angel.story 0
scoreboard players set #f.crash angel.story 0
scoreboard players set #f.fight_won angel.story 0
scoreboard players set #f.hold angel.story 0
scoreboard players set #f.lead_misato angel.story 0
scoreboard players set #f.lead_ritsuko angel.story 0
scoreboard players set #f.lp_misato angel.story 0
scoreboard players set #f.lp_ritsuko angel.story 0
scoreboard players set #f.rei_here angel.story 0
scoreboard players set #f.seen angel.story 0
scoreboard players set #f.turn_1 angel.story 0
scoreboard players set #f.turn_10 angel.story 0
scoreboard players set #f.turn_11 angel.story 0
scoreboard players set #f.turn_12 angel.story 0
scoreboard players set #f.turn_13 angel.story 0
scoreboard players set #f.turn_14 angel.story 0
scoreboard players set #f.turn_2 angel.story 0
scoreboard players set #f.turn_3 angel.story 0
scoreboard players set #f.turn_4 angel.story 0
scoreboard players set #f.turn_5 angel.story 0
scoreboard players set #f.turn_6 angel.story 0
scoreboard players set #f.turn_7 angel.story 0
scoreboard players set #f.turn_8 angel.story 0
scoreboard players set #f.turn_9 angel.story 0
execute if score #bridge_speaking angel.story matches ..-1 run scoreboard players set #bridge_speaking angel.story 0
