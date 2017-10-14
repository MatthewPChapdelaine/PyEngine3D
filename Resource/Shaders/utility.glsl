#include "scene_constants.glsl"


float get_luminance(vec3 color)
{
    return dot(vec3(0.2126, 0.7152, 0.0722), color);
}

/* non-linear depth to linear depth */
float depth_to_linear_depth(float depth)
{
    const float zNear = near_far.x;
    const float zFar = near_far.y;
    /* depth [0, 1] to NDC Z [-1, 1] */
    depth = depth * 2.0 - 1.0;
    /* NDC Z to distance[near, far] */
    return 2.0 * zNear * zFar / (zFar + zNear - depth * (zFar - zNear));
}

/* linear depth to non-linear depth */
float linear_depth_to_depth(float linear_depth)
{
    const float zNear = near_far.x;
    const float zFar = near_far.y;
    /* linear_depth to NDC Z [-1, 1] */
    float depth = (zFar + zNear - 2.0 * zNear * zFar / linear_depth) / (zFar - zNear);
    /* NDC Z [-1, 1] to depth [0, 1] */
    return depth * 0.5 + 0.5;
}

vec4 depth_to_relative_world(vec2 tex_coord, float depth)
{
    vec4 clip_coord = vec4(tex_coord * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    vec4 relative_pos = inv_view_origin * inv_perspective * clip_coord;
    relative_pos /= relative_pos.w;
    return relative_pos;
}

vec4 linear_depth_to_relative_world(vec2 tex_coord, float linear_depth)
{
    // way 1
    float depth = linear_depth_to_depth(linear_depth);

    // way 2
    //vec4 ndc = perspective * vec4(0.0, 0.0, -linear_depth, 1.0);
    //vec4 clip_coord = vec4(texcoord * 2.0 - 1.0, ndc.z / ndc.w, 1.0);

    return depth_to_relative_world(tex_coord, depth);
}

float rand(vec2 co){
    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

float rand2(vec4 seed4){
    float dot_product = dot(seed4, vec4(12.9898,78.233,45.164,94.673));
    return fract(sin(dot_product) * 43758.5453);
}

vec3 invert_y(vec3 vector)
{
    return vec3(vector.x, -vector.y, vector.z);
}