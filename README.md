# Find The Singer / 寻找歌姬

Please find the Grenyes. A small Godot 4 platformer — play it on [itch.io](https://kuthorx.itch.io/find-the-singer).

## Languages

The game ships in **English** and **简体中文**.

- On first launch the language follows the system/browser locale (Chinese → 中文, anything else → English).
- Use the **中文 / EN** button in the top-right corner of the title screen to switch; the choice is saved to `user://settings.cfg`.
- All UI text lives in `i18n/translations.csv` (`keys,zh,en`). Add a key there and use it as a Control's text (auto-translated) or via `tr()` in scripts.
- Chinese glyphs are rendered by the bundled ZCOOL KuaiLe font (SIL OFL, see `fonts/OFL-ZCOOLKuaiLe.txt`), configured as a fallback of Emily's Candy.
