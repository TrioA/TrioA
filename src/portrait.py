"""
ASCII Portrait Engine
Renders ASCII art for the terminal profile with support for custom portrait.ascii files.
"""

from __future__ import annotations

import os
from typing import List, Optional

# Default 25-line ASCII developer/cyber avatar placeholder
DEFAULT_ASCII_PORTRAIT: List[str] = [
    "           g@M%@%%@N%Nw,,                   ",
    "        ,M*|`||*%gNM=]mM%g||%N,             ",
    "       p!``  '! |''` '''|||jhlj%w           ",
    "     ,@L `    ,,        ''!`|j%M]%M         ",
    "    ]j'` .,wp@pw,    `.     ''''|%Wg       ",
    "  /{||]@@@@@@@@@pp.             |||||      ",
    " '` ']@@@@@@@@@@@@@@p     , ,'''` `        ",
    "  , :]%%@@@@@%%%%%%k%h '*||mkr     *       ",
    "  '  j%M`      |jkk'   ~nrn=|i    ;`       ",
    "   !  jrr*^`             `\"!  L'':!   ",
    "    j  lp;,.  ,/ @@    ,;\\nmy \"  ,~   ",
    "   i r @@@@mmHM @@@@ `^****M*,p ;,         ",
    "   | ]@@@@HHH]g@M%%%%%H,jmgpmb%  j         ",
    "    ;;%%%%%k%@[,.n|;.;j%%k|%k%%',[         ",
    "     H|%%k%%%j%k||,;;j;!!'|%ij}]@          ",
    "     \"djjmkL,\"]][,,,,wwxw;|#kjk` ",
    "       %;%km%%%%M%M|%%jkkii|||[            ",
    "        kjj%%kkkl|!||||||j|||\"        ",
    "         |jm%H@@@b%%kkmk%i|!,[             ",
    "         @p|j%%%%jkk|||j*'`;j[             ",
    "        ]@@@g|'''`'''  ` ,;j%k             ",
    "        @@@@@mgmp;,,,,:;jj%%k%             ",
    "       @@@@@@@@%%kgki!|jjjj%k%@ .          ",
    ". ^['' %@@@@HH%b%k{illljkjj%%%% ; `,.      ",
    "=[' ` . %HH%%%%%H@gkilljjj%kk%\".   `'i",
]


class PortraitRenderer:
    def __init__(self, ascii_file_path: Optional[str] = None):
        self.ascii_file_path = ascii_file_path or "assets/portrait.ascii"

    def get_lines(self) -> List[str]:
        """Loads lines from assets/portrait.ascii if available, otherwise returns default ASCII."""
        if os.path.exists(self.ascii_file_path):
            try:
                with open(self.ascii_file_path, "r", encoding="utf-8") as f:
                    lines = [line.rstrip("\r\n") for line in f.readlines()]
                if lines:
                    # Pad or truncate to 25 lines
                    if len(lines) < 25:
                        lines = lines + [""] * (25 - len(lines))
                    return lines[:25]
            except Exception:
                pass
        return DEFAULT_ASCII_PORTRAIT

    def render(self, x: int = 15, start_y: int = 30, line_height: int = 20) -> str:
        """Renders ASCII lines as SVG tspans."""
        lines = self.get_lines()
        tspan_elements = []
        for i, line in enumerate(lines):
            y = start_y + (i * line_height)
            # Escape XML entities in ASCII line
            escaped_line = (
                line.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            tspan_elements.append(f'<tspan x="{x}" y="{y}">{escaped_line}</tspan>')
        return "\n".join(tspan_elements)
