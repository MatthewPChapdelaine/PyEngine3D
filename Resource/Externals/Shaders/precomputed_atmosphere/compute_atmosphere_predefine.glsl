const int TRANSMITTANCE_TEXTURE_WIDTH = 256;
const int TRANSMITTANCE_TEXTURE_HEIGHT = 64;
const int SCATTERING_TEXTURE_R_SIZE = 32;
const int SCATTERING_TEXTURE_MU_SIZE = 128;
const int SCATTERING_TEXTURE_MU_S_SIZE = 32;
const int SCATTERING_TEXTURE_NU_SIZE = 8;
const int IRRADIANCE_TEXTURE_WIDTH = 64;
const int IRRADIANCE_TEXTURE_HEIGHT = 16;

#include "precomputed_atmosphere/definitions.glsl"

const AtmosphereParameters ATMOSPHERE = AtmosphereParameters(
vec3(1.474000, 1.850400, 1.911980),
0.004675,
6360.0,
6420.0,
DensityProfile(DensityProfileLayer[2](DensityProfileLayer(0.000000, 0.000000, 0.000000, 0.000000, 0.000000),DensityProfileLayer(0.000000, 1.000000, -0.125000, 0.000000, 0.000000))),
vec3(0.005802, 0.013558, 0.033100),
DensityProfile(DensityProfileLayer[2](DensityProfileLayer(0.000000, 0.000000, 0.000000, 0.000000, 0.000000),DensityProfileLayer(0.000000, 1.000000, -0.833333, 0.000000, 0.000000))),
vec3(0.003996, 0.003996, 0.003996),
vec3(0.004440, 0.004440, 0.004440),
0.8,
DensityProfile(DensityProfileLayer[2](DensityProfileLayer(25.000000, 0.000000, 0.000000, 0.066667, -0.666667),DensityProfileLayer(0.000000, 0.000000, 0.000000, -0.066667, 2.666667))),
vec3(0.000650, 0.001881, 0.000085),
vec3(0.100000, 0.100000, 0.100000),
-0.4999999690599179);
const vec3 SKY_SPECTRAL_RADIANCE_TO_LUMINANCE = vec3(114974.916437, 71305.954816, 65310.548555);
const vec3 SUN_SPECTRAL_RADIANCE_TO_LUMINANCE = vec3(98242.786222, 69954.398112, 66475.012354);

#include "precomputed_atmosphere/functions.glsl"