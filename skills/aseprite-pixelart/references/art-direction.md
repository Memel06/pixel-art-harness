# Pixel-art production and review

## Turn a request into a working brief

Record subject, purpose, native canvas/frame size, camera/perspective, silhouette priorities, light direction, palette budget, transparency, animation states/timing, anchor/origin, exports and references. Infer sensible defaults when unspecified; state choices and proceed. Existing project art direction takes precedence over example palettes or dimensions. Preserve reference provenance alongside the brief.

## Author at the target pixel grid

Start with three to five large value masses and test the silhouette at 1×. Establish a focal hierarchy before texture. Select related material ramps with deliberate hue/value shifts, shared darkest and lightest accents where helpful, and a small accent budget. Use deliberate clusters and controlled stair-step rhythms; remove isolated pixels that do not communicate form, texture or a highlight. Avoid pillow shading, uniformly black interior outlines, banding along contours and noisy texture. Dither only where it contributes material or a specific value transition.

Separate editable layers by meaningful function: background, silhouette/base, material shading, accents, foreground/effects. Keep a stable pivot and transparent padding across animation. Describe motion with readable key poses and spacing; avoid changing shading randomly between frames. Use native-size playback to check timing and volume consistency.

## Reference-assisted work

References guide silhouette, material, lighting and composition. Inspect supplied images before adapting them. For optional generated concept references, use the environment's image-generation skill/tool when available. Prompt for a clear subject, readable silhouette, chosen camera and lighting, quiet background, and material/color intent. Image generation is optional and must not require API credentials in the normal agent workflow. Do not claim Google Imagen integration: the available image-generation provider depends on the host.

A generated high-resolution picture is a concept reference, not automatically production pixel art. Rebuild important shapes on the native grid, simplify the palette, and author clean clusters in Aseprite. If importing a raster as a starting layer, preserve the reference, make the conversion explicit, and visually rework the result. Do not equate nearest-neighbor resizing or quantization with finishing the art. When the host requires its image tool for editing an image, obey that tool policy; Aseprite-native drawing remains the main route for original pixel assets.

## Review before delivery

Inspect the rendered artifact, not just its script or technical report. Review both 1× and nearest-neighbor enlarged views, the silhouette and the frame contact sheet; inspect playback when animated. Check:

- Does the requested subject read immediately at its intended display size?
- Are focal point, pose and negative space clear without detail?
- Do value groups separate adjacent forms and the background?
- Are material, light direction, outline weight and perspective consistent?
- Are edges and clusters intentional, with no stray pixels, awkward tangencies or unintended seams?
- Do frames retain volume, anchor and palette while movement and timing read clearly?
- Do editable source, PNGs and metadata describe the same final version?

Use technical QA to find palette, alpha, bounds and empty-frame problems, not as an aesthetic score. Write concrete observations, revise the highest-impact defect, render again and inspect the changed views. Continue while visible defects remain and progress is meaningful. Keep prior versions so comparisons are possible. If a limitation prevents the requested quality, disclose it instead of labeling the result exceptional.

For tiles, additionally test a repeated 3×3 patch and adjacent variants. For game sprites, composite onto representative light and dark backgrounds and check the foot origin in motion. These are conditional checks, not requirements for every icon.
