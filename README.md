# clipmeter

Measure a short video with numbers instead of guessing, then copy the style.

```
python clipmeter.py reference1.mp4 reference2.mp4 --words --json refs.json
```

Prints length, hard cuts per 10 s, brightness, contrast, saturation, share of moving frames, loudness (LUFS), silence %, and with `--words` the speaking speed. With several clips it prints the average: that is your rule book.

Needs `ffmpeg` and `ffprobe` on the PATH. `--words` also needs `faster-whisper`.
Works as a Claude Code skill: copy this folder to `.claude/skills/clipmeter/` and ask Claude to "measure these reference clips and build me a rule book".

Part of the tools I built while making my own Jarvis. Questions and builds: discord.gg/6PdHN4pz3q
