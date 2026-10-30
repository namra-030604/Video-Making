# Counters

A counter makes a changing quantity legible while it moves. Use it for one important metric at a time.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `from, to` | Starting and ending value; 0, required |
| `x, y, size` | Center and text size |
| `font, color` | sans-serif, white |
| `t0, dur` | 0, 1 second |
| `decimals, prefix, suffix` | 0, empty, empty |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  FX.counter(ctx, t, {from:0,to:12840,x:270,y:450,size:76,suffix:" views"});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Hold the final number long enough to read.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
