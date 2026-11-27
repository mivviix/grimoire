---
summary: Measured rules of Roblox GUI layout: text metrics, pixel snapping, UIScale in lists, AutomaticSize, rotation; read before precise UI work
tags: gui, ui, layout, text, textbounds, uiscale, automaticsize, rotation
---
# GUI layout rules (measured in Studio, 2026-11)

## Text
- Line height is TextSize + 1; the baseline sits at floor(top + ascent + 0.5).
- The legacy fonts (LegacyArial / LegacyArimo, the `Instance.new` default) draw at 1.5× TextSize. Set a real `FontFace` on every text object.
- Wrapped text: `TextBounds` counts only the lines that fit the box. UIPadding on a TextLabel insets its own text and narrows the wrap width.
- Weights a font family lacks fall back to the nearest face; Roblox never fakes bold.
- Multi-line TextBounds width can be off by 1 px.

## Boxes
- Positions and sizes snap to whole pixels, rounding half up.
- UIGradient interpolates in linear light, not sRGB, so midpoints look brighter than a CSS gradient.
- With no layout object, scale-sized children count as 0 for an `AutomaticSize` parent; inside a list they measure against the parent's box on the growing axis.

## Transforms
- `UIScale` on a child of a `UIListLayout` grows from the top-left and pushes its siblings. To grow in place, put a holder frame in the list and centre the scaled element inside it.
- `GuiObject.Rotation` turns about the element's own centre, not its AnchorPoint. For spokes or wedges around a wheel centre, put each bar in a full-size holder and rotate the holder.

UI here is built and checked for PC; don't fit phone or tablet unless asked.
