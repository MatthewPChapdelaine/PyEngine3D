from collections import OrderedDict
import os
import glob
import math
import time as timeModule

import numpy as np

from Common import logger
from Object import StaticActor, Camera, Light
from OpenGLContext import UniformBlock
from Utilities import Singleton, GetClassName, Attributes, FLOAT_ZERO, FLOAT4_ZERO, MATRIX4_IDENTITY, Matrix4


class SceneManager(Singleton):
    def __init__(self):
        self.coreManager = None
        self.resource_manager = None
        self.sceneLoader = None
        self.renderer = None
        self.framebuffer = None
        self.__current_scene_name = ""

        # Scene Objects
        self.mainCamera = None
        self.selectedObject = None

        self.cameras = []
        self.lights = []
        self.static_actors = []
        self.objectMap = {}  # All of objects

    def initialize(self, core_manager):
        logger.info("initialize " + GetClassName(self))
        self.coreManager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.sceneLoader = self.resource_manager.sceneLoader
        self.renderer = core_manager.renderer

        # new scene
        self.new_scene()

    def get_current_scene_name(self):
        return self.__current_scene_name

    def set_current_scene_name(self, scene_name):
        self.__current_scene_name = scene_name
        self.coreManager.set_window_title(scene_name)

    def clear_scene(self):
        self.coreManager.notifyClearScene()
        self.mainCamera = None
        self.cameras = []
        self.lights = []
        self.static_actors = []
        self.objectMap = {}
        resource = self.resource_manager.sceneLoader.getResource(self.__current_scene_name)
        if resource is not None and not os.path.exists(resource.meta_data.resource_filepath):
            self.resource_manager.sceneLoader.delete_resource(self.__current_scene_name)

    def new_scene(self):
        self.clear_scene()

        # add scene objects
        self.mainCamera = self.addCamera()
        self.addLight()

        self.set_current_scene_name(self.resource_manager.sceneLoader.get_new_resource_name("new_scene"))

        self.resource_manager.sceneLoader.create_resource(self.__current_scene_name)

    def open_scene(self, scene_name, scene_data):
        self.clear_scene()
        self.set_current_scene_name(scene_name)

        self.mainCamera = self.addCamera(scene_data.get('camera'))
        self.addLight(scene_data.get('light'))

        for object_data in scene_data.get('staticmeshes', []):
            self.addObject(**object_data)

    def save_scene(self):
        if self.__current_scene_name == "":
            self.set_current_scene_name(self.resource_manager.sceneLoader.get_new_resource_name("new_scene"))
        self.resource_manager.sceneLoader.save_resource(self.__current_scene_name)

    def get_save_data(self):
        static_actors = [static_actor.get_save_data() for static_actor in self.static_actors]
        scene_data = dict(
            camera=self.mainCamera.name,
            light=self.lights[0].name,
            static_actors=static_actors
        )
        return scene_data

    def generateObjectName(self, currName):
        index = 0
        if currName in self.objectMap:
            while True:
                newName = "%s_%d" % (currName, index)
                if newName not in self.objectMap:
                    return newName
                index += 1
        return currName

    def get_object_list(self, object_type):
        if Camera == object_type:
            return self.cameras
        elif Light == object_type:
            return self.lights
        elif StaticActor == object_type:
            return self.static_actors
        return None

    def regist_object(self, object):
        if object and object.name not in self.objectMap:
            object_list = self.get_object_list(type(object))
            object_list.append(object)
            self.objectMap[object.name] = object
            self.coreManager.sendObjectInfo(object)

    def unregist_resource(self, object):
        if object and object.name in self.objectMap:
            object_list = self.get_object_list(type(object))
            object_list.remove(object)
            self.objectMap.pop(object.name)

    def getMainCamera(self):
        return self.mainCamera

    def addCamera(self, name=''):
        camera_name = self.generateObjectName(name or "camera")
        logger.info("add Camera : %s" % camera_name)
        camera = Camera(camera_name,
                        scene_manager=self,
                        pos=(0, 0, 0),
                        model=self.resource_manager.getModel('Quad'))
        camera.initialize()
        self.regist_object(camera)
        return camera

    def addLight(self, name=''):
        light_name = self.generateObjectName(name or "light")
        logger.info("add Light : %s" % light_name)
        light = Light(light_name,
                      pos=(0, 0, 0),
                      model=self.resource_manager.getModel('Quad'),
                      lightColor=(1.0, 1.0, 1.0, 1.0))
        self.regist_object(light)
        return light

    def addObject(self, **object_data):
        model = object_data.get('model')
        if model:
            objName = self.generateObjectName(model.name)
            objType = GetClassName(model)
            logger.info("add %s : %s" % (objType, objName))

            if 'Model' == objType:
                obj_instance = StaticActor(objName, **object_data)
            else:
                obj_instance = None
            # regist
            self.regist_object(obj_instance)
            return obj_instance
        return None

    def addObjectHere(self, model):
        camera = self.getMainCamera()
        pos = camera.transform.pos + camera.get_view_dir() * 10.0
        return self.addObject(model=model, pos=pos)

    def clearObjects(self):
        self.cameras = []
        self.lights = []
        self.static_actors = []
        self.objectMap = {}

    def clear_static_actors(self):
        for static_actor in self.static_actors:
            if static_actor.name in self.objectMap:
                self.objectMap.pop(static_actor.name)
        self.static_actors = []

    def deleteObject(self, objName):
        obj = self.getObject(objName)
        if obj and obj != self.mainCamera:
            self.objectMap.pop(obj.name)
            if obj in self.cameras:
                self.cameras.remove(obj)
            if obj in self.lights:
                self.lights.remove(obj)
            if obj in self.static_actors:
                self.static_actors.remove(obj)
            self.coreManager.notifyDeleteObject(objName)

    def getObject(self, objName):
        return self.objectMap[objName] if objName in self.objectMap else None

    def getObjectNames(self):
        return self.objectMap.keys()

    def getObjects(self):
        return self.objectMap.values()

    def get_static_actors(self):
        return self.static_actors

    def getObjectAttribute(self, objName):
        obj = self.getObject(objName)
        return obj.getAttribute() if obj else None

    def setObjectAttribute(self, objectName, objectType, attributeName, attributeValue, attribute_index):
        obj = self.getObject(objectName)
        obj and obj.setAttribute(attributeName, attributeValue, attribute_index)

    def getSelectedObject(self):
        return self.selectedObject

    def setSelectedObject(self, objName):
        selectedObject = self.getObject(objName)
        if self.selectedObject is not selectedObject:
            if self.selectedObject:
                self.selectedObject.setSelected(False)
            self.selectedObject = selectedObject
            if selectedObject:
                selectedObject.setSelected(True)

    def setObjectFocus(self, objName):
        obj = self.getObject(objName)
        if obj and obj != self.mainCamera:
            self.mainCamera.transform.setPos(obj.transform.pos - self.mainCamera.transform.front * 2.0)

    def update_scene(self, dt):
        for camera in self.cameras:
            camera.update()

        for light in self.lights:
            light.update(dt)

        for obj in self.static_actors:
            obj.update(dt)
