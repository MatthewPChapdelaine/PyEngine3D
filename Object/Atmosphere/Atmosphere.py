import time
import math

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDeleteShader

import numpy as np

from Common import logger
from App import CoreManager
from OpenGLContext import VertexArrayBuffer

from Utilities import Attributes
from .constants import *
from .model import *


class Luminance:
    NONE = 0
    APPROXIMATE = 1
    PRECOMPUTED = 2


class Atmosphere:
    def __init__(self, **object_data):
        self.name = object_data.get('name', 'atmosphere')
        self.attributes = Attributes()
        self.is_render_atmosphere = True
        self.use_constant_solar_spectrum = False
        self.use_ozone = True
        self.use_combined_textures = True
        self.luminance_type = Luminance.NONE
        self.num_precomputed_wavelengths = 15 if Luminance.PRECOMPUTED == self.luminance_type else 3
        self.do_white_balance = False
        self.show_help = True
        self.view_distance_meters = 9000.0
        self.view_zenith_angle_radians = 1.47
        self.view_azimuth_angle_radians = -0.1
        self.sun_zenith_angle_radians = 1.3
        self.sun_azimuth_angle_radians = 2.9
        self.sun_direction = Float3()

        self.white_point = Float3()
        self.earth_center = Float3(0.0, -kBottomRadius / kLengthUnitInMeters, 0.0)
        self.sun_size = Float2(math.tan(kSunAngularRadius), math.cos(kSunAngularRadius))

        self.kSky = Float3(1.0, 1.0, 1.0)
        self.kSun = Float3(1.0, 1.0, 1.0)

        self.atmosphere_exposure = 0.0001

        # cloud constants
        self.cloud_altitude = 100.0
        self.cloud_height = 500.0
        self.cloud_speed = 0.01
        self.cloud_absorption = 0.15

        self.cloud_contrast = 2.0
        self.cloud_coverage = 0.9
        self.cloud_tiling = 0.0004

        self.noise_contrast = 1.0
        self.noise_coverage = 1.0
        self.noise_tiling = 0.0003

        self.model = None
        self.atmosphere_material_instance = None
        self.atmosphere_demo_material_instance = None

        self.transmittance_texture = None
        self.scattering_texture = None
        self.irradiance_texture = None
        self.optional_single_mie_scattering_texture = None

        self.cloud_texture = None
        self.noise_texture = None

        positions = np.array([(-1, 1, 0, 1), (-1, -1, 0, 1), (1, -1, 0, 1), (1, 1, 0, 1)], dtype=np.float32)
        indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
        self.quad = VertexArrayBuffer(
            name='atmosphere quad',
            datas=[positions, ],
            index_data=indices,
            dtype=np.float32
        )

        self.load_data(object_data)

        self.initialize()

    def getAttribute(self):
        self.attributes.setAttribute('is_render_atmosphere', self.is_render_atmosphere)

        self.attributes.setAttribute('atmosphere_exposure', self.atmosphere_exposure)

        self.attributes.setAttribute('cloud_altitude', self.cloud_altitude)
        self.attributes.setAttribute('cloud_height', self.cloud_height)
        self.attributes.setAttribute('cloud_tiling', self.cloud_tiling)
        self.attributes.setAttribute('cloud_speed', self.cloud_speed)

        self.attributes.setAttribute('cloud_contrast', self.cloud_contrast)
        self.attributes.setAttribute('cloud_coverage', self.cloud_coverage)
        self.attributes.setAttribute('cloud_absorption', self.cloud_absorption)

        self.attributes.setAttribute('noise_tiling', self.noise_tiling)
        self.attributes.setAttribute('noise_contrast', self.noise_contrast)
        self.attributes.setAttribute('noise_coverage', self.noise_coverage)
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)

    def load_data(self, object_data):
        for key, value in object_data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_save_data(self):
        save_data = {}
        for attribute in self.attributes.getAttributeNames():
            save_data[attribute] = self.attributes.getAttribute(attribute).value
        return save_data

    def initialize(self):
        resource_manager = CoreManager.instance().resource_manager

        # load material instance
        macros = {
            'USE_LUMINANCE': 1 if self.luminance_type else 0,
            'COMBINED_SCATTERING_TEXTURES': 1 if self.use_combined_textures else 0
        }
        self.atmosphere_material_instance = resource_manager.getMaterialInstance(
            'precomputed_atmosphere.atmosphere', macros=macros)

        self.atmosphere_demo_material_instance = resource_manager.getMaterialInstance(
            'precomputed_atmosphere.atmosphere_demo', macros=macros)

        # precompute constants
        max_sun_zenith_angle = 120.0 / 180.0 * kPi

        rayleigh_layer = DensityProfileLayer(0.0, 1.0, -1.0 / kRayleighScaleHeight, 0.0, 0.0)
        mie_layer = DensityProfileLayer(0.0, 1.0, -1.0 / kMieScaleHeight, 0.0, 0.0)

        ozone_density = [DensityProfileLayer(25000.0, 0.0, 0.0, 1.0 / 15000.0, -2.0 / 3.0),
                         DensityProfileLayer(0.0, 0.0, 0.0, -1.0 / 15000.0, 8.0 / 3.0)]

        wavelengths = []
        solar_irradiance = []
        rayleigh_scattering = []
        mie_scattering = []
        mie_extinction = []
        absorption_extinction = []
        ground_albedo = []

        for i in range(kLambdaMin, kLambdaMax + 1, 10):
            L = float(i) * 1e-3  # micro-meters
            mie = kMieAngstromBeta / kMieScaleHeight * math.pow(L, -kMieAngstromAlpha)
            wavelengths.append(i)
            if self.use_constant_solar_spectrum:
                solar_irradiance.append(kConstantSolarIrradiance)
            else:
                solar_irradiance.append(kSolarIrradiance[int((i - kLambdaMin) / 10)])
            rayleigh_scattering.append(kRayleigh * math.pow(L, -4))
            mie_scattering.append(mie * kMieSingleScatteringAlbedo)
            mie_extinction.append(mie)
            if self.use_ozone:
                absorption_extinction.append(kMaxOzoneNumberDensity * kOzoneCrossSection[int((i - kLambdaMin) / 10)])
            else:
                absorption_extinction.append(0.0)
            ground_albedo.append(kGroundAlbedo)

        rayleigh_density = [rayleigh_layer, ]
        mie_density = [mie_layer, ]

        if Luminance.PRECOMPUTED == self.luminance_type:
            self.kSky[...] = [MAX_LUMINOUS_EFFICACY, MAX_LUMINOUS_EFFICACY, MAX_LUMINOUS_EFFICACY]
        else:
            self.kSky[...] = ComputeSpectralRadianceToLuminanceFactors(wavelengths, solar_irradiance, -3)
        self.kSun[...] = ComputeSpectralRadianceToLuminanceFactors(wavelengths, solar_irradiance, 0)

        # generate precomputed textures
        if not resource_manager.texture_loader.hasResource('precomputed_atmosphere.transmittance') or \
                not resource_manager.texture_loader.hasResource('precomputed_atmosphere.scattering') or \
                not resource_manager.texture_loader.hasResource('precomputed_atmosphere.irradiance') or \
                not resource_manager.texture_loader.hasResource(
                    'precomputed_atmosphere.optional_single_mie_scattering') and not self.use_combined_textures:
            model = Model(wavelengths,
                          solar_irradiance,
                          kSunAngularRadius,
                          kBottomRadius,
                          kTopRadius,
                          rayleigh_density,
                          rayleigh_scattering,
                          mie_density,
                          mie_scattering,
                          mie_extinction,
                          kMiePhaseFunctionG,
                          ozone_density,
                          absorption_extinction,
                          ground_albedo,
                          max_sun_zenith_angle,
                          kLengthUnitInMeters,
                          self.num_precomputed_wavelengths,
                          Luminance.PRECOMPUTED == self.luminance_type,
                          self.use_combined_textures)
            model.generate()

        self.transmittance_texture = resource_manager.getTexture('precomputed_atmosphere.transmittance')
        self.scattering_texture = resource_manager.getTexture('precomputed_atmosphere.scattering')
        self.irradiance_texture = resource_manager.getTexture('precomputed_atmosphere.irradiance')

        if not self.use_combined_textures:
            self.optional_single_mie_scattering_texture = resource_manager.getTexture(
                'precomputed_atmosphere.optional_single_mie_scattering')

        self.cloud_texture = resource_manager.getTexture('precomputed_atmosphere.cloud_3d')
        self.noise_texture = resource_manager.getTexture('precomputed_atmosphere.noise_3d')

    def update(self, main_light):
        if not self.is_render_atmosphere:
            return

        self.sun_direction[...] = main_light.transform.front

    def bind_precomputed_atmosphere(self, material_instance, render_object=True):
        material_instance.bind_uniform_data("transmittance_texture", self.transmittance_texture)
        material_instance.bind_uniform_data("scattering_texture", self.scattering_texture)
        material_instance.bind_uniform_data("irradiance_texture", self.irradiance_texture)

        if not self.use_combined_textures:
            material_instance.bind_uniform_data(
                "single_mie_scattering_texture", self.optional_single_mie_scattering_texture)

        material_instance.bind_uniform_data("SKY_RADIANCE_TO_LUMINANCE", self.kSky * self.atmosphere_exposure)
        material_instance.bind_uniform_data("SUN_RADIANCE_TO_LUMINANCE", self.kSun * self.atmosphere_exposure)

        material_instance.bind_uniform_data("atmosphere_exposure", self.atmosphere_exposure)
        material_instance.bind_uniform_data("earth_center", self.earth_center)

        material_instance.bind_uniform_data("texture_cloud", self.cloud_texture)
        material_instance.bind_uniform_data("texture_noise", self.noise_texture)

        material_instance.bind_uniform_data('cloud_altitude', self.cloud_altitude)
        material_instance.bind_uniform_data('cloud_height', self.cloud_height)
        material_instance.bind_uniform_data('cloud_speed', self.cloud_speed)
        material_instance.bind_uniform_data('cloud_absorption', self.cloud_absorption)

        material_instance.bind_uniform_data('cloud_tiling', self.cloud_tiling)
        material_instance.bind_uniform_data('cloud_contrast', self.cloud_contrast)
        material_instance.bind_uniform_data('cloud_coverage', self.cloud_coverage)

        material_instance.bind_uniform_data('noise_tiling', self.noise_tiling)
        material_instance.bind_uniform_data('noise_contrast', self.noise_contrast)
        material_instance.bind_uniform_data('noise_coverage', self.noise_coverage)

    def render_precomputed_atmosphere(self, texture_linear_depth, texture_shadow, render_sun):
        if not self.is_render_atmosphere:
            return

        self.quad.bind_vertex_buffer()
        self.atmosphere_material_instance.use_program()
        self.atmosphere_material_instance.bind_material_instance()
        self.atmosphere_material_instance.bind_uniform_data("texture_linear_depth", texture_linear_depth)
        self.atmosphere_material_instance.bind_uniform_data("texture_shadow", texture_shadow)
        self.atmosphere_material_instance.bind_uniform_data("sun_size", self.sun_size)
        self.atmosphere_material_instance.bind_uniform_data("render_sun", render_sun)
        self.bind_precomputed_atmosphere(self.atmosphere_material_instance, render_object=False)
        self.quad.draw_elements()
