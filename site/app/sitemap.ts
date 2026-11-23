import type { MetadataRoute } from "next";
import { SITE_URL, pagePath, src, works } from "./works";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: `${SITE_URL}/`, changeFrequency: "weekly", priority: 1 },
    ...works.map((w) => ({
      url: `${SITE_URL}${pagePath(w.id)}`,
      changeFrequency: "monthly" as const,
      priority: 0.8,
      images: [`${SITE_URL}${src(w.id)}`],
    })),
  ];
}
