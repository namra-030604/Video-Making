# Light and glow

Blurred additive passes make an element luminous; a specular band can travel over a surface. Use both as brief highlights.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `drawFn` | Draw callback receiving ctx |
| `color, blur, passes` | cyan, 22, 3 |
| `x, y, w, h` | Sweep bounds |
| `t0, dur, angle` | 0, .8, -.3 radians |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  ctx.fillStyle="#70f8ff";
  FX.glow(ctx,c=>c.fillRect(200,400,140,80),{color:"#70f8ff",blur:22});
  FX.lightSweep(ctx,t,{x:200,y:400,w:140,h:80,t0:0,dur:.8});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Keep enough contrast around glowing text.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
