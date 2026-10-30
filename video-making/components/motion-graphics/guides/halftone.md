# Halftone

Halftone redraws image luminance as dots. Use it for a print or editorial texture.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `source` | Readable source canvas |
| `x, y, w, h` | Destination; source size by default |
| `cell, angle` | Dot spacing 8, rotation 0 |
| `color, bg` | #111, white |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  const source = document.createElement("canvas"); source.width=540; source.height=960;
  const s=source.getContext("2d"); s.fillStyle="#888"; s.fillRect(0,0,540,960);
  FX.halftone(ctx, source, {x:0,y:0,w:540,h:960,cell:10});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Choose cells large enough to survive downscaling.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
