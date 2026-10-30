# Camera and parallax

A camera transform pans, zooms, or rotates the whole composition. Offset layers by depth for a simple parallax effect.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `W, H` | Canvas dimensions |
| `from, to` | x, y, zoom, rot states |
| `t0, dur, ease` | 0, 1, inOutSine |
| `shake` | Optional FX.shake offset |
| `depth` | Parallax strength 0..1 |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  ctx.save();
  const cam=FX.camera(ctx,t,{W:540,H:960,from:{x:0,y:0,zoom:1},to:{x:50,y:0,zoom:1.2}});
  const p=FX.parallax(.3,cam); ctx.fillStyle="#5be0c8"; ctx.fillRect(180+p.x,400+p.y,180,120);
  ctx.restore();
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Use save and restore around the transform.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
