# Art direction: "Staff-paper guestbook"

## Seed-derived direction

The seed was a 256-character random alphanumeric string. These are the patterns I read from it:

- **Round glyphs and stems.** The string is full of `O`, `Q`, `0` and `I`, `1`, `l`. Round heads next to vertical strokes look like note heads with stems. That makes the protagonist a note head with a stem, and it gives the circle motif (eyes, wax seals, metronome).
- **Long letter runs broken by short digit bursts** (`...VNHVB297I1QAI1...`). This becomes the layout skeleton: large quiet fields of paper, then small dense clusters of information. Layouts are asymmetric, with the text set left and the illustration set right.
- **Mostly mixed-case letters and only a few digits.** This sets the palette: two inks on paper and exactly one accent, used rarely.
- **No punctuation at all, unbroken.** This sets the type personality: one continuous hand, so everything looks written by the same pen, with no boxes or frames.

## 15 shallow directions

1. Staff-paper guestbook: the world is a page of the fan booth's music notebook, and everything is drawn in gel-pen ink.
2. Cassette J-card: levels are folded inlay cards, and platforms are tape spools.
3. Postal sorting office: envelopes, postmarks and stamps are the terrain.
4. Glow-stick concert: neon light trails on a black stage.
5. Karaoke subtitle bar: lyric syllables light up and become platforms.
6. Kamishibai paper theatre: layered cut-paper scenery slides in.
7. *(unreasonable)* The hero lives inside the barcode on the album's back cover.
8. *(unreasonable)* The world is a spectrogram, and platforms are frequency peaks.
9. *(unreasonable)* Everything is finger-drawn on a fogged train window.
10. *(unreasonable)* The level is a vinyl groove, laid out as a spiral.
11. *(unreasonable)* Alphabet soup: letters float in broth.
12. *(unreasonable)* Thermal receipt paper, printed in monospace by a ticket machine.
13. Risograph zine with two misregistered inks.
14. Carved seal stamps in vermilion paste.
15. Origami: everything is folded from the fans' letters.

## Pick: #1, staff-paper guestbook

The owner's own design notes say that fans wrote messages in a large notebook at an offline booth, and that platforms are pens, chalk, quills and erasers. Direction #1 makes those notes literal: the whole game is a page of that notebook, and the hero is a small doodled note looking for its singer.

## Build brief (<=200 words)

**Aesthetic:** a gel-pen doodle drawn on cream music-manuscript paper. It should look hand-made and quiet, like someone's notebook rather than a game UI.

**Palette:** paper `#F4EEE1`, gel ink `#1E2246`, and one accent, Tianyi blue `#66CCFF`. The accent means only "the song" and appears on the hero's flag and the checkpoint pennant. Red pen `#D64034` is for danger only (fragile cracks, Game Over).

**Layout:** asymmetric. Text is left-aligned and sits on the staff lines. Illustration goes on the right. There are no boxes or panels, and the empty paper is left as breathing room.

**Type:** Caveat for Latin and LXGW WenKai for CJK (subset and renamed). Both are handwritten. Buttons are bare words, and an ink pen-stroke underline marks focus and hover.

**Material:** paper grain and fibres, and one pen everywhere: solid gel-ink fills with the same roughened, ink-bled edge.

**Forbidden:** gradients, glows, glassmorphism, rounded cards, drop shadows, floating geometric shapes, more than one accent, boxed buttons, and Quit on web.

## Revisions from the critic loop

The critic scored the rounds 4, 5, 5, 5, 5, 5 out of 10. These are the changes I kept:

- **One pen.** Hatching, stipple, gloss highlights and blush are gone. Every asset now goes through the same ink-bleed edge pass (`roughen` in `tools/art/gen_art.py`).
- **The staff became structure.**
  - Menus share one hand-ruled staff, read left to right: clef, the hero, the final barline. Title: the hero stands on the staff, looking ahead. Finish: the hero, happy, has reached the end of the staff. Game Over: the hero, hurt, has fallen off it.
  - Platforms are now notated measures, and the notation tells you the platform type. A plain measure is static. A dashed measure with a red crack is fragile. Repeat signs mean it moves back and forth. Sagging lines with marcato accents mean it bounces. A glissando means it is slippery. These replace the pen, chalk, quill, eraser and ruler objects.
- **No printed staves behind gameplay.** Repeated background staves read as ruled paper, so the world now sits on a plain page.
- **Stats as icons.** The finish page reuses the HUD's metronome, envelope and note icons instead of text labels.

I did not adopt the critic's repeated request to make the staff lines themselves the ground. That would mean redesigning the level geometry, and gameplay was out of scope.
