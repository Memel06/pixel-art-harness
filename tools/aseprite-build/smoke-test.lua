-- Creates a layered sprite, writes its editable Aseprite source, and exports a PNG.
-- Inputs are supplied by run-smoke-test.sh through --script-param.
local ase_path = assert(app.params.ase, "missing --script-param ase=<path>")
local png_path = assert(app.params.png, "missing --script-param png=<path>")

local sprite = Sprite(8, 8, ColorMode.RGB)
local base = sprite.layers[1]
base.name = "Base"
local accent = sprite:newLayer()
accent.name = "Accent"

local base_image = sprite.cels[1].image
for y = 0, 7 do
  for x = 0, 7 do
    if x == 0 or x == 7 or y == 0 or y == 7 then
      base_image:drawPixel(x, y, Color(35, 49, 74, 255))
    else
      base_image:drawPixel(x, y, Color(89, 117, 150, 255))
    end
  end
end

local accent_cel = sprite:newCel(accent, 1, Image(8, 8, ColorMode.RGB))
local accent_image = accent_cel.image
accent_image:drawPixel(3, 2, Color(255, 218, 105, 255))
accent_image:drawPixel(4, 2, Color(255, 218, 105, 255))
accent_image:drawPixel(2, 3, Color(255, 218, 105, 255))
accent_image:drawPixel(3, 3, Color(255, 236, 161, 255))
accent_image:drawPixel(4, 3, Color(255, 236, 161, 255))
accent_image:drawPixel(5, 3, Color(255, 218, 105, 255))
accent_image:drawPixel(3, 4, Color(255, 218, 105, 255))
accent_image:drawPixel(4, 4, Color(255, 218, 105, 255))

assert(#sprite.layers == 2, "expected two editable layers")
assert(sprite:saveAs(ase_path), "failed to save .aseprite source")
assert(sprite:saveCopyAs(png_path), "failed to export PNG")
print("smoke-test: wrote layered Aseprite source and PNG export")
