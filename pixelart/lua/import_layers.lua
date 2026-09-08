-- Assemble an editable Aseprite document from the PNG cel manifest made by
-- `pixelart render`. Invoke through the CLI; `manifest` is an absolute path.

local manifest_path = app.params.manifest
if not manifest_path or manifest_path == "" then
  error("missing --script-param manifest=/absolute/path/to/aseprite-manifest.json")
end

local handle, read_error = io.open(manifest_path, "r")
if not handle then error("cannot read manifest: " .. tostring(read_error)) end
local manifest_text = handle:read("*a")
handle:close()
local spec = json.decode(manifest_text)

local function rgb(hex)
  local value = string.gsub(hex, "#", "")
  local alpha = 255
  if string.len(value) == 8 then alpha = tonumber(string.sub(value, 7, 8), 16) end
  return Color{r=tonumber(string.sub(value, 1, 2), 16), g=tonumber(string.sub(value, 3, 4), 16), b=tonumber(string.sub(value, 5, 6), 16), a=alpha}
end

local sprite = Sprite{ width=spec.width, height=spec.height, colorMode=ColorMode.RGB }
if #sprite.layers > 0 then sprite:deleteLayer(sprite.layers[1]) end
local layers = {}
for index, layer_spec in ipairs(spec.layers) do
  local layer = sprite:newLayer()
  layer.name = layer_spec.name
  layer.isVisible = layer_spec.visible
  layer.opacity = layer_spec.opacity
  layers[index] = layer
end
for frame_index = 2, #spec.frames do sprite:newEmptyFrame() end
for frame_index, frame_spec in ipairs(spec.frames) do
  sprite.frames[frame_index].duration = frame_spec.duration / 1000.0
  for layer_index, filename in ipairs(frame_spec.cels) do
    sprite:newCel(layers[layer_index], frame_index, Image{ fromFile=filename }, Point(0, 0))
  end
end
local palette = sprite.palettes[1]
palette:resize(#spec.palette)
for index, hex in ipairs(spec.palette) do palette:setColor(index - 1, rgb(hex)) end
local directions = {forward=AniDir.FORWARD, reverse=AniDir.REVERSE, pingpong=AniDir.PING_PONG, pingpong_reverse=AniDir.PING_PONG_REVERSE}
for _, tag_spec in ipairs(spec.tags) do
  local tag = sprite:newTag(tag_spec["from"] + 1, tag_spec["to"] + 1)
  tag.name = tag_spec.name
  tag.aniDir = directions[tag_spec.direction or "forward"]
end
sprite:saveAs(spec.output)
