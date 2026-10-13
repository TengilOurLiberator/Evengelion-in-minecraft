"""The story's pacing: ONE table of every number that decides how long the film takes.

    import pace
    pace.use("video")            # the default: a whole playthrough in about 13 to 14 minutes
    pace.use("full")             # the original, unhurried values (what the story ran at before the video pacing)
    pace.PACE.gap                # read a value (an attribute of the current preset)

`build_story.py --pace video|full` picks the preset for a build (and for `--check`); the engine (core.CFG), the lead helper (lead.py), the objective system
(objective.py), the routes and the scenes read their numbers here and nowhere else.  Rules for editing: a value in "full" is what the code used before this
module existed (a `--pace full` build is byte for byte the old build); a value in "video" is a tightening of AIR, never of words: every scripted line is
still said, in order.  Nothing here assumes a line's exact length (live voices vary): the gaps are sleeps after a line's reported end, and what the
scenes schedule against a line's length is limited to the verbatim lines (sim.check_timing_bound).

Where a number lives:
    general      gap, answer waits and nudges, the safety net, the objectives' grace, walking pace of leaders
    s1 .. s6     one scene's sleeps, holds, estimates (named s<scene>_<what>)
    ending       the dawn and the card after the fight (scene 7)
    limits       what the route checker allows (comfort limits of the rides)
"""

PRESETS = {
    "full": dict(
        # ---- general
        gap=0.4,                       # seconds of silence after a line, before the next step
        wait_gap=0.4,                  # ... when the next step is a wait for the player's answer (the speak prompt appears after it)
        answer_timeout=None,           # an ordinary answer wait goes on by itself after this many seconds (None: only the global timeout / the safety net)
        nudge_first=12.0,              # the engine's gentle nudge (the asking character looks, the prompt pulses): first after this many seconds of silence ...
        nudge_repeat=15.0,             # ... then every this many
        stuck_hint_s=60.0,             # the safety net: a generic direction line after this long without progress
        stuck_skip_s=150.0,            # ... and the step is let go (a short fade) after this long
        ob_grace_cap=None,             # an objective with a longer grace of its own is shown after this many seconds at the latest (None: as written)
        ob_grace=2.0,                  # seconds before an objective shows
        ob_repeat=15.0,                # seconds without getting closer before the direction line comes again
        ob_line_secs=5.0,              # seconds the direction line stays
        lead_speed=0.14,               # lead(): default blocks a tick of a character who leads
        walk_speed=0.15,               # the walkers of scenes 4 and 5 (blocks a tick; 0.15 = 3 blocks a second)
        walk_slow=0.13,                # a character who steps out of a lift, to a mark
        walk_misc=0.12,
        lead_timeout=180.0, lead_hint=35.0,   # a leader waits for the player this long at a stop before he is brought (and the hint after)
        lead_est_pad=1.0,              # the checker's estimate of a walk: distance / speed + this
        est_overlap=False,             # the checker counts a line said WHILE a character walks (say_while) as part of the walk, not on top of it
        tutorial="full",               # "full": four lines, 20 s; "short": two lines, under 12 s, each ends the moment he does the thing
        tight=False,                   # the video pacing's structural cuts (scenes 1 to 6: lines said while moving, steps overlapped, fades for long walks)
        # ---- scene 1
        s1_setup_sleep=1.5, s1_card_hold=3.2, s1_note_hold=6.0,
        s1_est_leave=12.0, s1_est_phone=15.0, s1_est_street=14.0,
        s1_phone_after_pick=0.9, s1_phone_hangup=0.35, s1_phone_silence=0.8,
        s1_girl_look_timeout=45.0, s1_girl_max=6.0, s1_girl_away_ticks=14, s1_after_girl=1.4, s1_after_jolt=1.6, s1_angel_card_hold=2.0,
        s1_air_scale=1.0,              # the aircraft's timeline (the hit one comes down at 15 s in the full pacing) is scaled by this
        s1_before_103=2.8, s1_est_crash=4.0, s1_after_crash=1.4, s1_after_car=0.5, s1_after_board=0.6, s1_est_board=6.0,
        # ---- scene 2
        s2_drive_pause1=0.8, s2_drive_pause2=1.2, s2_ridge_pause=0.8,
        s2_to_ridge=dict(vmax=9.0, a_acc=1.3, a_dec=2.0, a_lat=2.0), s2_yaw_end=3.5,    # (the yaw blend into the ridge pose; a longer one keeps the turn rate down)
        s2_black_hold=24, s2_black_fade=20,   # ticks of real black after the blast, then of the fade back
        s2_est_push=5.0, s2_roll_sleep=2.6, s2_est_in=5.0, s2_engine_sleep=0.5, s2_engine_settle=3.2, s2_drive_pause3=1.0,
        s2_limp_min=2.3, s2_end_pause=0.8,
        # ---- scene 3
        s3_roll=dict(vmax=3.2, a_acc=0.8, a_dec=1.0, a_lat=1.2),      # the car rolling onto the wagon
        s3_gate_tail=6.5,              # the fade begins when the gate's boom and bolts (this many seconds after the gate begins to close) are nearly over
        s3_gate_trigger=3.6,           # seconds after the car starts to roll that the gate begins to close (the car's tail must be clear of the doorway)
        s3_fade=4.6, s3_fade_pause=0.5, s3_settle=1.4, s3_settle2=0.6, s3_ride_pause=1.6, s3_ride_pause2=1.5,
        s3_start_dist=10.0,            # blocks along the rail line at which the wagon starts its creep through the dark tunnel (it is held at 54 until 3.07 is over)
        s3_tunnel=dict(vmax=1.15, a_acc=0.35, a_dec=0.4),
        s3_max_quiet=60.0,             # more quiet than this after 3.10 and the ride is fade-skipped ahead ...
        s3_skip_keep=24.0,             # ... to this many seconds before the terminal
        s3_skip_black=1.2, s3_look=0.0, s3_end_pause=1.2, s3_end_pause2=3.0,
        # ---- scene 4
        s4_setup_fade=4.5, s4_setup_settle=1.2, s4_setup_sleep=1.5,
        s4_door_pause=0.9, s4_fade_black=0.8, s4_begin_ahead=0.0,
        s4_lobby_r=8.5, s4_lobby_est=3.0, s4_lobby_grace=3.0, s4_lobby_pause=0.8, s4_lift_pause1=1.1, s4_lift_pause2=0.9, s4_rit_est=3.5, s4_rit_settle=0.3,
        s4_alert_pause=1.4, s4_alert_end=0.5, s4_lift_est=6.0, s4_lift_grace=2.0, s4_doors_pause=0.7, s4_doors_close=1.4,
        s4_ride_black=7.0, s4_ride_dark=0.6, s4_ride_t1=4.3, s4_ride_t2=4.9, s4_ride_open=5.6, s4_dock_pause=0.8,
        s4_end_pause1=0.6, s4_end_pause2=1.2, s4_end_pause3=0.5,
        # ---- scene 5
        s5_setup_fade=4.5, s5_setup_settle=1.4, s5_setup_sleep=1.5,
        s5_door_pause=1.5, s5_est_face=10.0, s5_face_grace=3.0, s5_face_pause=0.5,
        s5_nothing=3.0,                # the cue sheet's beat of nothing after 5.01, before the cage lights (a silence worth keeping)
        s5_bank_step=0.5, s5_lights_stand=2.5, s5_father_hold=2.0, s5_impact_pause=0.8, s5_impact_after=1.5, s5_consent_timeout=45.0, s5_early_pause=0.6,
        s5_gurney_into_530=0.0,        # (video only) seconds into 5.30 at which the gurney is at its mark
        s5_rei_pause=0.5, s5_rei_after=0.8, s5_say_tick=130,       # the tick of the second impact at which 5.32 begins
        s5_est_mid=10.0,               # the checker's estimate of Ritsuko's walk back over the bridge (seconds still to go when the boy is with her)
        s5_est_girl=8.0, s5_girl_grace=10.0, s5_girl_pause=0.6, s5_nudge_first=9.0, s5_nudge_repeat=11.0,
        s5_yes_silence=1.2, s5_yes_hold=2.0, s5_follow_est=6.0, s5_bank_off0=1.0, s5_bank_off_step=1.1, s5_dark_pause=1.6, s5_dark_pause2=0.4,
        card_hold=3.5,
        # ---- scene 6
        s6_setup_fade=4.5, s6_setup_sleep=1.2, s6_hatch=1.2, s6_breath=1.2, s6_machinery=0.8, s6_after_6_02=0.8,
        s6_fluid_ticks=160,            # the amber fluid climbs from the floor to the ceiling in this many ticks (sfx.fluid_fill is 8 s long)
        s6_answer_timeout=6.0,
        s6_pad_black=3.0, s6_pad_pause=1.3, s6_word_pause=2.5, s6_after_flash=0.2, s6_surface_pause=1.4, s6_quiet=2.0,
        # ---- the ending (scene 7)
        end_hold=2.0, end_black=1.2, end_card_at=30.0, end_cage_dark=4.5, end_settle=1.2, end_card_hold=3.5,
        end_start_tick=None,           # the day clock is put here in the dark before the dawn (None: it runs from midnight, 18000, as built)
        end_dawn=((4.0, 30), (4.0, 30), (3.0, 14), (3.0, 14), (8.0, 7)),     # (seconds, clock rate): 7600 ticks in 22 s, from 18000 to the sun over the ridge at 25600
        end_fight_est=420.0,           # what the checker assumes the fight takes (seconds); the video value is the fight estimate's first-time player (tools/fight/estimate.py)
        # ---- limits of the route checker
        limit_yaw=60.0, limit_jerk=40.0,
    ),
}

# the video pacing: every value that differs from "full"
PRESETS["video"] = dict(
    PRESETS["full"],
    gap=0.1, wait_gap=0.0, answer_timeout=20.0, nudge_first=8.0, nudge_repeat=8.0, stuck_hint_s=30.0, stuck_skip_s=75.0,
    ob_grace=1.0, ob_grace_cap=3.0, ob_repeat=12.0, ob_line_secs=4.0,
    lead_speed=0.20, walk_speed=0.20, walk_slow=0.18, walk_misc=0.16, lead_timeout=75.0, lead_hint=20.0,
    tutorial="short", tight=True, lead_est_pad=0.4, est_overlap=True,
    limit_yaw=45.0,
    # ---- scene 1: a shorter card and note, the tutorial in two lines, the walks as a first-timer who follows the directions does them (the estimates), the
    # girl for 3.5 s at most, the aircraft's story in 11 s instead of 15
    s1_setup_sleep=0.5, s1_card_hold=2.4, s1_note_hold=4.0, s1_est_leave=5.0, s1_est_phone=5.0, s1_est_street=8.0,
    s1_phone_after_pick=0.5, s1_phone_hangup=0.2, s1_phone_silence=0.5, s1_girl_look_timeout=12.0, s1_girl_max=3.5, s1_girl_away_ticks=10, s1_after_girl=0.5,
    s1_after_jolt=0.9, s1_angel_card_hold=1.6, s1_air_scale=0.75, s1_before_103=1.2, s1_est_crash=3.0, s1_after_crash=0.5, s1_after_car=0.2, s1_after_board=0.2,
    s1_est_board=3.5,
    # ---- scene 2: no pauses that do no work, the car comes back to life as soon as she is in (the mine's two seconds of silence are untouched)
    s2_drive_pause1=0.2, s2_drive_pause2=0.4, s2_ridge_pause=0.3, s2_to_ridge=dict(vmax=11.0, a_acc=1.8, a_dec=2.4, a_lat=1.55), s2_yaw_end=3.5,
    s2_black_hold=14, s2_black_fade=14, s2_est_push=3.0, s2_roll_sleep=1.6, s2_est_in=3.0, s2_engine_sleep=0.2, s2_engine_settle=1.2, s2_drive_pause3=0.4,
    s2_end_pause=0.3,
    # ---- scene 3: the car rolls onto the wagon at 5 blocks a second, the gate shuts sooner, a shorter fade, the creep through the tunnel starts 22 blocks down the line,
    # and after 3.10 the cavern is looked at for a moment, then a fade skips the quiet stretch to the last 8 seconds of the ride
    s3_roll=dict(vmax=5.0, a_acc=1.2, a_dec=1.5, a_lat=1.2), s3_gate_trigger=2.4, s3_gate_tail=5.2,
    s3_fade=3.2, s3_fade_pause=0.2, s3_settle=0.9, s3_settle2=0.3, s3_ride_pause=0.5, s3_ride_pause2=0.8,
    s3_start_dist=22.0, s3_tunnel=dict(vmax=1.3, a_acc=0.4, a_dec=0.4), s3_max_quiet=8.0, s3_skip_keep=8.0, s3_skip_black=0.8, s3_look=1.5,
    s3_end_pause=0.5, s3_end_pause2=0.6,
    # ---- scene 4
    s4_setup_fade=3.0, s4_setup_settle=0.9, s4_setup_sleep=0.8, s4_door_pause=0.4, s4_fade_black=0.8, s4_begin_ahead=9.0,
    s4_lobby_r=15.0, s4_lobby_est=2.5, s4_lobby_grace=1.0, s4_lobby_pause=0.3, s4_lift_pause1=0.6, s4_lift_pause2=0.4, s4_rit_est=2.0, s4_rit_settle=0.1,
    s4_alert_pause=0.4, s4_lift_est=0.3, s4_lift_grace=1.0, s4_doors_pause=0.4, s4_doors_close=0.7,
    s4_ride_black=4.0, s4_ride_dark=0.4, s4_ride_t1=1.9, s4_ride_t2=2.5, s4_ride_open=2.7, s4_dock_pause=0.2,
    s4_end_pause1=0.2, s4_end_pause2=0.6, s4_end_pause3=0.1,
    # ---- scene 5
    s5_setup_fade=3.0, s5_setup_settle=1.0, s5_setup_sleep=0.5, s5_door_pause=0.5, s5_est_face=2.5, s5_est_mid=6.0, s5_face_grace=2.0, s5_face_pause=0.2, s5_nothing=2.5,
    s5_bank_step=0.375, s5_lights_stand=1.0, s5_father_hold=1.4, s5_impact_pause=0.4, s5_impact_after=0.6, s5_consent_timeout=20.0, s5_early_pause=0.2,
    s5_gurney_into_530=2.0, s5_rei_pause=0.1, s5_rei_after=0.3, s5_say_tick=100, s5_est_girl=4.0, s5_girl_grace=3.0, s5_girl_pause=0.3,
    s5_nudge_first=6.0, s5_nudge_repeat=8.0, s5_yes_silence=0.8, s5_yes_hold=2.0, s5_follow_est=3.0, s5_bank_off0=0.6, s5_bank_off_step=0.5,
    s5_dark_pause=0.6, s5_dark_pause2=0.1, card_hold=2.6,
    # ---- scene 6
    s6_setup_fade=3.0, s6_setup_sleep=0.5, s6_hatch=0.8, s6_breath=0.6, s6_machinery=0.3, s6_after_6_02=0.3, s6_fluid_ticks=100, s6_answer_timeout=5.0,
    s6_pad_black=2.5, s6_pad_pause=0.5, s6_word_pause=1.2, s6_after_flash=0.1, s6_surface_pause=0.6, s6_quiet=0.6,
    # ---- the ending: dawn in 11 s (the clock is put to the deep twilight, 22200, in the black: 3400 ticks to the sun over the ridge at 25600), the card, the cage
    end_hold=1.0, end_black=1.0, end_card_at=12.0, end_cage_dark=3.0, end_settle=0.9, end_card_hold=2.8, end_start_tick=22200,
    end_dawn=((2.0, 20), (2.0, 20), (2.0, 14), (5.0, 12.4)), end_fight_est=139.0,
)


class Pace:
    """The current preset: attribute access (`PACE.gap`); `use(name)` switches (before anything is built)."""

    def __init__(self, name="video"):
        self.use(name)

    def use(self, name):
        if name not in PRESETS:
            raise SystemExit(f"unknown pace {name!r}; choose one of {sorted(PRESETS)}")
        self.name = name
        self.v = PRESETS[name]
        return self

    def __getattr__(self, key):
        if key in ("name", "v"):
            raise AttributeError(key)
        try:
            return self.v[key]
        except KeyError:
            raise AttributeError(f"pace preset {self.name!r} has no value {key!r}") from None

    def override(self, **kw):
        """a copy of the current preset with some values changed (for one run: build_story.py --est-overlap, tests)"""
        self.v = dict(self.v, **kw)
        return self

    def differences(self):
        """[(key, full, video)] for the table in the build's report"""
        return [(k, PRESETS["full"][k], PRESETS["video"][k]) for k in PRESETS["full"] if PRESETS["full"][k] != PRESETS["video"][k]]


PACE = Pace("video")


def use(name):
    return PACE.use(name)
