import type { Metadata, Viewport } from "next";
import { Cormorant_Garamond } from "next/font/google";
import "./globals.css";

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: "500",
  style: ["normal", "italic"],
  display: "swap",
  variable: "--font-cormorant",
});

const title = "Teodor: Paintings from Feeling";
const description =
  "An AI painter given a hidden feeling, painting it the way human painters work. Can you name what he felt?";
const image = { url: "/paintings/r9.jpg", width: 900, height: 1200, alt: "The Cross in the Window, by Teodor" };

export const metadata: Metadata = {
  metadataBase: new URL("https://teodor.robertontiu.com"),
  title,
  description,
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
