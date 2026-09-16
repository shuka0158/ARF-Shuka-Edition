# Passport custom character art

`skull.png`, `hacker.png`, `robot.png` are real hand-drawn pixel art (not
programmatically generated), sourced from the Flipper Zero community pack:

- Repo: https://github.com/Kuronons/FZ_graphics
- License: CC0 1.0 Universal (public domain) — see that repo's LICENSE
- Originals: `Skull.png`, `Neuromancer.png`, `ED-209.png` from
  "Passport profile pictures/Profile pictures (.png files - 46x49px)"

Already sized 46x49 and converted to 1-bit; `scripts/install_passport_chars.py`
copies them into `assets/icons/Passport/` in the ARF clone at build time,
renamed per character/mood so they match what `passport.c` expects
(`I_<char>_<mood>1_46x49`). None of these three have separate mood art
upstream, so all three moods reuse the same portrait per character — only
the stock dolphin art (already shipped by ARF) actually varies by mood.
