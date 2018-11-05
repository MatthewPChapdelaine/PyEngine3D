const int PARTICLE_STATE_NONE = 0;
const int PARTICLE_STATE_DELAY = 1;
const int PARTICLE_STATE_ALIVE = 2;
const int PARTICLE_STATE_DEAD = 3;

const int ALIGN_MODE_NONE = 0;
const int ALIGN_MODE_BILLBOARD = 1;
const int ALIGN_MODE_VELOCITY_ALIGN = 2;


struct ParticleData
{
    mat4 parent_matrix;
    mat4 local_matrix;
    vec3 force;
    float delay;
    vec3 transform_position;
    float life_time;
    vec3 transform_rotation;
    float opacity;
    vec3 transform_scale;
    float elapsed_time;
    vec3 velocity_position;
    float sequence_ratio;
    vec3 velocity_rotation;
    int sequence_index;
    vec3 velocity_scale;
    int next_sequence_index;
    vec2 sequence_uv;
    vec2 next_sequence_uv;
    vec3 dummy_0;
    int state;
};


struct ParticleIndexRange
{
    uint begin_index;
    uint instance_count;
    uint destroy_count;
    uint dummy;
};


struct DispatchIndirectCommand
{
    uint num_groups_x;
    uint num_groups_y;
    uint num_groups_z;
};


struct DrawElementsIndirectCommand
{
    uint vertex_count;
    uint instance_count;
    uint first_index;
    uint base_vertex;
    uint base_instance;
};
