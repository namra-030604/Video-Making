# Glitch

Glitch offsets source strips and splits color channels. Use it briefly for an electronic accent or a broken signal.

## Parameters

| Parameter | Meaning / default |
|---|---|
| `source` | Source canvas |
| `amount` | Distortion, 0..1; .5 |
| `seed, slices` | Repeatable pattern; 1, 14 |

## Example

```html
<canvas id="art" width="540" height="960"></canvas>
<script src="../fx.js"></script>
<script>
const ctx = document.getElementById("art").getContext("2d");
function renderFrame(t) {
  ctx.clearRect(0,0,540,960);
  const source = document.createElement("canvas"); source.width=540; source.height=960;
  const s=source.getContext("2d"); s.fillStyle="#334"; s.fillRect(0,0,540,960);
  FX.glitch(ctx, source, t, {amount:.5,seed:7,slices:12});
  return {};
}
window.renderFrame = renderFrame;
renderFrame(0.5);
</script>
```

## Timing and design

- Keep it brief and avoid rapid whole-frame flashes.
- Start on a clear visual beat and finish the movement before the next idea.
- Check the midpoint and endpoint at 540 × 960 and phone display size.

## Common mistakes

- Passing wall-clock time or unseeded randomness makes seeks inconsistent.
- Letting motion obscure the main text for too long reduces readability.
