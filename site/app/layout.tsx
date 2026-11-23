import type { Metadata, Viewport } from "next";
import { Cormorant_Garamond } from "next/font/google";
import "./globals.css";
import { SITE_DESCRIPTION, SITE_TITLE, SITE_URL } from "./works";

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: "500",
  style: ["normal", "italic"],
  display: "swap",
  variable: "--font-cormorant",
});

const title = SITE_TITLE;
const description = SITE_DESCRIPTION;
const image = { url: "/paintings/r9.jpg", width: 900, height: 1200, alt: "The Cross in the Window, by Teodor" };

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title,
  description,
  applicationName: "Teodor",
  authors: [{ name: "Teodor" }, { name: "Robert Ontiu", url: "https://github.com/robertontiu" }],
  keywords: ["AI painter", "AI art", "painting", "Teodor", "emotion", "creative process"],
  alternates: { canonical: "/" },
  robots: { index: true, follow: true },
  openGraph: { title, description, url: "/", siteName: "Teodor", type: "website", images: [image] },
  twitter: { card: "summary_large_image", title, description, images: [image] },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#0d0b09",
  colorScheme: "dark",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={cormorant.variable}>
      <body>{children}</body>
    </html>
  );
}
