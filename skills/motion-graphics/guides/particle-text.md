# Particle text

Seeded dots fly into sampled glyph pixels. Use it for one brief reveal where a solid word would feel too plain.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `text, x, y` | Word and center |
| `size, font, color` | 64, sans-serif, white |
| `t0, dur` | 0, .8 seconds |
| `count, seed` | 350, 1 |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  FX.particleText(ctx, t, {text:"FORM",x:270,y:450,size:70,count:420,seed:7});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Use a bold font for enough sample points.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
