# Screen shake

A short decaying offset gives an impact weight. Use it sparingly so text remains readable.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `t0, dur` | Start and length; 0, .5 seconds |
| `amp, freq` | Pixel amplitude 12, cycles 18 |
| `seed` | Stable pattern; 1 |
| `x, y, rot` | Returned offsets |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  const s=FX.shake(t,{t0:0,dur:.45,amp:12,freq:18,seed:2});
  ctx.save(); ctx.translate(s.x,s.y); ctx.rotate(s.rot);
  ctx.fillStyle="#ff9b72"; ctx.fillRect(180,380,180,180); ctx.restore();
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Shake a contained layer if subtitles must stay steady.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
