# Prophet Brand Assets

This folder contains working Prophet logo assets.

## Folder Layout

- `brand/exports/`: processed logo variants.
- `brand/exports/icons/`: icon size exports and favicons.

## Logo Variants

Primary:
- `brand/exports/logo-horizontal-color.png`
- `brand/exports/logo-icon-color.png`

Secondary:
- `brand/exports/logo-horizontal-color-compact.png`

Monochrome:
- `brand/exports/logo-horizontal-mono-black.png`
- `brand/exports/logo-horizontal-mono-white-transparent.png`
- `brand/exports/logo-horizontal-mono-white.png`

Preview backgrounds:
- `brand/exports/logo-horizontal-mono-black-on-light.png`
- `brand/exports/logo-horizontal-mono-white-on-dark.png`

Icons:
- `brand/exports/icons/logo-icon-1024.png`
- `brand/exports/icons/logo-icon-512.png`
- `brand/exports/icons/logo-icon-256.png`
- `brand/exports/icons/logo-icon-128.png`
- `brand/exports/icons/logo-icon-64.png`
- `brand/exports/icons/logo-icon-32.png`
- `brand/exports/icons/favicon-32.png`
- `brand/exports/icons/favicon-16.png`

## Color Tokens

- `--prophet-primary: #0F172A`
- `--prophet-accent: #0EA5A4`
- `--prophet-black: #000000`
- `--prophet-white: #FFFFFF`

## Usage Rules

- Prefer `logo-horizontal-color.png` on light backgrounds.
- Prefer `logo-horizontal-mono-white-transparent.png` on dark backgrounds.
- Use icon-only assets for favicons, app icons, and small UI surfaces.
- Keep clear-space around the mark at least `0.5x` the icon stem width.
- Minimum digital size:
  - horizontal lockup: `120px` width
  - icon-only mark: `16px` width

## Don't

- Do not recolor outside the defined palette.
- Do not add shadows, glows, gradients, or effects.
- Do not stretch, skew, or rotate the mark.
- Do not place the black logo on very dark backgrounds.
- Do not place the white logo on very light backgrounds.

## Note

For print-grade or exact vector use, add canonical SVG masters to this folder when available.
