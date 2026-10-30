# Glass cards

A translucent card groups information over artwork. Use it for short copy or a metric over a busy scene.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `x, y, w, h, r` | Card geometry; r=22 |
| `title, body, font` | Text; sans-serif |
| `t0, dur` | 0, .65 seconds |
| `tint` | translucent white |
| `backdrop` | Optional source canvas for real clipped blur |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  FX.glassCard(ctx, t, {x:70,y:350,w:400,h:180,title:"Signal",body:"Now in motion"});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Keep contrast high over detailed footage.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
