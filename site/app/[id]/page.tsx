import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Gallery from "../Gallery";
import { SITE_DESCRIPTION, pagePath, src, works } from "../works";

export const dynamicParams = false;

export function generateStaticParams() {
  return works.map((w) => ({ id: w.id }));
}

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const w = works.find((x) => x.id === id);
  if (!w) return {};
  const title = `${w.title}, by Teodor`;
  const description = `“${w.title}”, a painting by Teodor (${w.style ? `${w.style}, ` : ""}Claude ${w.model}). ${SITE_DESCRIPTION}`;
  const image = { url: src(w.id), width: 900, height: 1200, alt: `${w.title}, by Teodor` };
  return {
    title,
    description,
    alternates: { canonical: pagePath(w.id) },
    openGraph: { title, description, url: pagePath(w.id), siteName: "Teodor", type: "article", images: [image] },
    twitter: { card: "summary_large_image", title, description, images: [image] },
  };
}

export default async function PaintingPage({ params }: Props) {
  const { id } = await params;
  if (!works.some((w) => w.id === id)) notFound();
  return <Gallery initial={id} />;
}
