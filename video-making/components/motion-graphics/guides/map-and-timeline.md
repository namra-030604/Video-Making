# Map and timeline

A route traces already projected points; a timeline reveals ordered events. Use them to show travel or a sequence in time.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `points, color, dash` | Projected route, cyan, solid |
| `t0, dur` | 0, 1 second |
| `x, y, w` | Timeline axis |
| `events` | `{label,at}` where at is 0..1 |
| `font` | sans-serif |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  FX.mapRoute(ctx,t,{points:[[80,600],[180,480],[350,520],[460,360]],color:"#72e6d1"});
  FX.timeline(ctx,t,{x:70,y:700,w:400,events:[{label:"A",at:.1},{label:"B",at:.5},{label:"C",at:.9}]});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

For real geography, `bash install.sh --with-maps` adds three npm modules (`world-atlas` data, `topojson-client`, `d3-geo`). Convert world-atlas TopoJSON with topojson-client, choose a d3-geo projection, then draw with `d3.geoPath(projection, ctx)` before passing projected route points to `FX.mapRoute`.

## Timing and design

- Keep route and event labels large at phone size.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
