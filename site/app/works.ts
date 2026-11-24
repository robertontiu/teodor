// Paintings in the order they were made. To add one: drop the jpg into public/paintings and add an entry at the end.
// The gallery shows them newest first.
// `model` is the Claude model that painted it (default Opus 5.5).
export type Work = { id: string; title: string; model: string };

const DEFAULT_MODEL = "Opus 5.5";

const inOrderMade: (Omit<Work, "model"> & { model?: string })[] = [
  { id: "r0", title: "A Warmth That Doesn’t Know Where It Came From" },
  { id: "r1", title: "Updraft, Late Morning" },
  { id: "r2", title: "Vent" },
  { id: "r3", title: "After the Supper Plates" },
  { id: "r4", title: "The Marks on the Doorpost" },
  { id: "r5", title: "The Fork at Evening, the Sail at Morning" },
  { id: "r6", title: "The Morning After, Number Eleven" },
  { id: "r7", title: "Gate, Evening" },
  { id: "r8", title: "The Threshold Light" },
  { id: "r9", title: "The Cross in the Window" },
  { id: "r10", title: "Past the Lit Window" },
  { id: "r11", title: "The Long Gold Hour" },
  { id: "r12", title: "The Footlights" },
  { id: "r13", title: "Black Noon" },
  { id: "r14", title: "The Field Turns Over" },
  { id: "r14b", title: "The Shadow Kept Both Legs", model: "Fable 5.2" },
  { id: "r15", title: "One More Night" },
];

export const works: Work[] = inOrderMade.map((w) => ({ ...w, model: w.model ?? DEFAULT_MODEL })).reverse();

export const SITE_URL = "https://teodor.robertontiu.com";
export const SITE_TITLE = "Teodor: Paintings from Feeling";
export const SITE_DESCRIPTION =
  "Teodor is an AI painter who works the way human painters do: from a feeling, drawing first, then looking and correcting stroke by stroke.";

export const src = (id: string) => `/paintings/${id}.jpg`;
export const pagePath = (id: string) => `/${id}/`;
