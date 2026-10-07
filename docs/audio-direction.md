# Audio direction: "The unfinished song"

## Concept

The art direction says the game is a page from a fan's music notebook and the hero is a doodled note looking for its singer. The audio takes that literally: the singer is missing, so her song is missing too.

- The gameplay track is a bright, Vocaloid-style J-pop arrangement in **D major**. Its melody starts out with holes in it.
- Each letter a fan left in the level fills more of the melody in. Once you have collected nearly all of them, a harmony voice and a glockenspiel join the chorus.
- The level-complete jingle is the first time the hook is sung all the way to the tonic.
- The title-screen lullaby plays the same hook on a music box, but its last pass "forgets" the ending and stops on the dominant. The song stays unfinished until you find the singer.

Every sound effect stays inside the same world. There is one gel pen on paper (taps, scribbles, tears) plus the song's own instruments (music box and celesta bells, plucks), and the pitched effects are tuned to D major so they never clash with the music. The single accent colour means "the song", and the accent sound is the melody voice.

## Instrumentation

| Role | Instrument (GM, MS Basic SoundFont) | Why |
|---|---|---|
| The singer (missing) | Synth Voice doubled by celesta | A synthetic voice stands in for a Vocaloid; the celesta gives each note a clear attack, so the gaps are audible |
| Harmony (all letters) | Voice Oohs a diatonic third below, plus glockenspiel on downbeats | The "choir of fans" joins once their letters are read |
| Rhythm | Acoustic piano comping (pushed 1, 2&, 3, 4 pattern) | A pop pulse that stays notebook-quiet |
| Bass | Acoustic bass, root / push / fifth / octave | Bouncy, matches the platforming |
| Kit | Kick, side-stick (clap in the chorus), soft closed hats, shaker | Light enough for dense SFX |
| Colour | Pizzicato off-beat stabs (pre-chorus and chorus), string pad (chorus), music-box arpeggio (intro, verse, tag) | The music box is the "waiting" motif shared with the title |

## Tracks

| File | Role | Tempo / key / form | Length | Loudness |
|---|---|---|---|---|
| `audio/music/menu.mp3` | Title, and the screen after each jingle | 90 BPM, D major, canon progression D–A/C#–Bm–F#m/A–G–D/F#–G–A ×4. The piano plays alone first; then the music box plays the hook; then Voice Oohs hum it an octave lower; then the music box plays it again but forgets the last two bars | 85.33 s (32 bars), seamless loop | -18 LUFS, peak -4.4 dBTP |
| `audio/music/play_base.mp3` | Gameplay band (always on) | 120 BPM, D major, 48 bars: intro 4, verse 12, pre-chorus 8, royal-road chorus IV–V–iii–vi 16, tag 8 | 96.00 s, seamless loop | -21.4 LUFS alone |
| `audio/music/play_mel1.mp3` | Melody skeleton (always on): the first note of each bar and every long note | same | 96.00 s | mono |
| `audio/music/play_mel2.mp3` | Remaining on-beat melody notes (from 30 % of the letters) | same | 96.00 s | mono |
| `audio/music/play_mel3.mp3` | Off-beat / syncopated melody notes (from 60 %) | same | 96.00 s | mono |
| `audio/music/play_mel4.mp3` | Chorus harmony and glockenspiel (from 90 %) | same | 96.00 s | mono |
| `audio/sfx/jingle_complete.mp3` | Finish screen | Hook over G→A resolving to D, with a glockenspiel roll | 5.25 s | -17.4 LUFS |
| `audio/sfx/jingle_gameover.mp3` | Game Over screen | Music box tries the hook in D minor and runs down (pitch and tempo sag like a spring unwinding) | 3.36 s | -17.4 LUFS |

All five gameplay stems start on the same frame and loop together. With every stem on, the full mix measures -18.0 LUFS (peak -3.7 dBTP). The level has 9 letters, so the stems unlock at 3, 6 and 9 letters. Each one fades in over 1.5 s.

## Sound effects

Each platform's notation has its own landing voice. The landing volume scales with fall speed, and tiny skitter hops stay silent.

| Event | File | Sound |
|---|---|---|
| Jump | `jump.wav` | Soft sine/triangle chirp A4→E5 plus a paper flick |
| Land on a plain measure | `land_measure.wav` | Pen-tip thump on the desk plus a low D pizzicato |
| Land on a fragile (dashed) measure | `land_fragile.wav` | Brittle glassy tick on D7 with a G#6 tritone shadow, and paper crinkle |
| Land on a repeat-sign (moving) measure | `land_repeat.wav` | Two marimba notes, A4 then D5 ("again!") |
| Land on a glissando (slippery) measure | `land_gliss.wav` | Quick harp run up the D pentatonic |
| Land on a sagging spring measure | `bounce.wav` | Marcato thump plus a rising "boing" D4→D5 with a little wobble |
| Fragile measure starts to split | `fragile_crack.wav` | Paper crackle plus a small bending creak |
| Fragile measure disappears | `fragile_break.wav` | Paper tear rising from low to high, then a thud (quieter with distance from the camera) |
| Fragile measure redrawn | `fragile_restore.wav` | Pencil scribble settling on a soft celesta D (quiet, distance-attenuated) |
| Letter pickup | `letter.wav` | Envelope flick plus a music-box bell. Successive letters climb the D pentatonic (D5 … D7), so the letters themselves sing a scale |
| Checkpoint | `checkpoint.wav` | D6 + A6 + D7 bells with a low D pluck ("the song is remembered here") |
| Fall / hurt | `hurt.wav` | A sour Eb→D minor second sagging down, with a dry crumple. Never harsh |
| Respawn | `respawn.wav` | A quick scribble, then a music-box arpeggio D–F#–A–D |
| Extra life (every 10 letters) | `life_up.wav` | Sparkle arpeggio up to F#7 |
| UI hover / focus | `ui_hover.wav` | Tiny pencil tick plus A6 blip (the quietest sound) |
| UI click | `ui_click.wav` | Pen click plus an A5 pluck |
| Start / Retry | `ui_confirm.wav` | D6→A6 bells |
| Back / Exit | `ui_back.wav` | A5→D5 bells |
| Language / mute / effects-slider tick | `ui_toggle.wav` | Short tick plus an E6 blip |

All SFX are 44.1 kHz 16-bit mono WAV, 0.08–1.1 s long. They are normalized to a short-term loudness hierarchy: rewards around -17 LUFS, movement -19 to -22, UI -21 to -24, hover -30. True peak is capped at -1.5 dBTP.

## Runtime (`scripts/AudioManager.gd`, autoload)

- **Buses** (`default_bus_layout.tres`): Master → Music, SFX. Mute silences Master.
- **Settings**: music volume (default 0.7), effects volume (0.8) and mute. They are saved to `user://settings.cfg` in the `[audio]` section, next to the language. You can change them from the title screen (two ink sliders with note-head handles, plus a Mute/Unmute word), and the **M** key toggles mute anywhere. Labels are in `i18n/translations.csv` (`AUDIO_*`).
- **Music**: the title plays `menu`. A level starts all gameplay stems on the same frame. Finish and Game Over fade the band out, play their jingle, then return to `menu`.
- **Web**: music plays as Web Audio samples (the build has no threads). The stems are decoded in the background while the title screen is up, so Start does not stall. The browser's autoplay rule still applies: sound starts after the first click or key press.
- UI sounds are attached automatically to every `BaseButton`. There is a 250 ms quiet window when a screen opens, so the focus it grabs on open makes no sound.

## Regenerating

```sh
python3 tools/audio/render.py     # score -> MIDI -> FluidSynth -> mastered mp3 (music + jingles)
python3 tools/audio/sfx.py        # synthesized SFX -> audio/sfx/*.wav
python3 tools/audio/analyze.py    # duration / LUFS / true peak / loop-seam report + spectrograms
```

Requirements: Python 3 with numpy and scipy, `fluidsynth`, `lame`, `ffmpeg`, and the MS Basic SoundFont from MuseScore 4 (the path is set in `render.py`). Loops are rendered three times back to back and the middle copy is kept, so reverb tails wrap across the seam. The loop flags are set in the `.import` files. Sources and licenses are listed in `audio/LICENSES.md`.
