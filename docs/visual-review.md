# Skywhale Observatory — visual review

![Skywhale Observatory, native Aseprite export enlarged 2× without smoothing](demo-preview.png)

The new showcase is an original 320×208 scene built entirely from integer-grid
DSL shapes: a flying whale carrying a warm observatory town above a twilight
cloud ocean. Eight editable layers separate atmosphere, whale body, near flipper,
terraces, observatory, travelers and foreground. The 24-color declared palette
uses teal against violet, with warm windows and lanterns. The source uses 22 colors.

The actual native frame, 2× preview, four-frame contact sheet and isolated whale
body silhouette were opened and inspected. The forked tail and rounded head read
at native size; the flipper, belly pleats and directional back highlights give the
body volume. Windows, the telescope and a tiny bow passenger establish scale.

The first render had abrupt sky-band edges and flat cloud masses. The second
version breaks those boundaries into stepped shelves and adds cloud-cap
highlights. The revised native export was opened again. The sky remains visibly
stylized and horizontal; motion is a small ambient loop, not a full swimming
animation. Frame continuity and encoded durations were checked, but real-time
playback was not reviewed.

[View the four-frame animation](demo-preview.gif). The flipper, pennants and
lanterns change across four 180 ms frames. All decoded GIF frames match their
opaque PNG previews exactly. This check caught and fixed a real GIF-export bug:
the old exporter made a used palette index transparent.

Aseprite reopened the editable document and exported exactly matching pixels
and durations for all four frames. This establishes file consistency, separate
from the visual observations above.

Reproduce with `pixelart render examples/skywhale.json --out output/demo`.
See the [brief](../examples/skywhale-brief.md) and the deterministic
[authoring script](../examples/build_skywhale.py). The original
[moonlit courier](../examples/moonlit-courier.json) remains as a smaller example.
