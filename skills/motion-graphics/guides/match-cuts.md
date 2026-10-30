# Match cuts

A match cut keeps one shape or position recognizable across two scenes. Align the shared object at the cut, then change its surrounding context.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `cut, dur` | Center time and blend span; .3 seconds |
| `a, b, k` | Scene A weight, scene B weight, progress |
| `fromRect, toRect` | `{x,y,w,h}` or `[x,y,w,h]` |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  const {a,b,k} = FX.matchCut(t, {cut:.5,dur:.3});
  const m = FX.matchTransform(k, [120,400,80,80], [230,390,80,80]);
  ctx.globalAlpha = a; ctx.fillStyle = "#4ad8c0"; ctx.fillRect(120,400,80,80);
  ctx.globalAlpha = b; ctx.fillStyle = "#ff9b72"; ctx.fillRect(m.x,m.y,80*m.scale,80*m.scale);
  ctx.globalAlpha = 1;
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Align a circle or card center on both sides of the cut.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
