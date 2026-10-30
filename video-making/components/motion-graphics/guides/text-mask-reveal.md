# Text mask reveal

A moving rectangular clip uncovers a headline. Use it when the text should feel precise and calm.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `text, x, y` | Headline and center |
| `size, font, color` | 60, sans-serif, white |
| `t0, dur` | 0, .7 seconds |
| `direction` | up or left |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  FX.textMaskReveal(ctx, t, {text:"REVEAL",x:270,y:450,size:68,t0:0,direction:"up"});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Give the mask room around descenders.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
