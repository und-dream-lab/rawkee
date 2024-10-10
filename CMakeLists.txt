#-
# ==========================================================================
# Last Updated 10/10/2024
#
# RawKee X3D Plugin 1.2.0 for Maya 2019+
# https://github.com/und-dream-lab/rawkee
#
# For older version of the plug-in (1.1.0) for older versions of Maya (Maya 6.0 - Maya 2008), visit:
# https://rawkee.sourceforge.net/
# 
# Aaron's Build Tools for Rawkee 1.2.0 on Windows 10:
#  - Maya2023
#  - Visual Studio 17 2022
#  - CMake 3.30
#  - PowerShell
#
# Contact Aaron at:
# aaron.bergstrom@und.edu
# UND Computational Research Center - DREAM Lab
# https://dream.crc.und.edu/
#
# Build Instructions using the above build tools.
# 0 - Prior to building RawKee, set the enviornment variables for 
#     RAWKEE_GIT_REPO, DEVKIT_LOCATION, MAYA_LOCATION
#
#     On Aaron's computer, these are:
#     RAWKEE_GIT_REPO    C:\mbuild\rawkee2024\
#     DEVKIT_LOCATION    C:\Users\aaron.bergstrom\devkitBase\
#     MAYA_LOCATION      C:\Program Files\Autodesk\Maya2023\
#
# 1 - Open PowerShell
# 2 - At the PowerShell prompt, change directory to your rawkee git repo location
# 3 - Run the following commands from the prompt
#     clear
#     cmake -Bbuild -G "Visual Studio 17 2022"
#     cmake --build build
#
#     Be sure to delete the "build" directory before you attempt to re-compile/build.
#
# 4 - Copy the following files from your RAWKEE_GIT_REPO location to your Maya Plug-ins folder:
#
#     build\Debug\x3d.mll                to                plug-ins\x3d.mll
#     mel\*.mel                          to                scripts\*.mel
#     icons\*.bmp                        to                icons\*.bmp
# ==========================================================================
#+


cmake_minimum_required(VERSION 3.30)

project(x3d)

# include the project setting file
include($ENV{DEVKIT_LOCATION}/cmake/pluginEntry.cmake)

# specify project name
set(PROJECT_NAME x3d)

######################################################################
# Location of your RawKee Git Repo on your computer.
# For instance, on Aaron's Windows computer, his repo is located here:
# C:\mbuild\rawkee2024\
######################################################################
include_directories($ENV{RAWKEE_GIT_REPO})

#set .mel file list
set(MEL_FILES 
   mel/AEx3dAnchorTemplate.mel
   mel/AEx3dBillboardTemplate.mel
   mel/AEx3dBooleanFilterTemplate.mel
   mel/AEx3dBooleanSequencerTemplate.mel
   mel/AEx3dBooleanToggleTemplate.mel
   mel/AEx3dBooleanTriggerTemplate.mel
   mel/AEx3dBoxTemplate.mel
   mel/AEx3dCollisionTemplate.mel
   mel/AEx3dColorInterpolatorTemplate.mel
   mel/AEx3dColorRGBATemplate.mel
   mel/AEx3dColorTemplate.mel
   mel/AEx3dConeTemplate.mel
   mel/AEx3dCoordinateInterpolatorTemplate.mel
   mel/AEx3dCoordinateTemplate.mel
   mel/AEx3dCylinderSensorTemplate.mel
   mel/AEx3dCylinderTemplate.mel
   mel/AEx3dGamepadSensorTemplate.mel
   mel/AEx3dGroupTemplate.mel
   mel/AEx3dIndexedFaceSetTemplate.mel
   mel/AEx3dInlineTemplate.mel
   mel/AEx3dIntegerSequencerTemplate.mel
   mel/AEx3dIntegerTriggerTemplate.mel
   mel/AEx3dKeySensorTemplate.mel
   mel/AEx3dLoadSensorTemplate.mel
   mel/AEx3dMetadataDoubleTemplate.mel
   mel/AEx3dMetadataFloatTemplate.mel
   mel/AEx3dMetadataIntegerTemplate.mel
   mel/AEx3dMetadataSetTemplate.mel
   mel/AEx3dMetadataStringTemplate.mel
   mel/AEx3dNavigationInfoTemplate.mel
   mel/AEx3dNormalInterpolatorTemplate.mel
   mel/AEx3dNormalTemplate.mel
   mel/AEx3dOrientationInterpolatorTemplate.mel
   mel/AEx3dPlaneSensorTemplate.mel
   mel/AEx3dPositionInterpolatorTemplate.mel
   mel/AEx3dProximitySensorTemplate.mel
   mel/AEx3dRouteTemplate.mel
   mel/AEx3dScalarInterpolatorTemplate.mel
   mel/AEx3dScriptTemplate.mel
   mel/AEx3dSoundTemplate.mel
   mel/AEx3dSphereSensorTemplate.mel
   mel/AEx3dSphereTemplate.mel
   mel/AEx3dStringSensorTemplate.mel
   mel/AEx3dSwitchTemplate.mel
   mel/AEx3dTextureCoordinateTemplate.mel
   mel/AEx3dTimeSensorTemplate.mel
   mel/AEx3dTimeTriggerTemplate.mel
   mel/AEx3dTouchSensorTemplate.mel
   mel/AEx3dVisibilitySensorTemplate.mel
   mel/AEx3dWorldInfoTemplate.mel
   mel/x3d.mel
   mel/x3dUtilCommands.mel
   mel/x3d_anchor_tables.mel
   mel/x3d_appearance_tables.mel
   mel/x3d_audioclip_tables.mel
   mel/x3d_billboard_tables.mel
   mel/x3d_booleanfilter_tables.mel
   mel/x3d_booleansequencer_tables.mel
   mel/x3d_booleantoggle_tables.mel
   mel/x3d_booleantrigger_tables.mel
   mel/x3d_box_tables.mel
   mel/x3d_collidableshape_tables.mel
   mel/x3d_collisioncollection_tables.mel
   mel/x3d_collisionsensor_tables.mel
   mel/x3d_collisionspace_tables.mel
   mel/x3d_collision_tables.mel
   mel/x3d_colorinterpolator_tables.mel
   mel/x3d_colorrgba_tables.mel
   mel/x3d_color_tables.mel
   mel/x3d_cone_tables.mel
   mel/x3d_coordinateinterpolator_tables.mel
   mel/x3d_coordinate_tables.mel
   mel/x3d_cylindersensor_tables.mel
   mel/x3d_cylinder_tables.mel
   mel/x3d_directionallight_tables.mel
   mel/x3d_exporter_procedures.mel
   mel/x3d_gamepadsensor_tables.mel
   mel/x3d_generic_tables.mel
   mel/x3d_group_tables.mel
   mel/x3d_hanimhumanoid_tables.mel
   mel/x3d_hanimjoint_tables.mel
   mel/x3d_hanimsite_tables.mel
   mel/x3d_ie_menus.mel
   mel/x3d_imagetexture_tables.mel
   mel/x3d_indexedfaceset_tables.mel
   mel/x3d_inline_tables.mel
   mel/x3d_integersequencer_tables.mel
   mel/x3d_integertrigger_tables.mel
   mel/x3d_keysensor_tables.mel
   mel/x3d_loadsensor_tables.mel
   mel/x3d_lod_tables.mel
   mel/x3d_material_tables.mel
   mel/x3d_metadatadouble_tables.mel
   mel/x3d_metadatafloat_tables.mel
   mel/x3d_metadatainteger_tables.mel
   mel/x3d_metadataset_tables.mel
   mel/x3d_metadatastring_tables.mel
   mel/x3d_movietexture_tables.mel
   mel/x3d_multitexturecoordinate_tables.mel
   mel/x3d_multitexturetransform_tables.mel
   mel/x3d_multitexture_tables.mel
   mel/x3d_navigationinfo_tables.mel
   mel/x3d_node_creation_procs.mel
   mel/x3d_normalinterpolator_tables.mel
   mel/x3d_normal_tables.mel
   mel/x3d_orientationinterpolator_tables.mel
   mel/x3d_pixeltexture_tables.mel
   mel/x3d_planesensor_tables.mel
   mel/x3d_pointlight_tables.mel
   mel/x3d_positioninterpolator_tables.mel
   mel/x3d_proximitysensor_tables.mel
   mel/x3d_rigidbodycollection_tables.mel
   mel/x3d_rigidbody_tables.mel
   mel/x3d_routing_scripts.mel
   mel/x3d_scalarinterpolator_tables.mel
   mel/x3d_scenegraph_ui_tree.mel
   mel/x3d_script_tables.mel
   mel/x3d_shape_tables.mel
   mel/x3d_sound_tables.mel
   mel/x3d_spheresensor_tables.mel
   mel/x3d_sphere_tables.mel
   mel/x3d_spotlight_tables.mel
   mel/x3d_stringsensor_tables.mel
   mel/x3d_switch_tables.mel
   mel/x3d_texturecoordinate_tables.mel
   mel/x3d_texturetransform_tables.mel
   mel/x3d_timesensor_tables.mel
   mel/x3d_timetrigger_tables.mel
   mel/x3d_touchsensor_tables.mel
   mel/x3d_transform_tables.mel
   mel/x3d_viewpoint_tables.mel
   mel/x3d_visibilitysensor_tables.mel
   mel/x3d_worldinfo_tables.mel
)

#set resource file list
set(RESOURCES_FILES 
   icons/audioclip.bmp
   icons/lodGroup.bmp
   icons/x3dAnchor.bmp
   icons/x3dBillboard.bmp
   icons/x3dBooleanFilter.bmp
   icons/x3dBooleanSequencer.bmp
   icons/x3dBooleanToggle.bmp
   icons/x3dBooleanTrigger.bmp
   icons/x3dBox.bmp
   icons/x3dCollision.bmp
   icons/x3dColor.bmp
   icons/x3dColorInterpolator.bmp
   icons/x3dColorRGBA.bmp
   icons/x3dCone.bmp
   icons/x3dCoordinate.bmp
   icons/x3dCoordinateInterpolator.bmp
   icons/x3dCylinder.bmp
   icons/x3dCylinderSensor.bmp
   icons/x3dGamepadSensor.bmp
   icons/x3dGroup.bmp
   icons/x3dIndexedFaceSet.bmp
   icons/x3dInline.bmp
   icons/x3dIntegerSequencer.bmp
   icons/x3dIntegerTrigger.bmp
   icons/x3dKeySensor.bmp
   icons/x3dLoadSensor.bmp
   icons/x3dMetadataDouble.bmp
   icons/x3dMetadataFloat.bmp
   icons/x3dMetadataInteger.bmp
   icons/x3dMetadataSet.bmp
   icons/x3dMetadataString.bmp
   icons/x3dNavigationInfo.bmp
   icons/x3dNormal.bmp
   icons/x3dNormalInterpolator.bmp
   icons/x3dOrientationInterpolator.bmp
   icons/x3dPlaneSensor.bmp
   icons/x3dPositionInterpolator.bmp
   icons/x3dProximitySensor.bmp
   icons/x3dRoute.bmp
   icons/x3dScalarInterpolator.bmp
   icons/x3dScript.bmp
   icons/x3dSound.bmp
   icons/x3dSphere.bmp
   icons/x3dSphereSensor.bmp
   icons/x3dStringSensor.bmp
   icons/x3dSwitch.bmp
   icons/x3dTextureCoordinate.bmp
   icons/x3dTimesensor.bmp
   icons/x3dTimeTrigger.bmp
   icons/x3dTouchsensor.bmp
   icons/x3dViewpoint.bmp
   icons/x3dVisibilitySensor.bmp
   icons/x3dWorldInfo.bmp
   icons/x3d_dirLight.bmp
   icons/x3d_pointLight.bmp
   icons/x3d_spotLight.bmp
   icons/x3d_trans.bmp
)


# set SOURCE_FILES
set(SOURCE_FILES
   rawkee/impl.h
   rawkee/sax3dWriter.h
   rawkee/vrml97FileTranslator.h
   rawkee/web3dExportMethods.h
   rawkee/web3dFileTranslator.h
   rawkee/webX3DExporter.h
   rawkee/x3dAnchor.h
   rawkee/x3dbFileTranslator.h
   rawkee/x3dBillboard.h
   rawkee/x3dBooleanFilter.h
   rawkee/x3dBooleanSequencer.h
   rawkee/x3dBooleanToggle.h
   rawkee/x3dBooleanTrigger.h
   rawkee/x3dBox.h
   rawkee/x3dCollision.h
   rawkee/x3dColor.h
   rawkee/x3dColorInterpolator.h
   rawkee/x3dColorRGBA.h
   rawkee/x3dCone.h
   rawkee/x3dCoordinate.h
   rawkee/x3dCoordinateInterpolator.h
   rawkee/x3dCylinder.h
   rawkee/x3dCylinderSensor.h
   rawkee/x3dExportOrganizer.h
   rawkee/x3dFileTranslator.h
   rawkee/x3dGamepadSensor.h
   rawkee/x3dGroup.h
   rawkee/x3dIndexedFaceSet.h
   rawkee/x3dInline.h
   rawkee/x3dIntegerSequencer.h
   rawkee/x3dIntegerTrigger.h
   rawkee/x3dKeySensor.h
   rawkee/x3dLoadSensor.h
   rawkee/x3dMetadataDouble.h
   rawkee/x3dMetadataFloat.h
   rawkee/x3dMetadataInteger.h
   rawkee/x3dMetadataSet.h
   rawkee/x3dMetadataString.h
   rawkee/x3dNavigationInfo.h
   rawkee/x3dNormal.h
   rawkee/x3dNormalInterpolator.h
   rawkee/x3dOrientationInterpolator.h
   rawkee/x3dPlaneSensor.h
   rawkee/x3dPositionInterpolator.h
   rawkee/x3dProximitySensor.h
   rawkee/x3dProximitySensorManip.h
   rawkee/x3dRoute.h
   rawkee/x3dScalarInterpolator.h
   rawkee/x3dScript.h
   rawkee/x3dSound.h
   rawkee/x3dSphere.h
   rawkee/x3dSphereSensor.h
   rawkee/x3dStringSensor.h
   rawkee/x3dSwitch.h
   rawkee/x3dTextureCoordinate.h
   rawkee/x3dTimeSensor.h
   rawkee/x3dTimeTrigger.h
   rawkee/x3dTouchSensor.h
   rawkee/x3dvFileTranslator.h
   rawkee/x3dVisibilitySensor.h
   rawkee/x3dWorldInfo.h

   cxx/sax3dWriter.cpp
   cxx/vrml97FileTranslator.cpp
   cxx/web3dExportMethods.cpp
   cxx/web3dFileTranslator.cpp
   cxx/webX3DExporter.cpp
   cxx/x3dAnchor.cpp
   cxx/x3dbFileTranslator.cpp
   cxx/x3dBillboard.cpp
   cxx/x3dBooleanFilter.cpp
   cxx/x3dBooleanSequencer.cpp
   cxx/x3dBooleanToggle.cpp
   cxx/x3dBooleanTrigger.cpp
   cxx/x3dBox.cpp
   cxx/x3dCollision.cpp
   cxx/x3dColor.cpp
   cxx/x3dColorInterpolator.cpp
   cxx/x3dColorRGBA.cpp
   cxx/x3dCone.cpp
   cxx/x3dCoordinate.cpp
   cxx/x3dCoordinateInterpolator.cpp
   cxx/x3dCylinder.cpp
   cxx/x3dCylinderSensor.cpp
   cxx/x3dExportOrganizer.cpp
   cxx/x3dFileTranslator.cpp
   cxx/x3dGamepadSensor.cpp
   cxx/x3dGroup.cpp
   cxx/x3dIndexedFaceSet.cpp
   cxx/x3dInline.cpp
   cxx/x3dIntegerSequencer.cpp
   cxx/x3dIntegerTrigger.cpp
   cxx/x3dKeySensor.cpp
   cxx/x3dLoadSensor.cpp
   cxx/x3dMetadataDouble.cpp
   cxx/x3dMetadataFloat.cpp
   cxx/x3dMetadataInteger.cpp
   cxx/x3dMetadataSet.cpp
   cxx/x3dMetadataString.cpp
   cxx/x3dNavigationInfo.cpp
   cxx/x3dNormal.cpp
   cxx/x3dNormalInterpolator.cpp
   cxx/x3dOrientationInterpolator.cpp
   cxx/x3dPlaneSensor.cpp
   cxx/x3dPositionInterpolator.cpp
   cxx/x3dProximitySensor.cpp
   cxx/x3dProximitySensorManip.cpp
   cxx/x3dRoute.cpp
   cxx/x3dScalarInterpolator.cpp
   cxx/x3dScript.cpp
   cxx/x3dSound.cpp
   cxx/x3dSphere.cpp
   cxx/x3dSphereSensor.cpp
   cxx/x3dStringSensor.cpp
   cxx/x3dSwitch.cpp
   cxx/x3dTextureCoordinate.cpp
   cxx/x3dTimeSensor.cpp
   cxx/x3dTimeTrigger.cpp
   cxx/x3dTouchSensor.cpp
   cxx/x3dvFileTranslator.cpp
   cxx/x3dVisibilitySensor.cpp
   cxx/x3dWorldInfo.cpp
   ${RESOURCES_FILES}
)

# set linking libraries
set(LIBRARIES
     Foundation
     OpenMaya
     OpenMayaUI
     OpenMayaAnim
     OpenMayaFX
     OpenMayaRender
     Image
)


#find opengl
find_opengl()


# Build plugin
build_plugin()

