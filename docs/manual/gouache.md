# Gouache (`gouache`)

**What it is.** Opaque watercolour: gum arabic paint packed with pigment and chalk. It covers what is under it, so you can put light over dark, and it dries fast to a flat, matte, slightly chalky field with crisp edges. It also re-dissolves. A wet stroke over dry gouache lifts some of the paint beneath into the brush, and the stroke goes muddy. As it dries, the value moves a little: darks dry lighter and lights dry slightly darker (about 3 to 5% at the extremes). Code: `studio/v8/media/opaque.py`, class `Gouache`.

**Supports.**
- `illustration_board` (default): smooth rigid board. Flat fields come out clean and dry-brush shows mostly as bristle streaks.
- `watercolour_paper`: cold-press paper with a visible tooth. Dry-brush and starved strokes break on it, and thin paint lets the grain show. It dries a little faster.
- `toned_paper`: mid-toned paper. If the ground you give to `new` is light (luminance above 0.7), the paper becomes a warm grey (`#7d7468`); a darker ground is used as given. Work up from the middle: darks, then the lights on top.

**Tools** (`"brush": ...`):
- `round` (default): a synthetic round. Opaque shapes and lines with crisp edges.
- `flat`: a synthetic flat with slightly rounded corners. Use it for flat, even fields and straight crisp edges. Overlapping parts of one stroke don't stack, so the field stays flat. Diluted, it leaves faint streaks.
- `dry`: dry-brush. Very little paint and almost no water: scratchy, broken bristle marks that skip along the stroke and catch the tooth. It does not lift the paint below.
- `liner`: a small pointed round for fine lines and last light accents. It carries a little more water, so its line runs longer.
- `blend` (used by the `blend` intention): a clean damp brush. It softens and lifts wet or re-dissolvable paint and adds no colour. Use it sparingly, because a real damp brush muddies gouache.
- Other names map to the nearest tool: `filbert` → round, `fan` and `dry_brush` → dry, `detail_round` → liner, `smudge` → blend.

**Parameters that matter** (on any intention that makes strokes):
- `water` (0 to 1, default 0.25; liner 0.4, dry 0.03): how diluted the paint is. Creamy paint (0.1 to 0.3) covers almost fully. At 0.5 and above it turns into a streaky, semi-transparent wash and re-dissolves more of the paint below.
- `react` (default 0.4): how readily dry paint under a wet stroke re-dissolves. `pickup` (default 0.4): how quickly the brush gets dirty from that paint. Turn both down for clean light-over-dark accents.
- `load`: how far a brushload goes. Gouache runs out sooner than oil, and a stroke that runs out or moves fast breaks into dry-brush.
- Felt state: fast, agitated strokes break up and pick up texture; careful strokes stay full and clean.

**Glaze.** In gouache, `glaze` is a wash of diluted gouache: semi-opaque (more body than watercolour), slightly uneven, and its water softens dry paint it crosses. Use it for toned grounds and big underlayers, not for jewel-like glazing.

**Drying and time.** Paint is wet only briefly. At the end of each episode most of the water leaves (65% on board, a little more on paper), so the next episode paints over dry, re-dissolvable paint. Inside one episode, strokes that cross wet paint mix with it a little. `dry` lets time pass. As paint dries it takes on the drying shift.

**Finishing** (no varnish: gouache is framed under glass):
- `finish dry`: dry everything completely. This applies the last of the drying shift; do it before judging values.
- `finish protect '{"amount": 0.5}'`: a light matte protective spray. It also dries the paint and deepens the darks very slightly.
- Final light accents and edge crispening are ordinary strokes: `liner` or a small `flat` with low `water` and `react` set to 0, so they don't lift what is under them.

**Order of work.** A toned `glaze` or the big flat shapes in middle values first, then the darker shapes, then the lights and details on top, and the brightest accents last. Keep repaints to a minimum: every wet pass over dry paint dirties it a little.

**Limits.** There is no real water flow: no blooms, no backruns, no granulation. A very wet wash behaves like a thin opaque film, not like watercolour. The drying shift moves values toward the middle and doesn't model particular pigments. Paint has a little body in the render but never forms impasto, and nothing cracks. The core `sign` command signs the same way as in oil.
