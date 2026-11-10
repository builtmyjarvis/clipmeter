---
name: clipmeter
description: Measure short videos (cuts, brightness, contrast, saturation, camera motion, loudness, silence, speaking speed) so you can copy a style from numbers instead of opinions. Use when asked to analyse, compare or reproduce the look of a reference short or clip.
---
# clipmeter: measure, don't guess

Rule: never ask the model what it thinks of a reference video. Make it measure, then recreate the numbers.

## How to use
1. Put 5 to 20 reference clips of ONE style in a folder.
2. Run `python clipmeter.py folder/*.mp4 --words --json refs.json` (needs ffmpeg; `--words` needs `pip install faster-whisper`).
3. Read the AVERAGE line. That is your rule book: length, cuts per 10 s, brightness/contrast/saturation, moving frames, loudness, silence, words per second.
4. Build your own clip, run clipmeter on it, and compare the numbers. Fix the biggest gap first.

## Notes
- Hard cuts are found by scene detection; fast camera moves can be counted as cuts. Check suspicious values by looking at the clip.
- Moving frames % says how often the camera or picture is in motion; very low numbers mean a static, boring look.
- Always look at a few still frames of your clip before rendering the full video.
