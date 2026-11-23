shader_type spatial;
render_mode shading_model_pbr, cull_back;

uniform vec4 gas = vec4(1.0);
uniform float output_gain = 1.0;
uniform float cathode = 0.0;
uniform float power = 1.0;

void fragment() {
    // The luminous gas column is thinner at the silhouette of the round glass.
    // UV.y measures metres of glass from the electrode along each physical bend.
    float chord = abs(dot(normalize(NORMAL), normalize(VIEW)));
    float discharge = mix(1.0, smoothstep(0.0, .036, UV.y), cathode);
    vec3 body = vec3(.38 + .62*chord, .06 + .94*chord*chord, .02 + .98*chord*chord*chord);
    vec3 glow = mix(vec3(.49,.021,.003), gas.rgb * body, discharge);
    ALBEDO = vec3(.46, .37, .28);
    ROUGHNESS = .32;
    SPECULAR = .35;
    EMISSION = glow * (output_gain * power);
}
