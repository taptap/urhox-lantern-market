shader_type spatial;
render_mode shading_model_pbr, cull_back;

// All inputs describe the surface itself. Incident light, visibility, bounced
// light and reflections are the renderer's responsibility.
uniform sampler2D grain : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D relief : filter_linear_mipmap, repeat_enable;
uniform vec4 tint = vec4(1.0);
uniform vec4 finish = vec4(1.0, 0.0, 1.0, 0.0); // repeats/m, metal, roughness multiplier, rain
uniform float damage = 0.0;

void fragment() {
    vec2 st = UV * finish.x;
    vec3 pigment = texture(grain, st).rgb;
    vec4 surface = texture(relief, st);
    float wear = damage * surface.a;
    float water = finish.w * smoothstep(.31,.64,mix(texture(relief, st * .57 + vec2(.27,.19)).a, surface.a, .36));
    ALBEDO = mix(tint.rgb * pigment, vec3(.19,.085,.041)*pigment, wear) * (1.0 - .39*water);
    METALLIC = finish.y * (1.0 - .82*wear);
    ROUGHNESS = clamp(mix(surface.b * finish.z, .085 + .09*surface.b, water), .065, 1.0);
    vec2 slope = (surface.rg*2.0-1.0) * (1.0 - .59*water);
    NORMAL_MAP = normalize(vec3(slope, 1.0)) * .5 + .5;
}
