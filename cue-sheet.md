# Cue sheet

What the world does around the lines in `script.md`. The spoken words are fixed (they are recorded); everything
here is staging and can change freely. Anchors are the names in `tools/world/anchors.json`.

Rules for every scene

- Nothing runs on a clock the player can lose to. A block of lines starts when the player arrives or answers.
- The player is never turned, never moved a tick at a time, and never cut hard between places: moves between
  sets go through black.
- Every wait has a way forward (`angel:story/skip`), and a nudge if the player does nothing.
- Sound carries as much as the picture: each place has a bed of ambience, and silence is used on purpose
  (after the mine; before the lights in the cage; when the father looks down and says nothing).

## Cards

White serif capitals on black, held in silence, cut in with a single low hit. Four of them, no more:

| When | Card |
|---|---|
| Before scene 1, over black, cicadas starting underneath | `A.D. 2015` |
| As the Angel steps out between the hills, two seconds, then back to the street | `ANGEL ATTACK` |
| After 5.44, as the cage goes dark behind you | `EVANGELION  UNIT 01` |
| After the fight is won and 7.18 has been said | `TO BE CONTINUED` then, small, `an unofficial fan work` |

## Scene 1. The empty city

Changed from the first draft: the photograph's note now reads *"If I'm late, ring me from the phone outside the
station. M.K."* so the player has a reason to walk to the phone and hear that the lines are dead.

- Wake on the platform. Heat, cicadas, a distant crossing bell that stops. Letter and photograph in hand.
- The phone: 1.01, 1.02 through the handset. Hang-up click; the cicadas stop. Silence.
- The street: the girl at `outskirts.vision`. Birds go up. She is gone when the player looks back.
- The jolt. Car alarms far off. `ANGEL ATTACK`. The Angel walks in from `outskirts.angel_spawn`; each footfall is
  felt before it is heard. The city siren starts. 1.03 from the loudspeakers, echoing.
- Aircraft, fire, the crash at `outskirts.crash`. The car. 1.04 to 1.06.

## Scene 2. The road

- The drive is the first breath: engine, wind, the siren falling behind. 2.01 to 2.04.
- The ridge. 2.05, 2.06. The mine: white, then **no sound at all for two full seconds**, then the blast arrives
  and the car goes over. Ears ringing under 2.07.
- Pushing the car is the first thing the player does with their hands. 2.09 counts them in.
- The call. 2.12 to 2.16. In the distance the Angel stands in the crater, glowing, regrowing.

## Scene 3. The descent

- The gate closes behind the car: daylight narrows to a line and is gone. 3.01. Rumble, darkness, the
  dashboard light on Misato's face.
- 3.02 to 3.07 in the dark. The wagon waits in the tunnel for the player's answers if it must.
- 3.08 at `geofront.wall_opens`. The rumble drops away into open air. 3.09, 3.10 over the cavern. Then let it
  be quiet and let the player look.

## Scene 4. Lost

Set: `hq`. Cast: Misato from the start, Ritsuko from the lift.

| Cue | What happens |
|---|---|
| Arrive | Out of black at `hq.start`. Misato two paces ahead, already walking, looking back for the player. `#beat 40`. |
| Follow | Misato walks `corr_1` → `corr_2` → `corr_3` and waits at each until the player is within 6 blocks. She never leaves the player behind; if they stop, she stops and turns. 4.01 at `corr_1`, 4.02 on the moving walkway. |
| The loop | She leads once round the ring. The second time past `hq.loop_door` she stops dead in front of it: 4.03. **WAIT.** 4.04. She presses a wall panel. |
| The page | PA chime, 4.05, echoing down the corridor. |
| Onward | `corr_4` → `corr_5`, down the long escalator to `corr_6`. No lines: footsteps and hum. |
| The lift | As the player reaches the lobby the lift arrives with a tone and opens. Ritsuko steps out of `hq.elevator_in` to `hq.elevator`. 4.06 (to Misato), 4.07, 4.08 (she turns to the player), 4.09, 4.10. **WAIT.** 4.11. `#beat 41`. |
| The alert | Lights dip to red for a moment. Klaxon, three pulses, then 4.12 over it. |
| Down | All three into the lift. Doors. Through black to the lower stop at `hq.dock`. |
| The crossing | They walk the catwalk over the red lake, Ritsuko leading, Misato beside the player. 4.13 to 4.17 as they walk, spaced along it. 4.18 at `hq.cage_door` as it opens onto darkness. |

## Scene 5. The cage

Set: `hq`. This is the scene the whole thing exists for. Slow down.

| Cue | What happens |
|---|---|
| Dark | Player walks onto the bridge behind Ritsuko. The door (`DOORS["cage_door"]`) closes behind them with a boom. Only the red emergency lamps. Characters go to `captain_mark` and `scientist_mark`. When the player reaches `hq.face` (or stops within 4 blocks of it): 5.01. Three seconds of nothing. |
| Lights | `CAGE_LIGHTS` come on in banks from the far end toward the player, each bank with a heavy breaker clunk, about half a second apart, the last bank the one on the face. The eyes stay dark. Let it stand for three seconds before anyone speaks. `#beat 50`. |
| | 5.02, 5.03. **WAIT.** |
| The father | `BOOTH_LIGHTS` on. Gendo is standing at `hq.booth`, already looking down. A beat. 5.04. 5.05. **WAIT.** `#beat 51`. `#present_gendo 1`. |
| The order | 5.06 to 5.12. Misato steps forward on 5.07; Ritsuko does not move. On 5.12 Ritsuko turns to the player. **WAIT.** |
| | 5.13 to 5.17. On 5.17 Misato looks at the floor. 5.18, 5.19. **WAIT.** 5.20. `#beat 52`. |
| First hit | Impact: a deep blow from above, the cage lights flicker (a third of the banks off and on), dust falls in the beams, chains swing, the lake rings. 5.21. 5.22. 5.23. Misato turns to the player: 5.24. **WAIT.** If the player agrees here, go to *Yes*. |
| Rei | 5.25 into the handset, 5.26, 5.27. 5.28 on the intercom. 5.29, 5.30. The side door at `hq.gurney_in` opens; the gurney rolls to `hq.gurney_mark`, wheels squeaking, medics either side. Rei tries to sit up: 5.31. `#present_rei 1`. |
| Second hit | Harder. Every light goes out for one second and comes back. A lighting rig tears loose at `debris_2` and falls. Rei is thrown from the gurney onto the deck. The hand comes up out of the lake (raised version, placed from `hand_cells()`; never cleared by box) and the rig breaks on it. **The eyes light, for the first time, for as long as the hand is up, and go dark again.** Medics back away. 5.32. 5.33. 5.34. 5.35. `#beat 53`. |
| The girl | When the player comes within 2 blocks of Rei: 5.36, 5.37, 5.38. **WAIT FOR YES.** Nudges some seconds apart, in this order, then repeating the last two: 5.39, 5.40, 5.41. Each nudge after 5.40 is followed by a distant impact. |
| Yes | Everything stops. The alarm cuts. 5.42. 5.43. Ritsuko walks toward the door; Misato stays by Rei. Gendo has not moved and says nothing: hold on him for two seconds before the booth lights go out. As the player follows Ritsuko: 5.44 from behind. `#beat 54`. Black. `EVANGELION  UNIT 01`. |

## Scene 6. The plug

| Cue | What happens |
|---|---|
| Sealed | Out of black, seated at `hq.plug_seat`. The hatch closes. Total dark. Own breathing. 6.01 muffled through the hull. Machinery. 6.02. Dim instrument light. 6.03. `#beat 60`. `#present` misato, ritsuko, gendo = 2. |
| The fluid | 6.04. Amber rises from the floor past the player's eyes; sound goes dull and close. 6.05, 6.06. **WAIT** (optional: go on after 6 seconds). |
| Contact | 6.07. The plug walls shimmer and go clear: the player is now looking down the bridge from where the giant's eyes are, with Misato and Ritsuko small on the deck below and the booth off to one side. 6.08. A rising tone that locks: 6.09. 6.10, 6.11. |
| Release | 6.12. 6.13 with the bolts going one by one, each a hammer blow, and the bridge sliding away. 6.14. Through black to the launch pad (`hq.pad`), player now at giant scale, looking up the shaft. 6.15. `#beat 61`. |
| The word | 6.16. A long pause. 6.17. 6.18. A charge whine climbing. 6.19. |
| Launch | The player goes up the shaft fast and smoothly (a physics push, not teleports), ring lights streaking past, roar. White at the top. |
| Surface | Night. The lift locks at `city.launch_top` with a clang. Wind. Far down the avenue, the Angel, already turning. 6.20. Quiet. 6.21. `#beat 70`. Hand over to `angel:fight/start`. |

## Scene 7. The fight

As built in `tools/fight`. After `angel:story/fight_done {result:"won"}`: the cross of light, 7.15 to 7.18, hold
on the empty avenue and the dawn starting, then `TO BE CONTINUED`. After the card the player wakes at human
size in the cage, lights on, everyone present, `#beat 80`, free to talk to anyone.
