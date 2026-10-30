---
component: motion-graphics
description: Use this component to add kinetic text, particles, charts, glass cards, transitions, glitch, halftone, maps and timelines, camera moves, counters, stroke drawing, ink and watercolor, morphing, glow, shake, or text masks to a code-rendered Canvas2D video.
---

# Motion graphics for Canvas2D

Use `fx.js` as a plain browser script before your composition script: `<script src="fx.js"></script>`. It creates `window.FX`; no import or package install is needed. Pass the canvas context, seek time in seconds, and an options object to each drawing helper. Call `ctx.save()` and `ctx.restore()` around camera transforms and any custom drawing state.

## Render contract

The page has `<canvas id="art" width=W height=H>`. Define `window.ready` as a Promise that resolves after fonts and assets load, set `window.fontLoaded = true` after it resolves, and set `window.DURATION` in seconds. `window.renderFrame(t)` synchronously draws the whole frame at time `t` seconds as a pure function of `t` and returns an object (possibly `{}`) for QC metadata. A Node driver seeks `t = frame/fps`, reads `canvas.toDataURL('image/png')`, and pipes PNGs to ffmpeg. See `gallery/index.html` for a complete offline page.

## Guides

| Technique | Guide | Use |
|---|---|---|
| Easing | [easing](guides/easing.md) | Shape progress with easing, springs, and Bezier curves. |
| Kinetic text | [kinetic text](guides/kinetic-text.md) | Bring words on with stagger and overshoot. |
| Text mask | [text mask reveal](guides/text-mask-reveal.md) | Reveal a headline through a moving window. |
| Particle text | [particle text](guides/particle-text.md) | Assemble a word from seeded glyph particles. |
| Charts | [charts](guides/charts.md) | Draw bars and lines with animated values. |
| Counters | [counters](guides/counters.md) | Count a metric with readable formatting. |
| Glass cards | [glass cards](guides/glass-cards.md) | Put information on a translucent panel. |
| Match cuts | [match cuts](guides/match-cuts.md) | Align a shared shape through a scene change. |
| Transitions | [transitions](guides/transitions.md) | Mask one scene into another. |
| Glitch | [glitch](guides/glitch.md) | Add brief RGB and horizontal displacement. |
| Halftone | [halftone](guides/halftone.md) | Convert a source image into a dot screen. |
| Camera | [camera and parallax](guides/camera-and-parallax.md) | Pan, zoom, rotate, and offset layers. |
| Shake | [screen shake](guides/screen-shake.md) | Give an impact a short decaying jolt. |
| Stroke draw | [stroke draw and handwriting](guides/stroke-draw-handwriting.md) | Animate a line, underline, or hand-drawn mark. |
| Ink wash | [ink and watercolor](guides/ink-watercolor.md) | Bloom layered color on paper texture. |
| Shape morph | [shape morph](guides/shape-morph.md) | Interpolate two polygon silhouettes. |
| Light | [light and glow](guides/light-and-glow.md) | Add luminous edges and specular movement. |
| Maps | [map and timeline](guides/map-and-timeline.md) | Trace a projected route or ordered events. |

## Rules

- Derive each frame from `t` and stable options. Seed variation; never depend on call order or wall time.
- Ease every visible entrance, exit, and camera move. Avoid abrupt stops.
- Keep something changing at least every 0.75 seconds.
- In a 9:16 frame, reserve the top 13% and bottom 22% for cards and subtitles unless the design intends to use them. Keep important text inside the remaining safe area.
- Check type and chart labels at phone size.
- Never use full-screen flashes faster than three per second; rapid flashing can trigger photosensitivity.

## How to verify

Render stills at several `t` values, including before, during, and after each effect. Check that no frame throws an exception, that the frames visibly differ, and that the important text remains readable and inside the intended safe area. Run `node test/check.mjs` for the source and guide checks.
