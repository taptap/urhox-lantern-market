-- Two light rigs, one set of objects and surface materials. In the work-light
-- rig the shop signs retain their printed ink but their backlights are off.
local M = {}
---@type Zone
local zone
---@type Light
local key
---@type Node
local shops
---@type Node
local workshopMist
---@type Material[]
local lamps = {}

---@param scene Scene
function M.Create(scene)
    renderer:SetHDRRendering(true)
    renderer:SetShadowMapSize(2048)
    renderer:SetShadowQuality(SHADOWQUALITY_PCF_24BIT)
    local isGLES = graphics:GetApiName() == "GLES"
    -- This runtime's GLES cluster shader calls shadow2DArray (desktop GLSL).
    -- Keep the directional shadow map, GTAO and all the practical lights on GLES.
    renderer:SetClusterLocalShadowsEnabled(not isGLES)
    renderer:SetVolumetricFogFroxelEnabled(true)
    renderer:SetVolumetricFogQuality(VOLUMETRIC_FOG_QUALITY_HIGH)
    shops = scene:GetChild("Night practicals", true)
    zone = scene:CreateChild("Market air"):CreateComponent("Zone")
    zone.boundingBox = BoundingBox(Vector3(-100,-50,-100), Vector3(100,100,100))
    zone.ambientSource = AMBIENT_COLOR
    zone.envTextureSpecIntensity = 0
    zone.tonemapMode = TONEMAP_MODE_ACES
    zone.autoExposureEnabled = true
    zone.autoExposurePlusEnabled = true
    zone.autoExposureMinBrightness, zone.autoExposureMaxBrightness = 1, 1
    zone.autoExposureBias = 0.75
    zone.autoExposureForceTarget = true
    zone.ssrEnabled = true
    zone.ssrQuality = 3
    zone.ssgiEnabled = true
    zone.ssgiQuality, zone.ssgiIntensity = 2, 0.52
    if isGLES then
        -- Stronger GTAO bands across the curb faces on this GLES backend.
        zone.ssaoRadius, zone.ssaoIntensity = 0.12, 0.10
    else
        zone.ssaoRadius, zone.ssaoIntensity = 0.25, 1.10
    end
    zone.bloomMode = BLOOM_MODE_UE
    zone.bloomUEIntensity, zone.bloomUEThreshold = 0.70, 0.74
    zone.bloomUESizeScale = 5
    zone.motionBlurEnabled = false
    zone.depthFogEnable = true
    zone.depthFogStart, zone.depthFogEnd = 8, 45
    zone.volumetricFogDensity = 0.009
    zone.volumetricFogHeight = 0
    zone.volumetricFogHeightFalloff = 0.07
    zone.volumetricFogViewDistance = 32
    zone.volumetricFogStartDistance = 0
    zone.volumetricFogPhaseG = 0.28
    zone.volumetricFogScatteringColor = Color(0.87,0.77,0.74)
    zone.volumetricFogAbsorptionIntensity = 0
    local lane = scene:GetChild("Foundry lane")
    local function addPocket(parent, name, position, radii, density, albedo)
        local pocket = parent:CreateChild(name)
        pocket.position, pocket.scale = position, radii
        local fog = pocket:CreateComponent("LocalFogVolume")
        fog.albedo = Color(albedo,albedo,albedo)
        fog.phaseG = zone.volumetricFogPhaseG
        fog.radialExtinction = density
    end
    -- Separate pockets let the haze reach the shutter without thickening the air at the fans.
    workshopMist = lane:CreateChild("Workshop haze")
    addPocket(workshopMist, "Workshop canopy haze", Vector3(-4.37,2.90,7.93), Vector3(1.50,1.48,2.30), .69,.96)
    addPocket(workshopMist, "Haze below the noodle sign", Vector3(-4.68,.62,8.80), Vector3(1.37,1.36,1.42), .43,.96)
    addPocket(lane, "Dispensary awning haze", Vector3(-4.57,2.48,5.04), Vector3(1.16,1.01,1.53), .09,.96)
    -- Under the overpass, soften the rear brickwork without turning the opening into a light source.
    addPocket(lane, "Inner passage haze", Vector3(-1.82,1.24,15.90), Vector3(2.52,1.85,2.94), .21,.42)
    key = scene:CreateChild("Overhead light"):CreateComponent("Light")
    key.lightType = LIGHT_DIRECTIONAL
    key.castShadows = true
    key.shadowBias = BiasParameters(0.00035,0.65)
    key.shadowCascade = CascadeParameters(5,14,26,42,0.85)
    lamps = {}
    local seen = {}
    for _, node in ipairs(scene:GetChildrenWithComponent("StaticModel", true)) do
        local model = node:GetComponent("StaticModel")
        for i = 0, model.numGeometries-1 do
            local m = model:GetMaterial(i)
            if m and not seen[m.name] then
                seen[m.name] = true
                if not m:GetShaderParameter("power"):IsEmpty() then
                    lamps[#lamps+1] = m
                end
            end
        end
    end
    M.Worklight(false)
end

function M.ToggleWorkshopMist()
    workshopMist:SetDeepEnabled(not workshopMist.enabled)
end

---@param on boolean
function M.Worklight(on)
    shops:SetDeepEnabled(not on)
    for _, m in ipairs(lamps) do m:SetShaderParameter("power", Variant(on and 0.0 or 1.0)) end
    key.node.direction = on and Vector3(0.53,-0.85,0.54) or Vector3(0.32,-0.90,-0.52)
    key.color = on and Color(1,.97,.92) or Color(.59,.52,.67)
    key.brightness = on and 1.9 or 0.35
    zone.ambientColor = on and Color(.30,.30,.30) or Color(.195,.111,.136)
    zone.fogColor = on and Color(.15,.16,.17) or Color(.18,.092,.112)
    zone.depthFogEnable = not on
    zone.volumetricFogEnabled = not on
    print(string.format("[Market] %s | %d practicals; %d printed/luminous materials", on and "neutral" or "night", shops.numChildren, #lamps))
end

return M
