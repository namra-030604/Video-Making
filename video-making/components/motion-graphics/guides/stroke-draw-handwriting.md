# Stroke draw and handwriting

A path is traced by distance, which gives a hand-drawn line a consistent speed. Use it for underlines, circles, and signature-like marks.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `path` | Point list or `{points}` |
| `t0, dur` | 0, 1 second |
| `color, width` | white, 4 pixels |
| `jitter, seed` | 0, 1 |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  FX.strokeDraw(ctx,t,{path:[[100,500],[250,480],[440,500]],color:"#fff",width:5,jitter:2,seed:4});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Use an OFL handwriting font for actual letters and add strokeDraw underlines or circles.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
