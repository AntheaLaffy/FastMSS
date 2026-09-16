# FastMSS logo color variant prompts

Generated with the built-in imagegen tool using `fastmss-logo.png` as the edit target. Hex values are requested sRGB targets; generated PNG pixels may vary slightly.

## 冷蓝 · 浅色界面

Output: `fastmss-logo-light.png`

```text
Use case: logo-brand
Asset type: color variant of the existing FastMSS logo, a transparent PNG asset.
Input image 1: EDIT TARGET — the existing complete FastMSS logo.
Primary request: Perform only a precise color replacement on this logo. Preserve the existing design exactly: the three separated ribbon contours, the F-like symbol, all negative spaces, the distinctive bend of the lower ribbon, the exact "FastMSS" lettering, typography, letter spacing, line weights, scale, location, margins, and square composition. Do not reinterpret or redraw the logo.
Color replacements: Top ribbon #2563EB; middle ribbon #0891B2; bottom ribbon #4F46E5; the complete wordmark #0F172A. Use these as the target flat sRGB fill colors; preserve clean antialiased edges.
Intended setting: White and pale cool-gray backgrounds in documentation and application UI.
Scene/backdrop: Keep a genuinely transparent background with alpha transparency, including the empty channels between the ribbons and the counters inside letters. Do not render the intended setting or any background; it is context only. No background rectangle and no painted checkerboard.
Constraints: Color-only edit. Preserve the original silhouette and wordmark exactly. Flat solid fills, no shading, no gradients, no glow, no shadow, no added outline, no 3D, no extra objects, no new text, no labels, no swatches, no watermark. Output a single standalone logo using the reference's full square canvas and generous margins.
```

## 亮青 · 深色界面

Output: `fastmss-logo-dark.png`

```text
Use case: logo-brand
Asset type: color variant of the existing FastMSS logo, a transparent PNG asset.
Input image 1: EDIT TARGET — the existing complete FastMSS logo.
Primary request: Perform only a precise color replacement on this logo. Preserve the existing design exactly: the three separated ribbon contours, the F-like symbol, all negative spaces, the distinctive bend of the lower ribbon, the exact "FastMSS" lettering, typography, letter spacing, line weights, scale, location, margins, and square composition. Do not reinterpret or redraw the logo.
Color replacements: Top ribbon #60A5FA; middle ribbon #2DD4BF; bottom ribbon #C4B5FD; the complete wordmark #F8FAFC. Use these as the target flat sRGB fill colors; preserve clean antialiased edges.
Intended setting: A very dark interface, so the entire wordmark must be near-white and all three ribbons must remain bright and distinct.
Scene/backdrop: Keep a genuinely transparent background with alpha transparency, including the empty channels between the ribbons and the counters inside letters. Do not render the intended setting or any background; it is context only. No background rectangle and no painted checkerboard.
Constraints: Color-only edit. Preserve the original silhouette and wordmark exactly. Flat solid fills, no shading, no gradients, no glow, no shadow, no added outline, no 3D, no extra objects, no new text, no labels, no swatches, no watermark. Output a single standalone logo using the reference's full square canvas and generous margins.
```

## 橙红 · 宣传场景

Output: `fastmss-logo-warm.png`

```text
Use case: logo-brand
Asset type: color variant of the existing FastMSS logo, a transparent PNG asset.
Input image 1: EDIT TARGET — the existing complete FastMSS logo.
Primary request: Perform only a precise color replacement on this logo. Preserve the existing design exactly: the three separated ribbon contours, the F-like symbol, all negative spaces, the distinctive bend of the lower ribbon, the exact "FastMSS" lettering, typography, letter spacing, line weights, scale, location, margins, and square composition. Do not reinterpret or redraw the logo.
Color replacements: Top ribbon #EA580C; middle ribbon #F59E0B; bottom ribbon #E11D48; the complete wordmark #292524. Use these as the target flat sRGB fill colors; preserve clean antialiased edges.
Intended setting: A warm pale background in launch announcements and promotional graphics.
Scene/backdrop: Keep a genuinely transparent background with alpha transparency, including the empty channels between the ribbons and the counters inside letters. Do not render the intended setting or any background; it is context only. No background rectangle and no painted checkerboard.
Constraints: Color-only edit. Preserve the original silhouette and wordmark exactly. Flat solid fills, no shading, no gradients, no glow, no shadow, no added outline, no 3D, no extra objects, no new text, no labels, no swatches, no watermark. Output a single standalone logo using the reference's full square canvas and generous margins.
```

## 纯黑 · 单色输出

Output: `fastmss-logo-mono.png`

```text
Use case: logo-brand
Asset type: color variant of the existing FastMSS logo, a transparent PNG asset.
Input image 1: EDIT TARGET — the existing complete FastMSS logo.
Primary request: Perform only a precise color replacement on this logo. Preserve the existing design exactly: the three separated ribbon contours, the F-like symbol, all negative spaces, the distinctive bend of the lower ribbon, the exact "FastMSS" lettering, typography, letter spacing, line weights, scale, location, margins, and square composition. Do not reinterpret or redraw the logo.
Color replacements: Top ribbon #000000; middle ribbon #000000; bottom ribbon #000000; the complete wordmark #000000. Every visible part of the symbol and lettering must be pure solid black; this is a strictly single-ink black logo.
Intended setting: A plain white background, monochrome printing and document reproduction.
Scene/backdrop: Keep a genuinely transparent background with alpha transparency, including the empty channels between the ribbons and the counters inside letters. Do not render the intended setting or any background; it is context only. No background rectangle and no painted checkerboard.
Constraints: Color-only edit. Preserve the original silhouette and wordmark exactly. Flat solid fills, no shading, no gradients, no glow, no shadow, no added outline, no 3D, no extra objects, no new text, no labels, no swatches, no watermark. Output a single standalone logo using the reference's full square canvas and generous margins.
```

## Dark variant: final processing

The initial dark recolor had visible alpha-edge artifacts. Its edges were cleaned, then the background was replaced with solid navy. The selected `fastmss-logo-dark.png` is an opaque dark-background presentation asset. The other selected variants retain transparency. The unsuccessful background-extraction attempt was discarded.

### Edge cleanup

```text
Use case: logo-brand
Asset type: corrected dark-theme FastMSS logo, transparent PNG.
Input image 1: edit target, the pale blue / teal / lavender FastMSS logo.
Primary request: Clean up the alpha matte and edge defects while preserving this logo's design, exact ribbon shapes, exact typography, wordmark spelling "FastMSS", proportions, positioning, spacing, square canvas, and colors.
The supplied image has unwanted white flecks, ragged stray pixels, and ghost outlines surrounding the white wordmark, around the letter counters, and along the lower lavender ribbon. Remove ALL such artifacts. Rebuild the edges as immaculate smooth vector-like boundaries with consistent antialiasing. The wordmark must be solid clean near-white inside the letter shapes, and completely transparent outside them; the genuine counters in "a" and other letters remain smoothly transparent. Clear every detached speck between and around letters. Do not add an outline.
Colors: top ribbon flat #60A5FA; middle ribbon flat #2DD4BF; lower ribbon flat #C4B5FD; wordmark flat #F8FAFC. No gradients, no texture, no shading.
Background: actual alpha transparency, including all empty channels and letter counters. No opaque background, no mockup, no checkerboard, no glow, no shadow.
Preserve the reference logo, but output a clean production logo with no ragged pixels, rough edges, streaks, white halo, or dirt outside its intended contours. One standalone logo only, no other text.
```

### Final navy background

```text
Use case: logo-brand
Edit target: supplied FastMSS logo, with pale-blue, teal and lavender ribbons and a white wordmark.
Replace every part of the gray checkerboard background with a perfectly uniform solid dark navy background, exactly #0B1220. Replace the checkerboard in all empty areas, between the ribbons and letters, and inside letter counters too.
Keep the logo's three ribbon contours, exact typography "FastMSS", proportions, positioning, layout and colors unchanged. Top ribbon pale blue #60A5FA, middle ribbon teal #2DD4BF, bottom ribbon lavender #C4B5FD; wordmark clean near-white #F8FAFC.
This deliverable MUST have a fully opaque solid dark navy background. Make it a crisp flat 2D logo on a dark canvas, with smooth clean antialiased edges, no checkerboard, no texture, no specks, no glow, no shadows, no gradients and no extra elements or words. Preserve the same full square composition and margins.
```
