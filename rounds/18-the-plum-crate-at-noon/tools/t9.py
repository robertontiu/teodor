import subprocess
L, M, D = "#ebe5d6", "#9b9384", "#2e2b28"
# T9: refined choice. Very high view, close. Awning stripe band cut across upper-right corner;
# crate wall upper-left behind him (mid with dark crate mouths); his head tipped back high-left, face up to us;
# body a long diagonal down to crossed ankles at lower-centre; passers-by feet stepping round them at right edge.
b = f'''<rect width="120" height="160" fill="{L}"/>
<polygon points="0,0 74,0 54,74 30,96 0,104" fill="{M}"/>
<g fill="{D}"><rect x="6" y="8" width="18" height="8"/><rect x="30" y="6" width="18" height="8"/><rect x="4" y="36" width="18" height="8"/><rect x="28" y="34" width="18" height="8"/><rect x="2" y="66" width="18" height="8"/></g>
<polygon points="80,0 120,0 120,30" fill="{D}"/>
<ellipse cx="46" cy="58" rx="12" ry="13" fill="{L}" stroke="{D}"/>
<path d="M36,70 Q54,66 64,78 L84,118 Q76,124 66,122 L44,92Z" fill="{D}"/>
<path d="M66,120 L74,148 L80,146 M78,118 L92,144 L98,140" stroke="{M}" stroke-width="7" fill="none"/>
<path d="M100,96 l10,-6 l4,8 l-10,6Z M106,126 l12,-2 l0,9 l-12,2Z" fill="{D}"/>
<rect x="108" y="40" width="8" height="52" fill="{M}"/><rect x="112" y="104" width="8" height="24" fill="{M}"/>'''
open("thumbs/t9.svg","w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="160" viewBox="0 0 120 160">{b}</svg>')
subprocess.run(["rsvg-convert","-w","240","-h","320","thumbs/t9.svg","-o","thumbs/t9.png"],check=True)
