-- Lantern Market | Hand-built street set. R restores the low reference camera.
local Lighting = require "MarketLighting"
---@type Scene
local scene_
---@type Node
local cameraNode_
---@type Camera
local camera_

local eyeHeight = 0.42
local homePitch = -math.deg(math.atan((568 - 843 / 2) / 930))
local pitch_, yaw_ = homePitch, 0.0
local lastAspect_ = 0.0
local worklight_ = false

local function frameCamera()
    local aspect = graphics:GetWidth() / math.max(1, graphics:GetHeight())
    if aspect ~= lastAspect_ then
        -- Preserve the calibrated lens; crop rather than stretch on a different display.
        camera_.fov = 2 * math.deg(math.atan(math.min(843, 1500 / aspect) / (2 * 930)))
        lastAspect_ = aspect
    end
end

local function resetCamera()
    pitch_, yaw_ = homePitch, 0
    cameraNode_.position = Vector3(0, eyeHeight, 0)
    cameraNode_.rotation = Quaternion(pitch_, yaw_, 0)
end

local function place(resource, position, heading)
    local node = scene_:CreateChild()
    node:LoadXML(cache:GetResource("XMLFile", "NightMarket/" .. resource .. ".xml"):GetRoot())
    node.position = position
    node.rotation = Quaternion(0, heading, 0)
end

function Start()
    graphics.windowTitle = "灯笼街 · Lantern Market"
    scene_ = Scene()
    scene_:CreateComponent("Octree")
    place("Market", Vector3(0,0,0), 23.7)
    place("Actors/Cat", Vector3(.011,0,2.06), -24)
    place("Actors/Worker", Vector3(1.17,.008,9.30), 16)
    Lighting.Create(scene_)

    cameraNode_ = scene_:CreateChild("Reference camera")
    camera_ = cameraNode_:CreateComponent("Camera")
    camera_.nearClip, camera_.farClip = 0.04, 60
    frameCamera()
    resetCamera()
    renderer:SetViewport(0, Viewport:new(scene_, camera_))
    SubscribeToEvent("Update", "HandleUpdate")
    print("[Market] WASD: move | RMB: look | Q/E: lower/raise | L: work light | F: workshop haze (night) | R: reference framing")
end

local function axis(positive, negative)
    return (input:GetKeyDown(positive) and 1 or 0) - (input:GetKeyDown(negative) and 1 or 0)
end

---@param eventData UpdateEventData
function HandleUpdate(_, eventData)
    frameCamera()
    if input:GetKeyPress(KEY_R) then resetCamera(); return end
    if input:GetKeyPress(KEY_L) then worklight_ = not worklight_; Lighting.Worklight(worklight_) end
    if not worklight_ and input:GetKeyPress(KEY_F) then Lighting.ToggleWorkshopMist() end
    local look = input:GetMouseButtonDown(MOUSEB_RIGHT)
    if look and input.mouseMode ~= MM_RELATIVE then
        input.mouseMode = MM_RELATIVE
    elseif not look and input.mouseMode == MM_RELATIVE then
        input.mouseMode = MM_ABSOLUTE
    elseif look then
        yaw_ = (yaw_ + input.mouseMoveX * 0.12) % 360
        pitch_ = Clamp(pitch_ + input.mouseMoveY * 0.12, -85, 85)
        cameraNode_.rotation = Quaternion(pitch_, yaw_, 0)
    end
    local dx, dy, dz = axis(KEY_D, KEY_A), axis(KEY_E, KEY_Q), axis(KEY_W, KEY_S)
    if dx ~= 0 or dy ~= 0 or dz ~= 0 then
        local walk = Quaternion(0,yaw_,0) * Vector3(dx,dy,dz):Normalized()
        local p = cameraNode_.position + walk * (eventData["TimeStep"]:GetFloat() * 1.8)
        cameraNode_.position = Vector3(p.x, Clamp(p.y,.13,12.0), p.z)
    end
end
