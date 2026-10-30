# Ink and watercolor

Layered low-opacity polygons bloom like ink spreading into paper. Use it as an organic background accent.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `x, y, w, h` | Blot center and extent |
| `color, seed, spread` | red, 1, 1 |
| `t0, dur` | 0, .8 seconds |
| `paperGrain W,H,seed,strength` | Canvas size, 1, .1 |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  FX.inkWash(ctx,t,{x:270,y:460,w:300,h:250,color:"#e87b71",seed:4});
  FX.paperGrain(ctx,{W:540,H:960,seed:4,strength:.08});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Pair with restrained paper grain.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
