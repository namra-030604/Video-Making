# Charts

Animated charts turn values into an ordered visual explanation. Bars compare categories; a line shows a sequence.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `x, y, w, h` | Chart rectangle |
| `values, labels, colors` | Bar data and styling |
| `points, color, lineWidth` | Line data and styling |
| `t0, stagger, dur` | Start, bar delay, duration |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  FX.barChart(ctx, t, {x:60,y:350,w:420,h:240,values:[22,48,36],labels:["A","B","C"]});
  FX.lineChart(ctx, t, {x:60,y:650,w:420,h:100,points:[.2,.7,.4,.9],t0:.2});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Scale labels for a phone.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
