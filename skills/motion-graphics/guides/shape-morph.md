# Shape morph

A morph resamples two polygons and interpolates their outlines. Use it for a symbolic transformation between simple silhouettes.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `shapeA, shapeB` | Polygon point lists |
| `t0, dur, ease` | 0, 1, inOutSine |
| `fill` | white |
| `regularPolygon(cx,cy,r,n,rot)` | Basic polygon |
| `star(cx,cy,r1,r2,n)` | Star outline |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  FX.morph(ctx,t,{shapeA:FX.regularPolygon(270,450,90,4),
    shapeB:FX.star(270,450,100,45,5),fill:"#72e6d1"});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Use similarly oriented shapes to avoid twisting.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
