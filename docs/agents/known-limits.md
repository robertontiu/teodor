# Known limits, hiccups and open directions

Back to the router: [AGENTS.md](../../AGENTS.md). The plan with checkboxes is [docs/proposals-v8.md](../proposals-v8.md); what each painting taught is in [docs/experiments.md](../experiments.md).

## Hiccups worth knowing (fixed)
- Round 7: the in-painting critic couldn't run (no Agent tool inside the painter session, and `claude -p` was unauthenticated). The orchestrator now runs critics.
- Round 8: the painter stopped at checkpoint 2 and couldn't be resumed. Phases now replace pause and resume; an interrupted phase restarts in a fresh session from the journal's last episode.
- `scene` version numbers skipped (v1, v3, …) because the counter counted .json and .png files. It now counts .png only.
- Round 14b (Fable 5.2) leaned on its own compositing and machine-perfect tile fills and didn't feel like a painting; the it-must-be-a-painting rule followed.

## What critics still name in most rounds
Mannequin or puppet figures, faces drawn on instead of painted, hands like tubes, a uniform dab that reads as "a digital filter", a big empty block of one colour. The v8 plan and the subject library target these.

## Open directions
- A learned motor vocabulary instead of parametric strokes; fatigue and session-level physiology.
- More viewers than one critic, to see how widely a painting's feeling is shared.
- A painter that keeps memory across paintings (style development).

## Museum APIs (as of Nov 2026)
- The Met's old search endpoint is retired (410 since 2026-10-01); use `/public/collection/v1.1/search` with `offset` and `limit`, or the department listings and the Open Access CSV. The Met API rate-limits fast requests with a 403. Objects are still read from `/public/collection/v1/objects/<id>` (`/v1.1/objects/` answers 404, checked 2026-11-26); `departmentId` and `medium` filters work on the v1.1 search. `tools/find_refs.py` paces Met requests at 0.6 s and stops asking the Met for the run on a 403.
- The Cleveland Museum of Art open-access API is reachable and CC0. Both APIs refuse requests without a User-Agent header.
- The Art Institute of Chicago's images are behind bot protection: don't work around it.
