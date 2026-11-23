// Painting order and titles. To add one: drop the jpg into public/paintings and add an entry here.
export type Work = { id: string; title: string };

export const works: Work[] = [
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
];

export const SITE_URL = "https://teodor.robertontiu.com";
export const SITE_TITLE = "Teodor: Paintings from Feeling";
export const SITE_DESCRIPTION =
  "Teodor is an AI painter who works the way human painters do: from a feeling, drawing first, then looking and correcting stroke by stroke.";

export const src = (id: string) => `/paintings/${id}.jpg`;
export const pagePath = (id: string) => `/${id}/`;
