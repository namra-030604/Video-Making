---
component: vertical-9-16-framing
description: >-
  Design or convert video for 9:16 vertical platforms (Shorts, Reels, TikTok) without losing context: zone layout
  (top card, hero, caption safe zone, platform UI margins), and landscape-to-vertical conversion recipes with
  ffmpeg (blurred fill, stacked split, tracked crop, letterbox with title). Use when making 1080x1920 output or
  reframing 16:9 footage.
---
# Vertical 9:16 framing

## Native vertical layout (1080x1920; scale fractions for 540x960 drafts)
| Zone | Fraction of height | Use |
|---|---|---|
| Top margin | 0-0.08 | keep clear (status bar, platform header) |
| Top card | 0.08-0.25 | hook line / title bar, 3-6 words |
| Hero | 0.25-0.68 | the one thing to look at; faces live here |
| Captions | 0.70-0.90 | karaoke subtitles (`subtitles.safe_top/safe_bottom`) |
| Bottom UI | 0.90-1.0 | keep clear (description, progress bar) |
Keep ~6% side margins and ~12% clear on the right edge where like/comment buttons sit (lower half).

## Converting landscape footage (do not hard centre-crop: it cuts people and context)
Pick by content; test with a still first (`ffmpeg -ss 5 -i in.mp4 -frames:v 1 test.png` after the filter).
1. **Blurred fill (safest, keeps the whole frame):**
   `ffmpeg -i in.mp4 -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:2,eq=brightness=-0.08[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2*0.85" -c:a copy out.mp4`
2. **Stacked split (two people / screen + face):** crop the two regions and `vstack` them, 1080x960 each.
3. **Moving crop (one subject that moves):** compute a per-second x centre (manually or from a detector), smooth it
   (moving average over ~1 s, max ~150 px/s), and use `crop=ih*9/16:ih:x(t):0` via `sendcmd` or render the crop in
   the canvas page where the footage is drawn with `MS.seekVideo` and an eased x.
4. **Letterbox + title:** scale to 1080 wide, put the hook text in the top card and captions below the footage.
Always check: faces fully inside the hero zone, no caption over a face, on-screen text from the source not cut.

## Code-drawn scenes
Design vertical from the start (`examples/hello-world` is 540x960): stack elements vertically, big type (title
>= 64 px at 1080 wide), at most 2 focal elements per frame. For 16:9 and 9:16 from one project, make layout a
function of `W/H` instead of fixed coordinates.
