# Kinetic text

Kinetic text brings words in one at a time. Use it for short titles and energetic emphasis.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `words` | String or word array |
| `x, y` | Baseline center |
| `size, font, color` | 54, sans-serif, white |
| `t0, stagger, dur` | 0, .12, .45 seconds |
| `mode` | pop, slide, or drop |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  FX.kineticText(ctx, t, {words:"MAKE IT MOVE",x:270,y:450,size:52,t0:0,mode:"pop"});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Keep the phrase short.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
