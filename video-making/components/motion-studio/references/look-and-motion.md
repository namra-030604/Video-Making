# Look and motion rules (from the two tutorials, mapped to mslib.js)

## Banned defaults
- A centred title on a gradient. - Everything fading in. - Linear, robotic motion. - Static dead frames.
- Full-screen flashing (accessibility). - Anything covering the title or the hero object.

## Must-haves
- A warm neutral canvas (`MS.palettes.warmNeutral`, `paper`) OR a strong theme (`darkSkyNeon`, `archival`).
- Neon accents (`MS.neon(ctx, drawFn, color)`), used on 1-2 things per beat, not everything.
- UI in ONE theme for the whole video (same radius, shadow, font, colours).
- A cursor driving every change: `MS.cursorAt(keys, t)` + `MS.drawCursor(...)`; a click key at the exact frame
  the UI changes, with a click sfx on the same time in beats.json.
- Strong first 1-2 seconds (hook): something big moves at 0.0 s; a promise or question on screen by 1.5 s.

## Easing (MS.ease / MS.spring / MS.squash / MS.hitWobble)
- slow in/out: `inOutCubic`, `inOutSine`, `inOutExpo` for camera/scene moves.
- arrival with overshoot: `outBack`, `outElastic`, `MS.spring(dt, freq, damp)` for UI pieces and words.
- landing: `outBounce` for objects that drop.
- squash and stretch: `MS.squash(MS.hitWobble(t, tHit))` -> [sx, sy] volume-preserving, on every press/impact.
- overlap: stagger related pieces 0.05-0.12 s apart; never start everything on the same frame.

## Texture and light (post FX, applied in seek() after drawing)
- programmatic film grain: `MS.grain(ctx, t, {amount: 0.05-0.1})` (seeded tile, offset per frame).
- soft bloom: `MS.bloom(ctx, {strength: 0.2-0.6})`.
- light flares: `MS.flare(ctx, x, y, {intensity})` on clicks/reveals, decaying in ~0.3 s.
- chromatic aberration: `MS.chromatic(ctx, px)`, 1-3 px base, short 8-12 px spikes on hits only.
- archival B&W option: `MS.archival(ctx, t)` (grayscale + contrast + seeded flicker, scratches, dust, vignette).
- vignette: `MS.vignette(ctx, 0.3)`.

## Layout devices
- Mixed bold serif + sans kinetic typography: `MS.kineticLine(ctx, [{text, font:'serif'|'sans'|'display'|'mono', color}], t, opts)`.
  The pack always provides Inter and Caveat (`MS.loadPackFonts()`, from `/__vsp/fonts/`). Other families (e.g. Instrument Serif,
  Playfair Display, Space Grotesk, Bebas Neue, JetBrains Mono) work only if installed on your system or added under
  `assets/` with their OFL license; load them in READY with `MS.fontsReady([...])` and check the stills for fallbacks.
- Split screens (animated): `MS.splitScreen(ctx, [draw0, draw1, draw2], k, {vertical})` - panels slide in staggered.
- Paper collage / torn-paper reveals with drop shadows: `MS.paperScrap(...)` (scrap slaps in with shadow),
  `MS.tearReveal(ctx, k, drawNext)` (ragged edge wipe with paper lip + shadow). Use photo cutouts inside scraps.
- Kaleidoscope clone / spin: `MS.kaleidoscope(ctx, sourceCanvas, {cx, cy, segments, rot})` - draw the hero into
  an offscreen buffer (`MS.buf`) then mirror/spin it.
- Dark sky + neon palettes: `darkSkyNeon` (deep navy -> violet gradient, seeded stars, cyan/magenta neon).

## Transitions
- Cut on the beat grid (beats.json `"cut": true`). Mask the outgoing scene (clip path / tear mask / split panels)
  so two scenes' text never overlaps. Whoosh sfx on the transition start, impact on the landing.
