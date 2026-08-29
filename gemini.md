# GitHub Profile Project Specification

## Project Goal

Build a highly customized GitHub profile system inspired by terminal-style developer
profiles that use a generated SVG as the primary visual surface.

The implementation should follow the same broad concept as the reference profile:
- a profile README
- a generated SVG
- dynamic GitHub statistics
- GitHub Actions for automatic updates
- separate light and dark variants
- programmatic SVG text/data replacement

However, this must be an ORIGINAL implementation and an ORIGINAL visual design.

Do not copy the reference project's source code, SVG artwork, exact layout, exact
wording, or implementation structure line-for-line.

The system must be modular enough that the visual design can be replaced later
without rewriting the statistics engine or GitHub Actions pipeline.

---

# V1 Visual Direction

## Overall Style

Target aesthetic:

- sophisticated terminal / engineering interface
- information-dense but readable
- dark-first
- clean monospace typography
- technical without looking like a generic hacker template
- restrained use of color
- strong alignment and spacing
- polished enough to feel intentionally designed
- original rather than a clone of the reference

The first release should feel like a carefully designed developer-system interface.

Do NOT fill the profile with:
- generic developer badges
- excessive emojis
- random GitHub statistic widgets
- unnecessary animations
- giant headings
- filler text

The visual system must prioritize the actual projects and technical identity.

---

# Core Layout

V1 should use a single generated SVG containing:

LEFT / PRIMARY VISUAL AREA
- placeholder for a future pixel-art portrait
- portrait area must already be integrated into the layout
- the implementation should make replacing the placeholder with the final
  generated portrait trivial

RIGHT / INFORMATION AREA
- GitHub username
- age / uptime
- operating systems
- location
- programming languages
- markup / data / configuration languages
- interests
- current projects
- hobbies
- website
- email
- GitHub statistics
- contribution statistics
- a few tasteful custom/fun fields

The exact layout is not required to copy the reference.

Improve:
- spacing
- information hierarchy
- readability
- alignment
- section structure
- typography
- visual balance

The layout should look intentionally designed rather than like a list of
terminal commands pasted into an SVG.

---

# Required Content

The profile should support the following information.

## Identity

Show:
- GitHub username: TrioA

Do NOT use "TrioA" anywhere else in visible profile content, decorative text,
headings, descriptions, generated copy, or branding.

Do not use a personal-name heading unless explicitly added later.

---

## Personal Information

Show:
- age / uptime
- operating systems
- broad location

The location should remain appropriately broad.

Do not expose:
- home address
- school
- phone number
- private account details
- tokens
- secrets
- other sensitive information

---

## Technical Information

Show:
- programming languages
- markup / data / configuration languages
- technical interests
- hardware/software interests where useful

Keep this concise and meaningful.

---

## Projects

Show a curated "Current Projects" section.

Projects must be configuration-driven so they can be changed without editing the
SVG-generation logic.

Do not hardcode project descriptions throughout the codebase.

Use a central configuration structure such as:
- YAML
- JSON
- Python dictionary

Prefer whichever is simplest and easiest to maintain.

---

## Hobbies

Show a small hobbies section.

Keep it concise.

---

## Links

Support:
- website
- public email

These should be stored in configuration rather than scattered through source code.

---

# Dynamic GitHub Statistics

Recreate the same GENERAL statistical concept used by the reference project.

Required dynamic statistics:

- owned repositories
- stars across owned repositories
- total contribution count
- followers
- total commits
- lines added
- lines deleted
- net lines of code

The implementation should dynamically query GitHub rather than hardcode statistics.

The statistics system should support pagination.

Use GitHub's current supported API mechanisms.

Prefer the simplest secure authentication method that supports the required data.

Do not assume a broad personal access token is necessary without investigating
whether GitHub Actions' built-in GITHUB_TOKEN can handle each operation.

If a PAT is genuinely required, document exactly:
- why it is required
- minimum permissions needed
- where it should be stored
- what the workflow accesses

Never hardcode credentials.

---

# Lines of Code

The reference implementation performs repository history traversal and caching
to calculate additions/deletions.

Reproduce the useful behavior, but do NOT blindly copy its implementation.

The implementation should:
- avoid unnecessary repeated API calls
- use caching where useful
- handle pagination
- handle empty repositories
- handle deleted/inaccessible repositories gracefully
- avoid crashing the entire build because one repository cannot be inspected
- clearly document what the metric means

Be explicit about whether the metric represents:
- commit additions/deletions
- source LOC
- or another definition

Do not label a metric "lines of code" if the underlying calculation actually
measures something different without explaining it.

---

# GitHub Actions

The project must automatically regenerate the profile.

Required triggers:

1. Push to the main branch
2. Daily scheduled update

The workflow should:

1. Check out the repository
2. Set up the required runtime
3. Install dependencies
4. Run the generator
5. Validate generated output
6. Commit changes only if files actually changed
7. Push the update

Use current, maintained GitHub Action versions.

Do not copy outdated action versions from the reference repository.

The workflow must fail clearly when:
- authentication is missing
- API calls fail unexpectedly
- generated SVG is malformed
- required files are missing

Avoid noisy commits when nothing changed.

---

# Light / Dark Mode

Generate:

- light_mode.svg
- dark_mode.svg

README.md should use a theme-aware `<picture>` element so GitHub can display the
appropriate SVG based on the viewer's theme.

The generated SVGs should share one logical design system rather than being
independently maintained copies.

Colors, typography, spacing, and content should be controlled centrally.

---

# Future Portrait Integration

The final portrait is NOT being added in V1 yet.

Instead, implement the layout with a portrait slot/place-holder.

The system must make it possible to later supply:
- a pixel-art portrait
- a generated bitmap
- an SVG portrait
- or another artistic treatment

without redesigning the entire system.

The portrait should eventually be derived from a user-provided photo, but no
photo processing is required in the initial implementation.

---

# Configuration

Create one obvious place for non-code profile information.

For example:

config/
  profile.yml

or an equally clean alternative.

It should contain fields such as:

- username
- age/birthday information
- operating systems
- location
- programming languages
- markup/data languages
- interests
- projects
- hobbies
- website
- email
- custom fields

Do not spread these values across Python source code or SVG files.

The GitHub username may be configuration-driven as well.

---

# Custom / Fun Fields

Include a small system for optional custom terminal-style fields.

Examples of the TYPE of information that could be supported:

- current focus
- build status
- favorite tools
- current obsession
- "last seen debugging"
- system status
- small technical joke

Do not invent fake personal facts.

These values must be configuration-driven.

---

# Architecture

Prefer a clean separation similar to:

profile configuration
        ↓
GitHub data collector
        ↓
statistics processing
        ↓
SVG renderer
        ↓
light/dark SVG output
        ↓
README embed

A possible structure:

.
├── README.md
├── gemini.md
├── config/
│   └── profile.yml
├── src/
│   ├── github_stats.py
│   ├── renderer.py
│   ├── portrait.py
│   └── main.py
├── assets/
│   ├── light_mode.svg
│   ├── dark_mode.svg
│   └── ...
├── cache/
├── tests/
├── requirements.txt
└── .github/
    └── workflows/
        └── update-profile.yml

This is only a suggested structure.

Use the structure that actually makes the project simpler.

Avoid unnecessary abstractions.

---

# SVG Requirements

SVG is the actual visual product.

Ensure:
- valid XML
- deterministic generation
- crisp rendering
- monospace alignment
- no accidental text wrapping
- consistent dimensions
- sensible scaling
- proper escaping of user/content data
- theme-specific colors
- no embedded secrets
- no unnecessary external dependencies

Keep the SVG maintainable.

Use IDs for dynamically replaced values where appropriate.

Do not make the final SVG dependent on a local font file.

---

# README

README.md should remain extremely small.

Prefer something conceptually like:

<picture>
  ...
</picture>

The README should primarily be responsible for displaying the generated profile.

Do not recreate the entire visual layout in Markdown.

---

# Quality Requirements

Before considering V1 complete:

- run the generator successfully
- verify both SVG files
- open/render both SVGs locally
- inspect alignment at normal GitHub profile width
- inspect light mode
- inspect dark mode
- verify long values do not destroy alignment
- verify numbers with commas render correctly
- test empty repositories
- test repositories with no default branch
- test missing optional fields
- test API failure handling
- test the workflow YAML
- test that a no-op run does not create pointless commits

Fix problems rather than merely reporting them.

---

# Git / Repository Rules

This project currently starts in an empty local folder.

Do not assume:
- a Git repository already exists
- a remote exists
- the repository has been published
- GitHub secrets already exist

Set up the local project so it can later be published cleanly.

Do not create or modify unrelated files outside this project.

Do not publish or push anything unless explicitly instructed.

---

# Development Philosophy

Work autonomously.

Inspect first.

Plan second.

Implement third.

Test continuously.

Iterate based on actual rendered output.

Prefer small, understandable files over clever architecture.

Do not rewrite working code merely to make it look different.

When you encounter uncertainty:
- inspect the repository
- inspect documentation
- verify behavior experimentally
- choose the simplest defensible implementation

Do not silently make assumptions about personal information.

---

# V1 Scope

V1 should deliver:

- original terminal-style SVG profile
- light/dark SVG versions
- dynamic GitHub statistics
- configurable personal/project information
- GitHub Actions automation
- caching for expensive history/statistics operations
- portrait placeholder
- README embedding
- local validation/testing
- documentation for setup and secrets

Do NOT spend the initial implementation cycle on:
- advanced animation
- elaborate web components
- unnecessary JavaScript frontends
- external statistic services
- excessive badge systems
- final portrait processing
- speculative future features

Build a solid engine first.

The visual design can be substantially revamped in V2 without replacing the
data/statistics system.