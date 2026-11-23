shader_type spatial;
render_mode shading_model_pbr, cull_back;

uniform sampler2D ink : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 stock = vec4(1.0);
uniform float output_gain = 0.0;
uniform float power = 1.0;

void fragment() {
    vec3 print_color = texture(ink, UV).rgb * stock.rgb;
    ALBEDO = print_color * .68;
    ROUGHNESS = .83;
    SPECULAR = .13;
    METALLIC = .02;
    EMISSION = print_color * (output_gain * power);
}
