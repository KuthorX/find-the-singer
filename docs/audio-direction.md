# Audio direction: "The unfinished song"

## Concept

The art direction says the game is a page from a fan's music notebook and the hero is a doodled note looking for its singer. The audio takes that literally: the singer is missing, so her song is missing too.

- The gameplay track is a bright, Vocaloid-style J-pop arrangement in **D major**. Its melody starts out with holes in it.
- Each letter a fan left in the level fills more of the melody in. Once you have collected nearly all of them, a harmony voice and a bell join the chorus.
- The level-complete jingle is the first time the hook is sung all the way to the tonic.
- The title-screen lullaby plays the same hook on a music box, but its last pass "forgets" the ending and stops on the dominant. The song stays unfinished until you find the singer.

Every sound effect stays inside the same world. There is one gel pen on paper (taps, scribbles, tears) plus the song's own instruments (music box, glass, harp, pizzicato and xylophone tones rendered from the same presets), and the pitched effects are tuned to D major so they never clash with the music. The single accent colour means "the song", and the accent sound is the melody voice.

## Instrumentation

The notes, and so the singer's melody and the title hook, are written in `tools/audio/score.py`. The 2026-10 rescore kept every note and re-orchestrated them (`tools/audio/orchestra.py`) with Serum 2 and Vital presets and the MS Basic SoundFont, rendered offline. Music and SFX were composed programmatically by AI (Claude).

| Role | Instrument | Why |
|---|---|---|
| The singer (missing) | Serum 2 **VOX - Synth Pop Choir** (vocal synth lead, light delay and hall) doubled by Serum 2 **PL - Xylo Pluck** | A synthetic pop voice stands in for a Vocaloid; the xylophone gives each note a clear attack, so the gaps are audible |
| Harmony (all letters) | Serum 2 **WIND - Flute** a diatonic third below, plus Serum 2 **BL - Kinderjoy** bell on chorus downbeats | The fans join once their letters are read |
| Rhythm | Serum 2 **KY - Delicacy** keys comping (pushed 1, 2&, 3, 4 pattern) | A pop pulse that stays notebook-quiet |
| Bass | MS Basic finger bass (GM 33), root / push / fifth / octave | Bouncy, matches the platforming |
| Kit | MS Basic GM drum kit: kick, side-stick (clap in the chorus), soft closed hats, shaker | Light enough for dense SFX |
| Colour | Serum 2 **KY - Harpsichord** off-beat stabs (pre-chorus and chorus; the "baroque staff"), Vital **Strings Section** pad (chorus), Kinderjoy music-box arpeggio (intro, verse, tag) | The music box is the "waiting" motif shared with the title |
| Title lullaby | Delicacy keys, Kinderjoy music box (the hook), Synth Pop Choir humming the hook an octave down (the singer's voice, far away), Vital Strings Section, MS Basic acoustic bass | Same voice and music box as the level, slower and softer |

## Tracks

| File | Role | Tempo / key / form | Length | Loudness |
|---|---|---|---|---|
| `audio/music/menu.ogg` | Title, and the screen after each jingle | 90 BPM, D major, canon progression D–A/C#–Bm–F#m/A–G–D/F#–G–A ×4. The keys play alone first; then the music box plays the hook; then the singer's voice hums it an octave lower; then the music box plays it again but forgets the last two bars | 85.33 s (32 bars), seamless loop | -18.0 LUFS, peak -3.9 dBTP |
| `audio/music/play_base.ogg` | Gameplay band (always on) | 120 BPM, D major, 48 bars: intro 4, verse 12, pre-chorus 8, royal-road chorus IV–V–iii–vi 16, tag 8 | 96.00 s, seamless loop | -23.4 LUFS alone |
| `audio/music/play_mel1.ogg` | Melody skeleton (always on): the first note of each bar and every long note | same | 96.00 s | stereo, -20.1 LUFS alone |
| `audio/music/play_mel2.ogg` | Remaining on-beat melody notes (from 30 % of the letters) | same | 96.00 s | stereo |
| `audio/music/play_mel3.ogg` | Off-beat / syncopated melody notes (from 60 %) | same | 96.00 s | stereo |
| `audio/music/play_mel4.ogg` | Chorus harmony and bell (from 90 %) | same | 96.00 s | stereo |
| `audio/sfx/jingle_complete.ogg` | Finish screen | Hook over G→A resolving to D, with a bell roll | 6.16 s | -17.0 LUFS |
| `audio/sfx/jingle_gameover.ogg` | Game Over screen | Music box tries the hook in D minor and runs down (pitch and tempo sag like a spring unwinding) | 4.94 s | -17.0 LUFS |

All five gameplay stems start on the same frame and loop together. With every stem on, the full mix measures -18.0 LUFS (peak -4.1 dBTP); the base plus the melody skeleton is -20.4 LUFS. The vocal lead is wide, so the melody stems are stereo Ogg Vorbis (a mono fold-down lost about 3 dB). The level has 9 letters, so the stems unlock at 3, 6 and 9 letters. Each one fades in over 1.5 s.

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
| Fragile measure redrawn | `fragile_restore.ogg` | Pencil scribble settling on a soft music-box D (quiet, distance-attenuated) |
| Letter pickup | `letter.ogg` | Envelope flick plus a music-box bell. Successive letters climb the D pentatonic (D5 … D7), so the letters themselves sing a scale |
| Checkpoint | `checkpoint.ogg` | D6 + A6 + D7 bells with a low D pluck ("the song is remembered here") |
| Fall / hurt | `hurt.wav` | A sour Eb→D minor second sagging down, with a dry crumple. Never harsh |
| Respawn | `respawn.ogg` | A quick scribble, then a music-box arpeggio D–F#–A–D |
| Extra life (every 10 letters) | `life_up.ogg` | Sparkle arpeggio up to F#7 |
| UI hover / focus | `ui_hover.wav` | Tiny pencil tick plus A6 blip (the quietest sound) |
| UI click | `ui_click.wav` | Pen click plus an A5 pluck |
| Start / Retry | `ui_confirm.wav` | D6→A6 bells |
| Back / Exit | `ui_back.wav` | A5→D5 bells |
| Language / mute / effects-slider tick | `ui_toggle.wav` | Short tick plus an E6 blip |

All SFX are 44.1 kHz 16-bit mono WAV, 0.08–1.1 s long. They are normalized to a short-term loudness hierarchy: rewards around -16 LUFS, movement -18 to -21, UI -20 to -23, hover -29. True peak is capped at -1.5 dBTP. Each effect layers numpy pen-and-paper foley with pitched tones from a rendered tone bank (`tools/audio/sfx_bank.py`): Serum 2 Kinderjoy (music box) and Xylo Pluck, Vital Ceramic (glass ticks), MS Basic harp and pizzicato.

## Runtime (`scripts/AudioManager.gd`, autoload)

- **Buses** (`default_bus_layout.tres`): Master → Music, SFX. Mute silences Master.
- **Settings**: music volume (default 0.7), effects volume (0.8) and mute. They are saved to `user://settings.cfg` in the `[audio]` section, next to the language. You can change them from the title screen (two ink sliders with note-head handles, plus a Mute/Unmute word), and the **M** key toggles mute anywhere. Labels are in `i18n/translations.csv` (`AUDIO_*`).
- **Music**: the title plays `menu`. A level starts all gameplay stems on the same frame. Finish and Game Over fade the band out, play their jingle, then return to `menu`.
- **Web**: music plays as Web Audio samples (the build has no threads). The stems are decoded in the background while the title screen is up, so Start does not stall. The browser's autoplay rule still applies: sound starts after the first click or key press.
- UI sounds are attached automatically to every `BaseButton`. There is a 250 ms quiet window when a screen opens, so the focus it grabs on open makes no sound.

## Regenerating

```sh
PY="arch -arm64 /tmp/audiokit/venv/bin/python"
$PY tools/audio/render.py [build_dir]          # score -> MIDI -> Vital/Serum 2/MS Basic -> mastered Ogg Vorbis, plus the SFX tone bank
$PY tools/audio/render.py [build_dir] --master-only   # re-mix from the rendered stems (balance trims live in render.py)
$PY tools/audio/sfx.py audio/sfx [build_dir]/stems/bank   # SFX: numpy foley + tone bank -> audio/sfx/*.wav
python3 tools/audio/analyze.py                 # duration / LUFS / true peak / loop-seam report + spectrograms
```

Requirements: the offline audiokit toolchain in `/tmp/audiokit` (pedalboard hosting Vital and Serum 2 headless, FluidSynth with `MS Basic.sf3`, numpy/scipy/soundfile with libsndfile Vorbis), `ffmpeg` (analysis only) and `lockf`. `render.py` renders every spec in one process under the shared `/tmp/audiokit/render.lock`. Nothing is played and no plugin window is opened. Loops are rendered once with a tail that is folded back onto the loop start, so reverb and releases wrap across the seam. The loop flags are set in the `.import` files. Sources and licenses are listed in `audio/LICENSES.md`.
