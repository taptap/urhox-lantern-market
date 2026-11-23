shader_type spatial;
render_mode shading_model_pbr, blend_mix, cull_back;

// The paper scatters the actual lights inside the box. Oblique rays traverse more
// dyed fibre than rays normal to the sheet. The print has no illumination in it.
uniform sampler2D ink : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D fibre : source_color, filter_linear_mipmap, repeat_enable;

void fragment() {
    vec3 pigment = texture(ink, UV).rgb;
    float density = texture(fibre, UV).r;
    ALBEDO = pigment * vec3(.58, .27, .17);
    BACKLIGHT = pigment * sqrt(pigment) * (.68 + .46 * density);
    ROUGHNESS = .94;
    SPECULAR = .08;
    ALPHA = .995;
}

void light() {
    float nl = dot(NORMAL, LIGHT);
    float back = max(-nl, 0.0);
    vec3 transmittance = exp(-vec3(.16, 1.56, 1.92) / max(back, .08));
    DIFFUSE_LIGHT += LIGHT_COLOR * ATTENUATION * .31831 *
        (ALBEDO * max(nl, 0.0) + BACKLIGHT * back * transmittance);
}
