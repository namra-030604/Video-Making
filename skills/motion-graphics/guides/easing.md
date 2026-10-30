# Easing

Easing changes the rate of motion so an entrance or camera move feels intentional. Use it for nearly every timed property.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `t, a, b` | Seconds, start, end |
| `ease` | Curve function; default inOutSine |
| `FX.spring(dt,freq,damp)` | Damped overshoot; 3, 5 |
| `FX.cubicBezier(x1,y1,x2,y2)` | Custom curve |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  const k = FX.prog(t, 0, 0.8, FX.ease.outCubic);
  ctx.fillStyle = "#80e6d8"; ctx.fillRect(50 + 300*k, 350, 70, 70);
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Draw a box using the eased progress.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
