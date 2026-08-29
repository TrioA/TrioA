"""
Terminal Profile SVG Renderer
Renders authentic terminal profile SVGs directly following the reference layout,
with exact monospace character grid, dot leaders, and dynamic live data replacement.
"""

from __future__ import annotations

import html
from typing import Optional
from src.config import ProfileConfig
from src.github_stats import GithubStats
from src.portrait import PortraitRenderer
from src.theme import TerminalTheme, get_theme


class ProfileRenderer:
    WIDTH = 985
    HEIGHT = 530
    RIGHT_X = 390
    LINE_WIDTH = 58

    def __init__(self, config: ProfileConfig, stats: GithubStats, custom_ascii_path: Optional[str] = None):
        self.config = config
        self.stats = stats
        self.portrait_renderer = PortraitRenderer(custom_ascii_path)

    @staticmethod
    def escape(text: Optional[str]) -> str:
        if text is None:
            return ""
        return html.escape(str(text), quote=True)

    def _render_dot_line(self, key: str, val: str, y: int, max_val_len: Optional[int] = None) -> str:
        """Renders a single line with dot leaders dynamically matching character width."""
        # Truncate value if exceeding max length to avoid line wrap/overflow
        if max_val_len and len(val) > max_val_len:
            val = val[: max_val_len - 3] + "..."
        
        # Max available space for value: LINE_WIDTH - len(key) - 6
        avail_for_val = max(10, self.LINE_WIDTH - len(key) - 6)
        if len(val) > avail_for_val:
            val = val[: avail_for_val - 3] + "..."

        escaped_val = self.escape(val)
        
        # Calculate dots count
        # Format is: ". key: " + dots + " " + val
        needed_dots = max(2, self.LINE_WIDTH - len(key) - len(val) - 4)
        dots_str = "." * needed_dots

        # Handle compound keys like "Languages.Programming"
        if "." in key:
            parts = key.split(".")
            key_tspans = ".".join([f'<tspan class="key">{self.escape(p)}</tspan>' for p in parts])
        else:
            key_tspans = f'<tspan class="key">{self.escape(key)}</tspan>'

        return (
            f'<tspan x="{self.RIGHT_X}" y="{y}" class="cc">. </tspan>'
            f'{key_tspans}:<tspan class="cc"> {dots_str} </tspan>'
            f'<tspan class="value">{escaped_val}</tspan>'
        )

    def _render_separator(self, title: Optional[str], y: int) -> str:
        """Renders a section divider line matching reference."""
        if title:
            # e.g. "- Contact -——————————————————————————————————————————————-—-"
            dash_count = max(4, self.LINE_WIDTH - len(title) - 6)
            dashes = "—" * dash_count
            return f'<tspan x="{self.RIGHT_X}" y="{y}">- {self.escape(title)}</tspan> -{dashes}-—-'
        else:
            # Header line: e.g. "arav@grant -———————————————————————————————————————————-—-"
            host_header = f"{self.config.identity.username.lower()}@grant"
            dash_count = max(4, self.LINE_WIDTH - len(host_header) - 3)
            dashes = "—" * dash_count
            return f'<tspan x="{self.RIGHT_X}" y="{y}">{self.escape(host_header)}</tspan> -{dashes}-—-'

    def render_svg(self, theme_name: str = "dark") -> str:
        theme: TerminalTheme = get_theme(theme_name)
        
        # 1. Left side ASCII portrait
        ascii_tspans = self.portrait_renderer.render(x=15, start_y=30, line_height=20)

        # 2. Right side info rows
        right_tspans = []

        # Row 0 (y=30): Header
        right_tspans.append(self._render_separator(None, 30))

        # System Specs
        os_val = ", ".join(self.config.personal.operating_systems) or "Linux, Windows"
        uptime_val = self.config.personal.uptime_display or "18 years, 2 months, 10 days"
        location_val = self.config.personal.location or "Gurugram, India"
        focus_val = self.config.custom_fields.get("Current Focus", "Circuit Simulation, Vulkan Graphics")
        hardware_val = self.config.custom_fields.get("Hardware Lab", "ESP32-CAM, Arduino, Robotics")

        right_tspans.append(self._render_dot_line("OS", os_val, 50))
        right_tspans.append(self._render_dot_line("Uptime", uptime_val, 70))
        right_tspans.append(self._render_dot_line("Location", location_val, 90))
        right_tspans.append(self._render_dot_line("Focus", focus_val, 110))
        right_tspans.append(self._render_dot_line("Hardware", hardware_val, 130))
        
        # Empty row (y=150)
        right_tspans.append(f'<tspan x="{self.RIGHT_X}" y="150" class="cc">. </tspan>')

        # Technical Stack
        prog_langs = ", ".join(self.config.technical.languages[:4]) or "C++, JavaScript, Python, C#"
        sys_web = ", ".join(self.config.technical.markup_and_configs[:5]) or "Vulkan, React, Vite, CMake, Docker"
        interests_val = ", ".join(self.config.technical.interests[:3]) or "Circuit Simulation, 3D Graphics"

        right_tspans.append(self._render_dot_line("Languages.Programming", prog_langs, 170))
        right_tspans.append(self._render_dot_line("Languages.Computer", sys_web, 190))
        right_tspans.append(self._render_dot_line("Languages.Real", "English, Hindi", 210))

        # Empty row (y=230)
        right_tspans.append(f'<tspan x="{self.RIGHT_X}" y="230" class="cc">. </tspan>')

        # Projects Showcase
        p1 = self.config.projects[0] if len(self.config.projects) > 0 else None
        p2 = self.config.projects[1] if len(self.config.projects) > 1 else None
        p3 = self.config.projects[2] if len(self.config.projects) > 2 else None

        if p1:
            right_tspans.append(self._render_dot_line(f"Project.{p1.name}", p1.description, 250))
        else:
            right_tspans.append(self._render_dot_line("Project.NodeLAB", "Browser Circuit Simulator in Canvas 2D", 250))

        if p2:
            right_tspans.append(self._render_dot_line(f"Project.{p2.name}", p2.description, 270))
        else:
            right_tspans.append(self._render_dot_line("Project.ModernMinecraft", "C++ Vulkan Engine & Client", 270))

        if p3:
            right_tspans.append(self._render_dot_line(f"Project.{p3.name}", p3.description, 290))
        else:
            right_tspans.append(self._render_dot_line("Project.Portfolio", "Hardware & Software Showcase", 290))

        # Section: Contact (y=310 / 330)
        right_tspans.append(self._render_separator("Contact", 330))

        email_val = self.config.links.email or "hello@arav.is-a.dev"
        web_val = self.config.links.website or "https://arav.is-a.dev"
        gh_val = self.config.identity.username or "TrioA"
        insta_val = "@arav.g267"

        right_tspans.append(self._render_dot_line("Email.Personal", email_val, 350))
        right_tspans.append(self._render_dot_line("Website", web_val, 370))
        right_tspans.append(self._render_dot_line("GitHub", gh_val, 390))
        right_tspans.append(self._render_dot_line("Instagram", insta_val, 410))

        # Empty row (y=430)
        right_tspans.append(f'<tspan x="{self.RIGHT_X}" y="430" class="cc">. </tspan>')

        # Section: GitHub Stats (y=450)
        right_tspans.append(self._render_separator("GitHub Stats", 450))

        # Row: Repos & Stars (y=470)
        repos_cnt = self.stats.repositories or 12
        contrib_cnt = self.stats.contributions or 133
        stars_cnt = self.stats.stars or 0
        repo_dots = "." * max(2, 6 - len(str(repos_cnt)))
        star_dots = "." * max(2, 12 - len(str(stars_cnt)))
        
        right_tspans.append(
            f'<tspan x="{self.RIGHT_X}" y="470" class="cc">. </tspan>'
            f'<tspan class="key">Repos</tspan>:<tspan class="cc" id="repo_data_dots"> {repo_dots} </tspan>'
            f'<tspan class="value" id="repo_data">{repos_cnt}</tspan> '
            f'{{<tspan class="key">Contributed</tspan>: <tspan class="value" id="contrib_data">{contrib_cnt}</tspan>}} | '
            f'<tspan class="key">Stars</tspan>:<tspan class="cc" id="star_data_dots"> {star_dots} </tspan>'
            f'<tspan class="value" id="star_data">{stars_cnt}</tspan>'
        )

        # Row: Commits & Followers (y=490)
        commits_cnt = self.stats.commits or 240
        followers_cnt = self.stats.followers or 4
        commit_dots = "." * max(2, 17 - len(f"{commits_cnt:,}"))
        follower_dots = "." * max(2, 8 - len(str(followers_cnt)))

        right_tspans.append(
            f'<tspan x="{self.RIGHT_X}" y="490" class="cc">. </tspan>'
            f'<tspan class="key">Commits</tspan>:<tspan class="cc" id="commit_data_dots"> {commit_dots} </tspan>'
            f'<tspan class="value" id="commit_data">{commits_cnt:,}</tspan> | '
            f'<tspan class="key">Followers</tspan>:<tspan class="cc" id="follower_data_dots"> {follower_dots} </tspan>'
            f'<tspan class="value" id="follower_data">{followers_cnt}</tspan>'
        )

        # Row: Lines of code (y=510)
        additions = self.stats.lines_added or 523178
        deletions = self.stats.lines_deleted or 76902
        net_loc = self.stats.net_lines or (additions - deletions)
        
        right_tspans.append(
            f'<tspan x="{self.RIGHT_X}" y="510" class="cc">. </tspan>'
            f'<tspan class="key">Lines of Code on GitHub</tspan>:<tspan class="cc" id="loc_data_dots">. </tspan>'
            f'<tspan class="value" id="loc_data">{net_loc:,}</tspan> '
            f'( <tspan class="addColor" id="loc_add">{additions:,}</tspan><tspan class="addColor">++</tspan>, '
            f'<tspan id="loc_del_dots"> </tspan><tspan class="delColor" id="loc_del">{deletions:,}</tspan><tspan class="delColor">--</tspan> )'
        )

        all_right_tspans_str = "\n".join(right_tspans)

        # Build complete SVG
        svg_content = f'''<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="{self.WIDTH}px" height="{self.HEIGHT}px" font-size="16px">
<style>
@font-face {{
src: local('Consolas'), local('Consolas Bold');
font-family: 'ConsolasFallback';
font-display: swap;
-webkit-size-adjust: 109%;
size-adjust: 109%;
}}
.key {{fill: {theme.key_color};}}
.value {{fill: {theme.value_color};}}
.addColor {{fill: {theme.add_color};}}
.delColor {{fill: {theme.del_color};}}
.cc {{fill: {theme.cc_color};}}
text, tspan {{white-space: pre;}}
</style>
<rect width="{self.WIDTH}px" height="{self.HEIGHT}px" fill="{theme.bg}" rx="15"/>
<text x="15" y="30" fill="{theme.text_base}" class="ascii">
{ascii_tspans}
</text>
<text x="{self.RIGHT_X}" y="30" fill="{theme.text_base}">
{all_right_tspans_str}
</text>
</svg>'''
        return svg_content
