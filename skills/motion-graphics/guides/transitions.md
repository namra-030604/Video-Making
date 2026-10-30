# Transitions

A transition reveals scene B through a moving mask or blend. Use it to connect two related scenes without a jarring jump.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `type` | wipe, circle, slide, dissolve, blinds |
| `cut, dur` | Start and duration; .5 seconds |
| `drawA, drawB` | Scene callbacks receiving ctx |
| `W, H` | Canvas dimensions |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  FX.transition(ctx, t, {type:"circle",cut:0,dur:.7,W:540,H:960,
    drawA:c=>{c.fillStyle="#18243c";c.fillRect(0,0,540,960);},
    drawB:c=>{c.fillStyle="#d06b85";c.fillRect(0,0,540,960);}});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Place the cut where the new scene has a visual anchor.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
