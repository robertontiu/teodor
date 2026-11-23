"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// Painting order and titles. To add one: drop the jpg into public/paintings and add [id, title] here.
const works: [string, string][] = [
  ["r0", "A Warmth That Doesn’t Know Where It Came From"],
  ["r1", "Updraft, Late Morning"],
  ["r2", "Vent"],
  ["r3", "After the Supper Plates"],
  ["r4", "The Marks on the Doorpost"],
  ["r5", "The Fork at Evening, the Sail at Morning"],
  ["r6", "The Morning After, Number Eleven"],
  ["r7", "Gate, Evening"],
  ["r8", "The Threshold Light"],
  ["r9", "The Cross in the Window"],
  ["r10", "Past the Lit Window"],
];

const src = (id: string) => `/paintings/${id}.jpg`;

const toggleFullscreen = () => {
  try {
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen().catch(() => {});
  } catch {}
};

export default function Gallery() {
  const trackRef = useRef<HTMLElement>(null);
  const slidesRef = useRef<HTMLElement[]>([]);
  const curRef = useRef(0);
  const [cur, setCur] = useState(-1);
  const [title, setTitle] = useState({ text: "Teodor", visible: true });

  const show = useCallback((i: number) => {
    curRef.current = i;
    setCur(i);
    setTitle((t) => ({ ...t, visible: false }));
    window.setTimeout(() => setTitle({ text: works[i][1], visible: true }), 180);
  }, []);

  const go = useCallback((d: number) => {
    const slides = slidesRef.current;
    const i = Math.max(0, Math.min(slides.length - 1, curRef.current + d));
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    slides[i]?.scrollIntoView({ behavior: reduce ? "auto" : "smooth", inline: "center" });
  }, []);

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    const slides = slidesRef.current;

    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting && e.intersectionRatio > 0.6) show(Number((e.target as HTMLElement).dataset.i));
        }
      },
      { root: track, threshold: [0.6] },
    );
    slides.forEach((s) => io.observe(s));

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
        e.preventDefault();
        go(1);
      } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
        e.preventDefault();
        go(-1);
      } else if (e.key === "Home") {
        slides[0].scrollIntoView({ inline: "center" });
      } else if (e.key === "End") {
        slides[slides.length - 1].scrollIntoView({ inline: "center" });
      } else if (e.key === "f" || e.key === "F") {
        toggleFullscreen();
      }
    };
    addEventListener("keydown", onKey);
    show(0);

    return () => {
      io.disconnect();
      removeEventListener("keydown", onKey);
    };
  }, [go, show]);

  return (
    <>
      <noscript>
        <style>{".slide img{opacity:1}"}</style>
      </noscript>
      <main className="track" ref={trackRef} aria-label="Paintings" onDoubleClick={toggleFullscreen}>
        {works.map(([id, t], i) => (
          <section
            key={id}
            className={i === cur ? "slide on" : "slide"}
            id={id}
            data-i={i}
            aria-label={t}
            ref={(el) => {
              if (el) slidesRef.current[i] = el;
            }}
          >
            <div className="glow" style={{ backgroundImage: `url('${src(id)}')` }} />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={src(id)} alt={t} loading={i > 1 ? "lazy" : undefined} />
          </section>
        ))}
      </main>
      <button className="nav prev" aria-label="Previous painting" onClick={() => go(-1)} />
      <button className="nav next" aria-label="Next painting" onClick={() => go(1)} />
      <a className="gh" href="https://github.com/robertontiu/teodor" target="_blank" rel="noopener noreferrer" aria-label="Teodor on GitHub">
        <span className="pill">
          <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">
            <path
              fill="currentColor"
              d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
            />
          </svg>
          <span className="label">GitHub</span>
        </span>
      </a>
      <footer className="bar">
        <h1 style={{ opacity: title.visible ? 1 : 0 }}>{title.text}</h1>
      </footer>
    </>
  );
}
