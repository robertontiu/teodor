# Woodblock (`woodblock`)

**What it is.** A Japanese multi-block colour woodblock print (ukiyo-e), and also the black-and-white woodcut of German Expressionism. It is not a brush medium: each stroke of a tool marks out a carved block, and that block is printed once, as a whole, when the stroke is over. Colours are transparent water-based films laid over the paper and earlier impressions, so overlapping blocks combine like overprinted colour (Kubelka-Munk layers). Nothing can be blended or smudged: `blend` intentions do nothing in this medium.

**Supports.**
- `washi` (default): hosho paper, soft kozo fibre. Long fibres and a cloudy formation show in the paper and in flat colour.
- `coarse`: a heavier, grainier paper for the woodcut. The ink thins out in the paper's hollows and the wood grain shows more strongly.

**Tools** (`"brush": ...` in `strokes`, `free` and `match`):
- `key`: the keyblock line. Draw it like a brush line: it swells with pressure and tapers at both ends, and the carver keeps it standing. It prints dense and crisp, always in register. Usually black (`#1b1a1c`), size 4 to 10. `liner` is accepted as another name for it.
- `block`: a colour block. The area the stroke covers is carved and printed as a flat, slightly uneven film: wood grain, baren mottle, paper fibre, a slightly heavier edge where the pigment pools, and a registration slip of 0 to 2 px against the keyline. The printer mixes the ink to give the colour you ask for over what is already there, as far as a transparent colour can (it can only darken). Set `"density"` to print a fixed film thickness instead (1.0 is roughly the named colour over white paper); `"opacity"` (default 0.3) sets how much the colour covers what is under it; `"grain"` sets the strength of the wood grain; `"registration": 0` removes the slip. This is the default tool, so `match` prints blocks.
- `bokashi`: a graded block, colour wiped into water. Full strength where the stroke starts, fading to the paper where it ends. `"fade": "end"` reverses it, `"both"` makes it strong in the middle. For a Hiroshige sky, draw one very wide stroke (size larger than the canvas width) from just above the top edge down to where the sky should go pale.
- `gouge`: the woodcut gouge. It cuts white out of a black block: print a black block first (a `glaze` with opacity 1, or a `block`), then cut. `"cut": "v"` gives V-gouge wedges (pointed at both ends), `"u"` gives U-gouge channels with rounded ends and a little ink caught on the floor of wide cuts. The default is V for sizes under 14, U otherwise. Edges splinter along the wood grain (horizontal). Cuts show the paper, not earlier colour blocks: to have colour in the cuts, print it after cutting.

**Intentions.**
- `glaze` prints one flat block over the region: its shape is the region (hard carved edge; `feather` only rounds it slightly), and `opacity` sets the film (0.2 is a light tint, 1.0 a full black block).
- `strokes` and `free`: each stroke is its own block, so many small strokes look like many small blocks. Large flat fields read best as a `glaze` region or a few broad `block` strokes.
- `match` works but makes many small overlapping blocks; give it large sizes and use it for the main fields, then add the keyline last.
- Felt state: tension and arousal make keylines and gouge marks jagged and broken (the Expressionist hand); care makes them clean.

**Order of work.** As a printer would: lightest colour blocks first, darker ones on top, bokashi on its own block, keyline last (or first). Woodcut: black block, then gouge.

**Drying and time.** None to speak of: each impression is printed onto damp paper and does not flow afterwards. `dry` does nothing.

**Finishing** (no varnish or fixative):
- `finish seal '{"text": "テオ", "at": "br", "size": 60, "color": "#b8322a"}'`: a printed red seal block with the text cut out in white (one or two characters centred, more in two columns). It replaces a hand signature.
- `finish impression`: the final pressing; printed areas sink slightly into the paper (shown under raking light). With `'{"region": {...}, "height": 1.6}'` it does blind embossing (karazuri): the region is raised without ink.

**Limits.** No mica, no metallic or opaque white body colour (gofun), no wiping of ink off a block after printing. Wood grain always runs horizontally. A gouge over bare paper changes nothing. The core `sign` command still signs like oil; use `finish seal` instead.
