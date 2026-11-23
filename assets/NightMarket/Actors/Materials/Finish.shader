shader_type spatial;
render_mode shading_model_pbr, cull_back;

// COLOR stores the pigment swatch; UV.xy stores each solid's roughness and metalness.
uniform float phosphor = 0.0;

void fragment() {
    vec3 pigment = pow(COLOR.rgb, vec3(2.2));
    ALBEDO = pigment;
    ROUGHNESS = UV.x;
    METALLIC = UV.y;
    EMISSION = pigment * phosphor;
}
