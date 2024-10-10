#ifndef __WEB3DEXPORTMETHODS_H
#define __WEB3DEXPORTMETHODS_H

//
// Copyright (C) 2004, 2005 North Dakota State University (http://atl.ndsu.edu/resources/maya_x3d.php) 
// 
//This library is free software; you can redistribute it and/or 
//modify it under the terms of the GNU Lesser General Public License 
//as published by the Free Software Foundation; either version 2.1 of 
//the License, or (at your option) any later version.

//This library is distributed in the hope that it will be useful, but 
//WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY 
//or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public 
//License for more details.

//You should have received a copy of the GNU Lesser General Public License 
//along with this library; if not, write to the Free Software Foundation, Inc., 
//59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

// File: web3dExportMethods.h
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/x3dBox.h>
#include <rawkee/x3dColor.h>
#include <rawkee/x3dColorRGBA.h>
#include <rawkee/x3dCone.h>
#include <rawkee/x3dCoordinate.h>
#include <rawkee/x3dCylinder.h>
#include <rawkee/x3dIndexedFaceSet.h>
#include <rawkee/x3dMetadataDouble.h>
#include <rawkee/x3dMetadataFloat.h>
#include <rawkee/x3dMetadataInteger.h>
#include <rawkee/x3dMetadataSet.h>
#include <rawkee/x3dMetadataString.h>
#include <rawkee/x3dNavigationInfo.h>
#include <rawkee/x3dNormal.h>
#include <rawkee/x3dNormal.h>
#include <rawkee/x3dRoute.h>
#include <rawkee/x3dScript.h>
#include <rawkee/x3dSound.h>
#include <rawkee/x3dSphere.h>
#include <rawkee/x3dTextureCoordinate.h>
#include <rawkee/x3dTimeSensor.h>
#include <rawkee/x3dTouchSensor.h>
#include <rawkee/x3dWorldInfo.h>

#include <rawkee/x3dColorInterpolator.h>
#include <rawkee/x3dCoordinateInterpolator.h>
#include <rawkee/x3dNormalInterpolator.h>
#include <rawkee/x3dOrientationInterpolator.h>
#include <rawkee/x3dPositionInterpolator.h>
#include <rawkee/x3dScalarInterpolator.h>

#include <rawkee/x3dBooleanSequencer.h>
#include <rawkee/x3dIntegerSequencer.h>

#include <rawkee/x3dKeySensor.h>
#include <rawkee/x3dLoadSensor.h>
#include <rawkee/x3dStringSensor.h>

#include <rawkee/x3dCylinderSensor.h>
#include <rawkee/x3dPlaneSensor.h>
#include <rawkee/x3dSphereSensor.h>

#include <rawkee/x3dGamepadSensor.h>
#include <rawkee/x3dProximitySensor.h>
#include <rawkee/x3dProximitySensorManip.h>
#include <rawkee/x3dVisibilitySensor.h>

#include <rawkee/x3dBooleanFilter.h>
#include <rawkee/x3dBooleanToggle.h>
#include <rawkee/x3dBooleanTrigger.h>

#include <rawkee/x3dIntegerTrigger.h>

#include <rawkee/x3dTimeTrigger.h>

#include <rawkee/x3dAnchor.h>
#include <rawkee/x3dBillboard.h>
#include <rawkee/x3dCollision.h>
#include <rawkee/x3dGroup.h>
#include <rawkee/x3dInline.h>
#include <rawkee/x3dSwitch.h>

//*****************************************
//*****************************************

#define X3D_TRANS "transform"
#define X3D_AUDIOCLIP "audio"
#define X3D_SOUND "x3dSound"
#define X3D_TEXTTRANS "place2dTexture"
#define X3D_MESH "mesh"

#define X3D_PROXSENSOR "x3dProximitySensor"
#define X3D_VISSENSOR "x3dVisbilitySensor"
#define X3D_LOADSENSOR "x3dLoadSensor"
#define X3D_KEYSENSOR "x3dKeySensor"
#define X3D_STRINGSENSOR "x3dStringSensor"
#define X3D_CYLSENSOR "x3dCylinderSensor"
#define X3D_PLANESENSOR "x3dPlaneSensor"
#define X3D_SPHERESENSOR "x3dSphereSensor"
#define X3D_TIMESENSOR "x3dTimeSensor"
#define X3D_TOUCHSENSOR "x3dTouchSensor"

#define X3D_BOOLTRIGGER "x3dBooleanTrigger"
#define X3D_BOOLFILTER "x3dBooleanFilter"
#define X3D_BOOLTOGGLE "x3dBooleanToggle"
#define X3D_INTTRIGGER "x3dIntegerTrigger"
#define X3D_TIMETRIGGER "x3dTimeTrigger"

#define X3D_NAVIGATION "x3dNavigationInfo"
#define X3D_WORLDINFO "x3dWorldInfo"

#define X3D_POSINTER "x3dPositionInterpolator"
#define X3D_ORIINTER "x3dOrientationInterpolator"
#define X3D_COORDINTER "x3dCoordinateInterpolator"
#define X3D_NORMINTER "x3dNormalInterpolator"
#define X3D_COLORINTER "x3dColorInterpolator"
#define X3D_SCALINTER "x3dScalarInterpolator"

#define X3D_BOOLSEQ "x3dBooleanSequencer"
#define X3D_INTSEQ "x3dIntegerSequencer"

#define X3D_SCRIPT "x3dScript"

#define X3D_ANCHOR "x3dAnchor"
#define X3D_GROUP "x3dGroup"
#define X3D_SWITCH "x3dSwitch"
#define X3D_COLLISION "x3dCollision"
#define X3D_LOD "lodGroup"
#define X3D_INLINE "x3dInline"
#define X3D_BILLBOARD "x3dBillboard"

#define X3D_IFS "x3dIndexedFaceSet"
#define X3D_COL "x3dColor"
#define X3D_COLRGBA "x3dColorRGBA"
#define X3D_NORMAL "x3dNormal"
#define X3D_TEXCOORD "x3dTextureCoordinate"
#define X3D_COORD "x3dCoordinate"

#define X3D_BOX "x3dBox"
#define X3D_SPHERE "x3dSphere"
#define X3D_CONE "x3dCone"
#define X3D_CYL "x3dCylinder"

#define X3D_VIEW "camera"
#define X3D_DIRLIGHT "directionalLight"
#define X3D_SPOTLIGHT "spotLight"
#define X3D_POINTLIGHT "pointLight"

#define X3D_AMBLIGHT "ambientLight"
#define X3D_AREALIGHT "areaLight"
#define X3D_VOLLIGHT "volumeLight"

#define X3D_HANIMJOINT "joint"
#define X3D_GAMEPADSENSOR "x3dGamepadSensor"

#define X3DMETAD 0
#define X3DMETAF 1
#define X3DMETAI 2
#define X3DMETASE 3
#define X3DMETAST 4
//#define PI 3.141593

#define X3DENC 0
#define X3DVENC 1
#define VRML97ENC 2
#define X3DBENC 3

class web3dExportMethods
{
public:
			web3dExportMethods();
	virtual	~web3dExportMethods();

	MStringArray	getX3DFields(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getX3DFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getX3DCollidableShapeValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getX3DFields(MString nodeName, unsigned int subNode);
	MStringArray	getX3DFieldValues(MString nodeName, unsigned int subNode);

	MObject		getMyDepNodeObj(MString nodeName);
//	MFnDependencyNode	getMyDepNode(MString nodeName);
//	MFnDependencyNode	findNonExportTexture(MString nodeName);
	MObject		findNonExportTexture(MString nodeName);


	MStringArray	getMaterialFields();
	MStringArray	getMaterialFieldValues(MFnDependencyNode &depNode, unsigned int subNode);

	MStringArray	getRBCFields();
	MStringArray	getRBCFieldValues(MFnDependencyNode &depNode, unsigned int subNode);

	MStringArray	getRigidBodyFields();
	MStringArray	getRigidBodyFieldValues(MFnDagNode &dagNode, MFnDagNode &parent);

	MStringArray	getCollisionCollectionFields();
	MStringArray	getCollisionCollectionFieldValues(MFnDependencyNode &depNode);

	MStringArray	getCollisionSpaceFields();
	MStringArray	getCollisionSpaceFieldValues(MFnDependencyNode &depNode);

	MStringArray	getCollisionSensorFields();
	MStringArray	getCollisionSensorFieldValues(MFnDependencyNode &depNode);

	MStringArray	getHAnimHumanoidFields();
	MStringArray	getHAnimHumanoidFieldValues(MFnDagNode &dagNode, unsigned int subNode);

	MStringArray	getIFSFields();
	MStringArray	getIFSFieldValues(MDagPath dagpath, unsigned int subNode);
	MStringArray	getHAnimIFSFieldValues(MDagPath dagpath, unsigned int subNode, MStringArray sca, MFloatVectorArray cna, bool istb);

	MStringArray	getCoord_Fields();
	MStringArray	getCoord_FieldValues(MDagPath dagpath, unsigned int subNode);

	MStringArray	getNormal_Fields();
	MStringArray	getNormal_FieldValues(MDagPath dagpath, unsigned int subNode);

	MStringArray	getColorFields();
	MStringArray	CRGBA_Fields();

	MStringArray	getColorFieldValues(MDagPath dagpath, unsigned int subNode);
	MStringArray	CRGBA_FieldValues(MDagPath dagpath, unsigned int subNode);

	MStringArray	getTextCoordFields();
	MStringArray	getTextCoordFieldValues(MDagPath dagpath, MString usedUVSet, bool isMulti, unsigned int subNode);

	MString			getSFVec2f(MString sValue, MFnDependencyNode &depNode);
	MString			getSFVec2d(MString sValue, MFnDependencyNode &depNode);
	MString			getMFVec2f(MString sValue, MFnDependencyNode &depNode);
	MString			getMFVec2d(MString sValue, MFnDependencyNode &depNode);

	MString			getSFVec3f(MString sValue, MFnDependencyNode &depNode);
	MString			getSFVec3fWorld(MString sValue, MFnDependencyNode &depNode);
	MString			getSFVec3fHAnim(MString sValue, MFnDependencyNode &depNode, double pVal[]);
	MString			getSFVec3d(MString sValue, MFnDependencyNode &depNode);
	MString			getMFVec3f(MString sValue, MFnDependencyNode &depNode);
	MString			getMFVec3fNonScript(MString sValue, MFnDependencyNode &depNode);
	MString			getMFVec3d(MString sValue, MFnDependencyNode &depNode);

	MString			getMultipleMFVec3f(MString sValue, MFnDependencyNode &depNode);
	MString			getSFColor(MString sValue, MFnDependencyNode &depNode);
	MString			getMFColor(MString sValue, MFnDependencyNode &depNode);
	MString			getMFColorNonScript(MString sValue, MFnDependencyNode &depNode);

	MString			getSFColorRGBA(MString sValue, MFnDependencyNode &depNode);
	MString			getMFColorRGBA(MString sValue, MFnDependencyNode &depNode);
	MString			getSFRotation(MString sValue, MFnDependencyNode &depNode);
	MString			getSFRotationWorld(MString sValue, MFnDependencyNode &depNode);
	MString			getSFRotationHAnim(MString sValue, MFnDependencyNode &depNode);
//	MString			getSFRotation(MString sValue, MFnDependencyNode &depNode, bool isLight);
	MString			getMFRotation(MString sValue, MFnDependencyNode &depNode);
	MString			getMFRotationNonScript(MString sValue, MFnDependencyNode &depNode);
	MString			getSFFloat(MString sValue, MFnDependencyNode &depNode);
	MString			getMFFloat(MString sValue, MFnDependencyNode &depNode);
	MString			getMFFloatNonScript(MString sValue, MFnDependencyNode &depNode);
	MString			getMFFloatMetadata(MString sValue, MFnDependencyNode &depNode);
	MString			getSFDouble(MString sValue, MFnDependencyNode &depNode);
	MString			getMFDouble(MString sValue, MFnDependencyNode &depNode);
	MString			getMFDoubleNonScript(MString sValue, MFnDependencyNode &depNode);
	MString			getSFFloatFromSFVec3f(MString sValue, MFnDependencyNode &depNode);
	MString			getSFImage(MString sValue, MFnDependencyNode &depNode);
	MString			getMFImage(MString sValue, MFnDependencyNode &depNode);
	MString			getSFString(MString sValue, MFnDependencyNode &depNode);
	MString			getMFString(MString sValue, MFnDependencyNode &depNode);
	MString			getMFStringNonScript(MString sValue, MFnDependencyNode &depNode);
	MString			getSFBool(MString sValue, MFnDependencyNode &depNode);
	MString			getMFBool(MString sValue, MFnDependencyNode &depNode);
	MString			getMFBoolNonScript(MString sValue, MFnDependencyNode &depNode);
	MString			getSFInt32(MString sValue, MFnDependencyNode &depNode);
	MString			getMFInt32(MString sValue, MFnDependencyNode &depNode);
	MString			getMFInt32NonScript(MString sValue, MFnDependencyNode &depNode);
	MString			getMFInt32Metadata(MString sValue, MFnDependencyNode &depNode);
	MString			getSFTime(MString sValue, MFnDependencyNode &depNode);
	MString			getMFTime(MString sValue, MFnDependencyNode &depNode);

	MString			getFieldOfView(MFnDependencyNode &depNode);
	MString			getLODRanges(MFnDependencyNode &depNode);
	MString			getAudioURLs(MFnDependencyNode &depNode);
	MString			getInlineURLs(MFnDependencyNode &depNode);
	MString			getImageURLs(MFnDependencyNode &depNode, unsigned int msType);

	MString			getLightIntensity(MString sValue, MFnDependencyNode &depNode);
	MString			getLightAttenuation(MFnDependencyNode &depNode);
	MString			getDirection(MString sValue, MFnDependencyNode &depNode);
	MString			getDirection(MFnDependencyNode &depNode);
	MString			getParentSFVec3f(MString sValue, MFnDependencyNode &depNode);
	MString			getParentSFRotation(MString sValue, MFnDependencyNode &depNode);
	MString			getLightRadius(MFnDependencyNode &depNode);
	MString			getRadianAngle(MString sValue, MFnDependencyNode &depNode);

//	MStringArray	getUsedUVSetsInOrder(MFnMesh mesh, bool & hasT, MStringArray uvSetNames, unsigned int val);
	MStringArray	getUsedUVSetsInOrder(MObject mObj, bool & hasT, MStringArray uvSetNames, unsigned int val);
//	MStringArray	getShaderTexturesInOrder(MFnMesh mesh, unsigned int val);
	MStringArray	getShaderTexturesInOrder(MObject mObj, unsigned int val);
	MString			compileTextureCoordinates(MDagPath dagpath, MString usedUVSet, unsigned int sn, bool hasMulti);

	MString			postProcessIndices(MIntArray bIndex);
	MString			postProcessPointArray(MPointArray pArray, unsigned int vl);
	MString			postProcessFloatPointArray(MFloatPointArray pArray, unsigned int vl);
	MString			postProcessVectorArray(MFloatVectorArray vArray);
	MString			postProcessColorArray(MColorArray cArray, bool hasAlpha);

	bool			findBumpMap(MPlug mBump, MStringArray & tArray, MStringArray & mArray);
	bool			findColorMap(MPlug mColor, MStringArray & tArray, MStringArray & mArray, bool hasAnother);
	bool			findSpecularMap(MPlug mSpecular, MStringArray & tArray, MStringArray & mArray);
	void			setGlobalCPV(bool value);
	void			setGlobalNPV(bool value);
	void			setGlobalSolid(bool value);
	void			setGlobalCA(float value);
	void			setExportEncoding(int value);
	void			setAudioDir(MString aDir);
	void			setImageDir(MString iDir);
	void			setInlineDir(MString inDir);
	void			setBaseUrl(MString bUrl);
	void			setTF(MString extension);
//	void			setAdjTexture(bool at);
	void			setTW(int twVal);
	void			setTH(int thVal);
	void			setConsolidate(bool conVal);
	void			setUseRelURL(bool value);
	bool			getUseRelURL();
	void			setUseRelURLW(bool value);
	bool			getUseRelURLW();
	MString			specCharProcessor(MString pString);

	MStringArray	getFieldNamesTexture(MFnDependencyNode &depNode, MString textureType);
	MStringArray	getFieldValuesTexture(MFnDependencyNode &depNode, MString textureType);
	MString		extractPixelValues(MFnDependencyNode &depNode);

	MStringArray	getTransFields();
	MStringArray	getTransFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	int			getPixelLength(MFnDependencyNode &depNode);
	MImage		getImageObject(MFnDependencyNode &depNode);

	MStringArray	getJointFields();
	MStringArray	getSiteFields();
//	MStringArray	getJointFieldValues(MFnDependencyNode &depNode, unsigned int subNode, MString humanName, double pVal[]);
//	MStringArray	getJointFieldValues(MFnIkJoint ikjNode, unsigned int subNode, MString humanName, double pVal[]);
	MStringArray	getJointFieldValues(MObject mObj, unsigned int subNode, MString humanName, double pVal[]);
	MStringArray	getSiteFieldValues(MFnDependencyNode &depNode, unsigned int subNode, MString humanName, double pVal[], bool nsHAnim);
	
//	static			MFloatArray uCoord;
//	static			MFloatArray vCoord;

	MStringArray	getScriptCustomFieldNames(MFnDagNode &sNode);
	MStringArray	getScriptCustomFieldTypes(MFnDagNode &sNode);
	MStringArray	getScriptCustomFieldAccess(MFnDagNode &sNode);
	MString		getScriptCustomValue(MFnDagNode &sNode, unsigned int index);
	MObjectArray	getScriptNodeObjects(MFnDagNode &sNode, unsigned int index);
	MStringArray	getScriptRemoteURLs(MFnDependencyNode &aDag);
	MStringArray	getScriptLocalURLs(MFnDependencyNode &aDag);
	MString		replaceNewLines(MString cString);
	MFloatVectorArray	getComparedFloatVectorArray(MFloatVectorArray normalValues);

protected:

	static bool		globalCPV;
	static bool		globalNPV;
	static bool		globalSolid;
	static float	globalCA;
	static int		exEncoding;
	static MString	audioDir;
	static MString	imageDir;
	static MString	inlineDir;
	static MString	baseUrl;
	static MString	exTextureFormat;
	static bool adjTexture;
	static int x3dTextureWidth;
	static int x3dTextureHeight;
	static bool conMedia;
	static bool useRelURL;
	static bool useRelURLW;

	MStringArray	getTextureTransformFields();
	MStringArray	getAnchorFields();
//	MStringArray	getShapeFields(MFnDependencyNode depNode, unsigned int subNode);
	MStringArray	getShapeFields();
//	MStringArray	getProxFields(MFnDependencyNode depNode, unsigned int subNode);
	MStringArray	getProxFields();
//	MStringArray	getVisFields(MFnDependencyNode depNode, unsigned int subNode);
	MStringArray	getVisFields();
//	MStringArray	getTiSFields(MFnDependencyNode depNode, unsigned int subNode);
	MStringArray	getTiSFields();
//	MStringArray	getToSFields(MFnDependencyNode depNode, unsigned int subNode);
	MStringArray	getToSFields();
//	MStringArray	getGamepadSFields(MFnDependencyNode depNode, unsigned int subNode);
	MStringArray	getGamepadSFields();
	MStringArray	getPlaneSensorFields();
	MStringArray	getSphereSensorFields();
	MStringArray	getCylSensorFields();
	MStringArray	getKeySensorFields();
	MStringArray	getLoadSensorFields();
	MStringArray	getStringSensorFields();

	MStringArray	getNIFields();
	MStringArray	getWIFields();

	MStringArray	getPIFields();
	MStringArray	getOIFields();
	MStringArray	getColorIFields();
	MStringArray	getScalarIFields();
	MStringArray	getCoordIFields();
	MStringArray	getNormalIFields();
	MStringArray	getBoolSFields();
	MStringArray	getIntSFields();
	MStringArray	getBoolToggleFields();
	MStringArray	getIntTriggerFields();

	MStringArray	getScriptFields();
	MStringArray	getGroupFields();
	MStringArray	getBillboardFields();
	MStringArray	getSwitchFields();
	MStringArray	getCollisionFields();
	MStringArray	getLODFields();

	MStringArray	getBoxFields();
	MStringArray	getSphereFields();
	MStringArray	getConeFields();
	MStringArray	getCylinderFields();
	MStringArray	getViewpointFields();
	MStringArray	getDirLightFields();
	MStringArray	getSpotLightFields();
	MStringArray	getPointLightFields();

	MStringArray	getAnchorFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getTextureTransformFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getShapeFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getProxFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getVisFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getTiSFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getToSFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getGamepadSFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getCylSensorFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getPlaneSensorFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getSphereSensorFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getKeySensorFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getLoadSensorFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getStringSensorFieldValues(MFnDependencyNode &depNode, unsigned int subNode);

	MStringArray	getNIFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getWIFieldValues(MFnDependencyNode &depNode, unsigned int subNode);

	MStringArray	getPIFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getOIFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getColorIFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getCoordIFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getNormalIFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getScalarIFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getBoolSFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getIntSFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getBoolToggleFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getIntTriggerFieldValues(MFnDependencyNode &depNode, unsigned int subNode);

	MStringArray	getScriptFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getGroupFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getBillboardFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getSwitchFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getCollisionFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getLODFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
//	MStringArray	getAudioClipFields(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getAudioClipFields();
	MStringArray	getAudioClipFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
//	MStringArray	getSoundFields(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getSoundFields();
	MStringArray	getSoundFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getInlineFields();
	MStringArray	getInlineFieldValues(MFnDependencyNode &depNode, unsigned int subNode);

	MStringArray	getBoxFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getSphereFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getConeFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getCylinderFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getViewpointFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getDirLightFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getSpotLightFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getPointLightFieldValues(MFnDependencyNode &depNode, unsigned int subNode);
	MStringArray	getAPointLightFieldValues(MFnDependencyNode &depNode, unsigned int subNode);

	void			setDiffuseColor(MPlug mColor, MPlug mDiffuse, MStringArray & tArray);
	void			setAmbientIntensity(MPlug mAmbient, MStringArray & tArray);
	void			setEmissiveColor(MPlug mEmissive, MStringArray & tArray);
	void			setShininess(MFnDependencyNode &depFn, MPlugArray mShininess, MStringArray & tArray);
	void			setSpecularColor(MPlug mSpecular, MStringArray & tArray);
	void			setTransparency(MPlug mTransparency, MStringArray & tArray);

	MString			getCCW(MDagPath dagpath, unsigned int sn);
	MString			getColorIndex(MDagPath dagpath, unsigned int sn);
	MString			getColorPerVertex(MDagPath dagpath, unsigned int sn);
	MString			getConvex(MDagPath dagpath, unsigned int sn);
	MString			getCoordIndex(MDagPath dagpath, unsigned int sn);
	MString			getHAnimCoordIndex(MDagPath dagpath, unsigned int sn, MStringArray sca);
	MString			getCreaseAngle(MDagPath dagpath, unsigned int sn);
	MString			getNormalIndex(MDagPath dagpath, unsigned int sn);
	MString			getHAnimNormalIndex(MDagPath dagpath, unsigned int sn, MFloatVectorArray cna);
	MString			getNormalPerVertex(MDagPath dagpath, unsigned int sn);
	MString			getSolid(MDagPath dagpath, unsigned int sn);
	MString			getTexCoordIndex(MDagPath dagpath, unsigned int sn);

	MString			computeColorI(MDagPath dagpath, unsigned int sn);
	MString			computeNI(MDagPath dagpath, unsigned int sn);
	MString			computeHAnimNI(MDagPath dagpath, unsigned int sn, MFloatVectorArray cna);
	MString			computeCoordI(MDagPath dagpath, unsigned int sn);
	MString			computeHAnimCoordI(MDagPath dagpath, unsigned int sn, MStringArray sca);
	MString			computeTexCoordI(MDagPath dagpath, MStringArray usedMaps, unsigned int sn, bool isMulti);
	void			getLostUV(float & lostU, float & lostV, MFloatArray uCoord, MFloatArray vCoord);
	void			getExtremes(float & minU, float & maxU, float & minV, float & maxV, MFloatArray uCoord, MFloatArray vCoord);

	MString			assignMode(int value);
};

#endif
