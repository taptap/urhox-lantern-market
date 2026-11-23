shader_type spatial;
render_mode shading_model_pbr, cull_back;

// Modulation by a seamless, synthesized fibre swatch fixed to the solid, never to the camera.
uniform sampler2D yarn : filter_linear_mipmap, repeat_enable;
uniform float coat = 0.0;
varying vec3 rest_point;
varying vec3 rest_normal;

void vertex() {
    rest_point = VERTEX;
    rest_normal = NORMAL;
}

void fragment() {
    vec3 p = rest_point * mix(12.0, 22.0, coat);
    vec3 w = abs(rest_normal);
    w *= w;
    w /= max(0.001, w.x + w.y + w.z);
    float leg = coat * (1.0 - smoothstep(0.13, 0.20, rest_point.y));
    float side = mix(texture(yarn, p.yz).r, texture(yarn, p.zy).r, leg);
    float grain = side * w.x + texture(yarn, p.xz).r * w.y + texture(yarn, p.xy).r * w.z;
    if (coat > 0.5) {
        vec2 tuft_uv = vec2(dot(p, vec3(0.76, 0.68, 0.16)), mix(p.z, p.y, leg));
        grain = mix(grain, texture(yarn, tuft_uv * 0.27 + vec2(0.19)).r, 0.46);
    }
    ALBEDO = pow(COLOR.rgb, vec3(2.2)) * (1.0 + mix(0.40, 0.76, coat) * (grain - 0.5));
    ROUGHNESS = clamp(UV.x + (grain - 0.5) * 0.12, 0.0, 1.0);
    METALLIC = UV.y;
    SPECULAR = mix(0.30, 0.22, coat);
}
