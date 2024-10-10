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

// File: web3dExportMethods.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

web3dExportMethods::web3dExportMethods()
{

}

web3dExportMethods::~web3dExportMethods()
{

}

bool web3dExportMethods::globalCPV = true;
bool web3dExportMethods::globalNPV = true;
bool web3dExportMethods::globalSolid = true;
bool web3dExportMethods::useRelURL = true;
bool web3dExportMethods::useRelURLW = true;
float web3dExportMethods::globalCA = 0.0f;
int	web3dExportMethods::exEncoding = X3DENC;

MString web3dExportMethods::audioDir;
MString web3dExportMethods::inlineDir;
MString web3dExportMethods::imageDir;
MString web3dExportMethods::baseUrl;
MString web3dExportMethods::exTextureFormat;
//bool web3dExportMethods::adjTexture;
int web3dExportMethods::x3dTextureWidth;
int web3dExportMethods::x3dTextureHeight;
bool web3dExportMethods::conMedia;

//MFloatArray	web3dExportMethods::uCoord;
//MFloatArray	web3dExportMethods::vCoord;

MStringArray web3dExportMethods::getX3DFields(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray newArray;
	if(depNode.typeName().operator ==(X3D_TRANS))
	{
		newArray = getTransFields();
	}
	if(depNode.typeName().operator ==(X3D_ANCHOR))
	{
		newArray = getAnchorFields();
	}
	if(depNode.typeName().operator ==(X3D_AUDIOCLIP))
	{
		newArray = getAudioClipFields();							//(depNode, subNode);
	}
	if(depNode.typeName().operator ==(X3D_SOUND))
	{
		newArray = getSoundFields();								//(depNode, subNode);
	}
	if(depNode.typeName().operator ==(X3D_TEXTTRANS))
	{
		newArray = getTextureTransformFields();
	}
	else if(depNode.typeName().operator ==(X3D_MESH))
	{
		newArray = getShapeFields();								//(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_PROXSENSOR))
	{
		newArray = getProxFields();								//(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_VISSENSOR))
	{
		newArray = getVisFields();								//(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_TIMESENSOR))
	{
		newArray = getTiSFields();								//(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_TOUCHSENSOR))
	{
		newArray = getToSFields();								//(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_GAMEPADSENSOR))
	{
		newArray = getGamepadSFields();							//(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_CYLSENSOR))
	{
		newArray = getCylSensorFields();
	}
	else if(depNode.typeName().operator ==(X3D_PLANESENSOR))
	{
		newArray = getPlaneSensorFields();
	}
	else if(depNode.typeName().operator ==(X3D_SPHERESENSOR))
	{
		newArray = getSphereSensorFields();
	}
	else if(depNode.typeName().operator ==(X3D_LOADSENSOR))
	{
		newArray = getLoadSensorFields();
	}
	else if(depNode.typeName().operator ==(X3D_KEYSENSOR))
	{
		newArray = getKeySensorFields();
	}
	else if(depNode.typeName().operator ==(X3D_STRINGSENSOR))
	{
		newArray = getStringSensorFields();
	}
	else if(depNode.typeName().operator ==(X3D_NAVIGATION))
	{
		newArray = getNIFields();
	}
	else if(depNode.typeName().operator ==(X3D_WORLDINFO))
	{
		newArray = getWIFields();
	}
	else if(depNode.typeName().operator ==(X3D_POSINTER))
	{
		newArray = getPIFields();
	}
	else if(depNode.typeName().operator ==(X3D_ORIINTER))
	{
		newArray = getOIFields();
	}
	else if(depNode.typeName().operator ==(X3D_COLORINTER))
	{
		newArray = getColorIFields();
	}
	else if(depNode.typeName().operator ==(X3D_SCALINTER))
	{
		newArray = getScalarIFields();
	}
	else if(depNode.typeName().operator ==(X3D_COORDINTER))
	{
		newArray = getCoordIFields();
	}
	else if(depNode.typeName().operator ==(X3D_NORMINTER))
	{
		newArray = getNormalIFields();
	}
	else if(depNode.typeName().operator ==(X3D_BOOLSEQ))
	{
		newArray = getBoolSFields();
	}
	else if(depNode.typeName().operator ==(X3D_INTSEQ))
	{
		newArray = getIntSFields();
	}
	else if(depNode.typeName().operator ==(X3D_BOOLFILTER))
	{
		MStringArray empty;
		newArray = empty;
	}
	else if(depNode.typeName().operator ==(X3D_BOOLTOGGLE))
	{
		newArray = getBoolToggleFields();
	}
	else if(depNode.typeName().operator ==(X3D_BOOLTRIGGER))
	{
		MStringArray empty;
		newArray = empty;
	}
	else if(depNode.typeName().operator ==(X3D_TIMETRIGGER))
	{
		MStringArray empty;
		newArray = empty;
	}
	else if(depNode.typeName().operator ==(X3D_INTTRIGGER))
	{
		newArray = getIntTriggerFields();
	}
	else if(depNode.typeName().operator ==(X3D_SCRIPT))
	{
		newArray = getScriptFields();
	}
	else if(depNode.typeName().operator ==(X3D_GROUP))
	{
		newArray = getGroupFields();
	}
	else if(depNode.typeName().operator ==(X3D_BILLBOARD))
	{
		newArray = getBillboardFields();
	}
	else if(depNode.typeName().operator ==(X3D_SWITCH))
	{
		newArray = getSwitchFields();
	}
	else if(depNode.typeName().operator ==(X3D_COLLISION))
	{
		newArray = getCollisionFields();
	}
	else if(depNode.typeName().operator ==(X3D_LOD))
	{
		newArray = getLODFields();
	}
//	else if(depNode.typeName().operator ==(X3D_IFS))
//	{
//		newArray = getIFSFields(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_COL))
//	{
//		newArray = getColorFields(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_COLRGBA))
//	{
//		newArray = CRGBA_Fields(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_NORMAL))
//	{
//		newArray = getNormal_Fields(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_TEXCOORD))
//	{
//		newArray = getTextCoordFields(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_COORD))
//	{
//		newArray = getCoord_Fields(depNode, subNode);
//	}
	else if(depNode.typeName().operator ==(X3D_BOX))
	{
		newArray = getBoxFields();
	}
	else if(depNode.typeName().operator ==(X3D_SPHERE))
	{
		newArray = getSphereFields();
	}
	else if(depNode.typeName().operator ==(X3D_CONE))
	{
		newArray = getConeFields();
	}
	else if(depNode.typeName().operator ==(X3D_CYL))
	{
		newArray = getCylinderFields();
	}
	else if(depNode.typeName().operator ==(X3D_VIEW))
	{
		newArray = getViewpointFields();
	}
	else if(depNode.typeName().operator ==(X3D_DIRLIGHT))
	{
		newArray = getDirLightFields();
	}
	else if(depNode.typeName().operator ==(X3D_SPOTLIGHT))
	{
		newArray = getSpotLightFields();
	}
	else if(depNode.typeName().operator ==(X3D_POINTLIGHT))
	{
		newArray = getPointLightFields();
	}
	else if(depNode.typeName().operator ==(X3D_AMBLIGHT))
	{
		newArray = getPointLightFields();
	}
	else if(depNode.typeName().operator ==(X3D_INLINE))
	{
		newArray = getInlineFields();
	}
//	else if(depNode.typeName().operator ==(X3D_AREALIGHT))
//	{
//		newArray = getSpotLightFields(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_VOLLIGHT))
//	{
//		newArray = getPointLightFields(depNode, subNode);
//	}
	return newArray;
}

MStringArray web3dExportMethods::getX3DCollidableShapeValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//center
	MString tString("0 0 0");
	MString tString2 = getSFVec3f("rotatePivot", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//rotation
	tString.set("0 0 1 0");
	tString2 = getSFRotationWorld("rotate", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");
	
	//translation
	tString.set("0 0 0");
	tString2 = getSFVec3fWorld("translate", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray web3dExportMethods::getX3DFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray newArray;
	if(depNode.typeName().operator ==(X3D_TRANS))
	{
		newArray = getTransFieldValues(depNode, subNode);
	}
	if(depNode.typeName().operator ==(X3D_ANCHOR))
	{
		newArray = getAnchorFieldValues(depNode, subNode);
	}
	if(depNode.typeName().operator ==(X3D_AUDIOCLIP))
	{
		newArray = getAudioClipFieldValues(depNode, subNode);
	}
	if(depNode.typeName().operator ==(X3D_SOUND))
	{
		newArray = getSoundFieldValues(depNode, subNode);
	}
	if(depNode.typeName().operator ==(X3D_TEXTTRANS))
	{
		newArray = getTextureTransformFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_MESH))
	{
		newArray = getShapeFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_PROXSENSOR))
	{
		newArray = getProxFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_VISSENSOR))
	{
		newArray = getVisFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_TIMESENSOR))
	{
		newArray = getTiSFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_TOUCHSENSOR))
	{
		newArray = getToSFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_GAMEPADSENSOR))
	{
		newArray = getGamepadSFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_CYLSENSOR))
	{
		newArray = getCylSensorFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_PLANESENSOR))
	{
		newArray = getPlaneSensorFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_SPHERESENSOR))
	{
		newArray = getSphereSensorFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_LOADSENSOR))
	{
		newArray = getLoadSensorFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_KEYSENSOR))
	{
		newArray = getKeySensorFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_STRINGSENSOR))
	{
		newArray = getStringSensorFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_NAVIGATION))
	{
		newArray = getNIFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_WORLDINFO))
	{
		newArray = getWIFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_POSINTER))
	{
		newArray = getPIFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_ORIINTER))
	{
		newArray = getOIFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_COLORINTER))
	{
		newArray = getColorIFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_SCALINTER))
	{
		newArray = getScalarIFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_COORDINTER))
	{
		newArray = getCoordIFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_NORMINTER))
	{
		newArray = getNormalIFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_BOOLSEQ))
	{
		newArray = getBoolSFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_INTSEQ))
	{
		newArray = getIntSFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_BOOLFILTER))
	{
		MStringArray empty;
		newArray = empty;
	}
	else if(depNode.typeName().operator ==(X3D_BOOLTOGGLE))
	{
		newArray = getBoolToggleFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_BOOLTRIGGER))
	{
		MStringArray empty;
		newArray = empty;
	}
	else if(depNode.typeName().operator ==(X3D_TIMETRIGGER))
	{
		MStringArray empty;
		newArray = empty;
	}
	else if(depNode.typeName().operator ==(X3D_INTTRIGGER))
	{
		newArray = getIntTriggerFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_SCRIPT))
	{
		newArray = getScriptFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_GROUP))
	{
		newArray = getGroupFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_BILLBOARD))
	{
		newArray = getBillboardFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_SWITCH))
	{
		newArray = getSwitchFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_COLLISION))
	{
		newArray = getCollisionFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_LOD))
	{
		newArray = getLODFieldValues(depNode, subNode);
	}
//	else if(depNode.typeName().operator ==(X3D_IFS))
//	{
//		newArray = getIFSFieldValues(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_COL))
//	{
//		newArray = getColorFieldValues(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_COLRGBA))
//	{
//		newArray = CRGBA_FieldValues(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_NORMAL))
//	{
//		newArray = getNormal_FieldValues(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_TEXCOORD))
//	{
//		newArray = getTextCoordFieldValues(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_COORD))
//	{
//		newArray = getCoord_FieldValues(depNode, subNode);
//	}
	else if(depNode.typeName().operator ==(X3D_BOX))
	{
		newArray = getBoxFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_SPHERE))
	{
		newArray = getSphereFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_CONE))
	{
		newArray = getConeFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_CYL))
	{
		newArray = getCylinderFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_VIEW))
	{
		newArray = getViewpointFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_DIRLIGHT))
	{
		newArray = getDirLightFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_SPOTLIGHT))
	{
		newArray = getSpotLightFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_POINTLIGHT))
	{
		newArray = getPointLightFieldValues(depNode, subNode);
	}
	else if(depNode.typeName().operator ==(X3D_INLINE))
	{
		newArray = getInlineFieldValues(depNode, subNode);
	}
//	else if(depNode.typeName().operator ==(X3D_AMBLIGHT))
//	{
//		newArray = getAPointLightFieldValues(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_AREALIGHT))
//	{
//		newArray = getSpotLightFieldValues(depNode, subNode);
//	}
//	else if(depNode.typeName().operator ==(X3D_VOLLIGHT))
//	{
//		newArray = getPointLightFieldValues(depNode, subNode);
//	}

	return newArray;
}

MStringArray web3dExportMethods::getX3DFields(MString nodeName, unsigned int subNode)
{
	MFnDependencyNode tDep(getMyDepNodeObj(nodeName));
	return getX3DFields(tDep, subNode);
}

MStringArray web3dExportMethods::getX3DFieldValues(MString nodeName, unsigned int subNode)
{
	MFnDependencyNode tDep(getMyDepNodeObj(nodeName));
	return getX3DFieldValues(tDep, subNode);
}

/*
MFnDependencyNode web3dExportMethods::findNonExportTexture(MString nodeName)
{
	cout << "Texture Name First: " << nodeName << endl;
//	MFnDependencyNode tDep = getMyDepNode(nodeName);
	MFnDependencyNode tDep(getMyDepNodeObj(nodeName));
	MFnDependencyNode tester;
	if(tDep.object().operator ==(tester.object()))
	{
		int i = nodeName.rindex('_');
		if(i>1)
		{
			MString chop1 = nodeName.substring(0,i-1);
			int j = chop1.rindex('_');
			if(j>1)
			{
				MString newTexture = chop1.substring(0, j-1);
//				tDep.setObject(getMyDepNode(newTexture).object());
				tDep.setObject(getMyDepNodeObj(newTexture));
			}
		}
	}
	cout << "Texture Name Second: " << tDep.name() << endl;
	return tDep;
}
*/

MObject web3dExportMethods::findNonExportTexture(MString nodeName)
{
	cout << "Texture Name First: " << nodeName << endl;
//	MFnDependencyNode tDep = getMyDepNode(nodeName);
	MFnDependencyNode tDep(getMyDepNodeObj(nodeName));
	MFnDependencyNode tester;
	if(tDep.object().operator ==(tester.object()))
	{
		int i = nodeName.rindex('_');
		if(i>1)
		{
			MString chop1 = nodeName.substring(0,i-1);
			int j = chop1.rindex('_');
			if(j>1)
			{
				MString newTexture = chop1.substring(0, j-1);
//				tDep.setObject(getMyDepNode(newTexture).object());
				tDep.setObject(getMyDepNodeObj(newTexture));
			}
		}
	}
	cout << "Texture Name Second: " << tDep.name() << endl;
	return tDep.object();
}

/*
MFnDependencyNode web3dExportMethods::getMyDepNode(MString nodeName)
{
	MSelectionList tempList;
	tempList.clear();
	tempList.add(nodeName);
	MItSelectionList newMItSel(tempList);
	MObject tObject;
	newMItSel.getDependNode(tObject);
	MFnDependencyNode newDep(tObject);
	return newDep;
}
*/

MObject web3dExportMethods::getMyDepNodeObj(MString nodeName)
{
	MSelectionList tempList;
	tempList.clear();
	tempList.add(nodeName);
	MItSelectionList newMItSel(tempList);
	MObject tObject;
	newMItSel.getDependNode(tObject);
	return tObject;
}

//MStringArray	web3dExportMethods::getAudioClipFields(MFnDependencyNode &depNode, unsigned int subNode)
MStringArray	web3dExportMethods::getAudioClipFields()
{
	MStringArray tArray;
	tArray.append("description");
	tArray.append("loop");
	tArray.append("pauseTime");
	tArray.append("pitch");
	tArray.append("resumeTime");
	tArray.append("startTime");
	tArray.append("stopTime");
	tArray.append("url");
	return tArray;
}

MStringArray	web3dExportMethods::getTransFields()
{
	MStringArray tArray;
	tArray.append("center");
	tArray.append("rotation");
	tArray.append("scale");
	tArray.append("scaleOrientation");
	tArray.append("translation");
	return tArray;
}

MStringArray	web3dExportMethods::getHAnimHumanoidFields()
{
	MStringArray tArray;
	tArray.append("name");
	tArray.append("center");
	tArray.append("rotation");
	tArray.append("scale");
	tArray.append("scaleOrientation");
	tArray.append("translation");
	return tArray;
}

MStringArray	web3dExportMethods::getJointFields()
{
	MStringArray tArray;
	tArray.append("name");
	tArray.append("center");
	tArray.append("rotation");
	tArray.append("scale");
	tArray.append("scaleOrientation");
	tArray.append("translation");
	return tArray;
}

MStringArray	web3dExportMethods::getSiteFields()
{
	MStringArray tArray;
	tArray.append("name");
	tArray.append("center");
	tArray.append("rotation");
	tArray.append("scale");
	tArray.append("scaleOrientation");
	tArray.append("translation");
	return tArray;
}

MStringArray	web3dExportMethods::getAnchorFields()
{
	MStringArray tArray;
	tArray.append("description");
	tArray.append("parameter");
	tArray.append("url");
	return tArray;
}

MStringArray	web3dExportMethods::getSoundFields()		//MFnDependencyNode depNode, unsigned int subNode)
{
	MStringArray tArray;

	tArray.append("direction");
	tArray.append("intensity");
	tArray.append("location");
	tArray.append("maxBack");
	tArray.append("maxFront");
	tArray.append("minBack");
	tArray.append("minFront");
	tArray.append("priority");
	tArray.append("spatialize");

	return tArray;
}

MStringArray	web3dExportMethods::getTextureTransformFields()
{
	MStringArray tArray;
	tArray.append("center");
	tArray.append("rotation");
	tArray.append("scale");
	tArray.append("translation");
	return tArray;
}

MStringArray web3dExportMethods::getMaterialFields()
{
	MStringArray tArray;
	tArray.append("ambientIntensity");
	tArray.append("diffuseColor");
	tArray.append("emissiveColor");
	tArray.append("shininess");
	tArray.append("specularColor");
	tArray.append("transparency");	
	return tArray;
}

MStringArray	web3dExportMethods::getShapeFields()		//(MFnDependencyNode depNode, unsigned int subNode)
{
	MStringArray tArray;
	tArray.append("none");

	return tArray;
}
MStringArray	web3dExportMethods::getProxFields()			//(MFnDependencyNode depNode, unsigned int subNode)
{
	MStringArray tArray;
	tArray.append("enabled");
	tArray.append("center");
	tArray.append("size");
	return tArray;
}
MStringArray	web3dExportMethods::getVisFields()			//(MFnDependencyNode depNode, unsigned int subNode)
{
	MStringArray tArray;
	tArray.append("enabled");
	tArray.append("center");
	tArray.append("size");
	return tArray;
}
MStringArray	web3dExportMethods::getTiSFields()			//(MFnDependencyNode depNode, unsigned int subNode)
{
	MStringArray tArray;
	tArray.append("cycleInterval");
	tArray.append("enabled");
	tArray.append("loop");
	if(exEncoding != VRML97ENC) tArray.append("pauseTime");//Not in VRML
	if(exEncoding != VRML97ENC) tArray.append("resumeTime");//Not in VRML
	tArray.append("startTime");
	tArray.append("stopTime");
	return tArray;
}

MStringArray	web3dExportMethods::getToSFields()			//(MFnDependencyNode depNode, unsigned int subNode)
{
	MStringArray tArray;
	if(exEncoding != VRML97ENC) tArray.append("description");//Not in VRML
	tArray.append("enabled");
	return tArray;
}

MStringArray	web3dExportMethods::getGamepadSFields()		//(MFnDependencyNode depNode, unsigned int subNode)
{
	MStringArray tArray;
	tArray.append("name");
	tArray.append("enabled");
	return tArray;
}

MStringArray	web3dExportMethods::getCylSensorFields()
{
	MStringArray tArray;
	tArray.append("autoOffset");
	if(exEncoding != VRML97ENC) tArray.append("description");//Not in VRML
	tArray.append("diskAngle");
	tArray.append("enabled");
	tArray.append("maxAngle");
	tArray.append("minAngle");
	tArray.append("offset");

	return tArray;
}

MStringArray	web3dExportMethods::getPlaneSensorFields()
{
	MStringArray tArray;
	tArray.append("autoOffset");
	if(exEncoding != VRML97ENC) tArray.append("description");//Not in VRML
	tArray.append("enabled");
	tArray.append("maxPosition");
	tArray.append("minPosition");
	tArray.append("offset");

	return tArray;
}

MStringArray	web3dExportMethods::getSphereSensorFields()
{
	MStringArray tArray;
	tArray.append("autoOffset");
	if(exEncoding != VRML97ENC) tArray.append("description");//Not in VRML
	tArray.append("enabled");
	tArray.append("offset");

	return tArray;
}

MStringArray	web3dExportMethods::getKeySensorFields()
{
	MStringArray tArray;
	tArray.append("enabled");
	return tArray;
}

MStringArray	web3dExportMethods::getLoadSensorFields()
{
	MStringArray tArray;
	tArray.append("enabled");
	tArray.append("timeOut");
//	tArray.append("watchList");

	return tArray;
}

MStringArray	web3dExportMethods::getStringSensorFields()
{
	MStringArray tArray;
	tArray.append("deletionAllowed");
	tArray.append("enabled");

	return tArray;
}

MStringArray	web3dExportMethods::getNIFields()
{
	MStringArray tArray;
	tArray.append("avatarSize");
	tArray.append("headlight");
	tArray.append("speed");
	if(exEncoding != VRML97ENC) tArray.append("transitionType");
	tArray.append("type");
	tArray.append("visibilityLimit");

	return tArray;
}
MStringArray	web3dExportMethods::getWIFields()
{
	MStringArray tArray;
	tArray.append("title");
	tArray.append("info");
	return tArray;
}
MStringArray	web3dExportMethods::getPIFields()
{
	MStringArray tArray;
	tArray.append("key");
	tArray.append("keyValue");
	return tArray;
}

MStringArray	web3dExportMethods::getOIFields()
{
	MStringArray tArray;
	tArray.append("key");
	tArray.append("keyValue");
	return tArray;
}

MStringArray	web3dExportMethods::getColorIFields()
{
	MStringArray tArray;
	tArray.append("key");
	tArray.append("keyValue");
	return tArray;
}

MStringArray	web3dExportMethods::getCoordIFields()
{
	MStringArray tArray;
	tArray.append("key");
	tArray.append("keyValue");
	return tArray;
}

MStringArray	web3dExportMethods::getScalarIFields()
{
	MStringArray tArray;
	tArray.append("key");
	tArray.append("keyValue");
	return tArray;
}

MStringArray	web3dExportMethods::getNormalIFields()
{
	MStringArray tArray;
	tArray.append("key");
	tArray.append("keyValue");
	return tArray;
}

MStringArray	web3dExportMethods::getBoolSFields()
{
	MStringArray tArray;
	tArray.append("key");
	tArray.append("keyValue");
	return tArray;
}

MStringArray	web3dExportMethods::getIntSFields()
{
	MStringArray tArray;
	tArray.append("key");
	tArray.append("keyValue");
	return tArray;
}

MStringArray	web3dExportMethods::getBoolToggleFields()
{
	MStringArray tArray;
	tArray.append("toggle");
	return tArray;
}

MStringArray	web3dExportMethods::getIntTriggerFields()
{
	MStringArray tArray;
	tArray.append("integerKey");
	return tArray;
}

MStringArray	web3dExportMethods::getScriptFields()
{
	MStringArray tArray;
	tArray.append("directOutput");
	tArray.append("mustEvaluate");
	tArray.append("url");
	return tArray;
}
MStringArray	web3dExportMethods::getGroupFields()
{
	MStringArray tArray;
	tArray.append("");
	return tArray;
}

MStringArray	web3dExportMethods::getBillboardFields()
{
	MStringArray tArray;
	tArray.append("axisOfRotation");
	return tArray;
}

MStringArray	web3dExportMethods::getSwitchFields()
{
	MStringArray tArray;
	tArray.append("whichChoice");
	return tArray;
}
MStringArray	web3dExportMethods::getCollisionFields()
{
	MStringArray tArray;
	if(exEncoding==VRML97ENC) tArray.append("collide");
	else tArray.append("enabled");
	return tArray;
}
MStringArray	web3dExportMethods::getLODFields()
{
	MStringArray tArray;
	tArray.append("center");
	tArray.append("range");
	return tArray;
}

MStringArray	web3dExportMethods::getCollisionCollectionFields()
{
	MStringArray tArray;
	tArray.append("appliedParameters");
	tArray.append("bounce");
	tArray.append("enabled");
	tArray.append("frictionCoefficients");
	tArray.append("minBounceSpeed");
	tArray.append("surfaceSpeed");
	tArray.append("slipFactors");
	tArray.append("softnessErrorCorrection");
	tArray.append("softnessConstantForceMix");
	return tArray;
}

MStringArray	web3dExportMethods::getCollisionSensorFields()
{
	MStringArray tArray;
	tArray.append("enabled");
	return tArray;
}

MStringArray	web3dExportMethods::getCollisionSpaceFields()
{
	MStringArray tArray;
	tArray.append("enabled");
	tArray.append("useGeometry");
	return tArray;
}

MStringArray	web3dExportMethods::getRigidBodyFields()
{
	MStringArray tArray;
	tArray.append("angularDampingFactor");
	tArray.append("angularVelocity");
	tArray.append("autoDamp");
	tArray.append("autoDisable");
	tArray.append("centerOfMass");
	tArray.append("disableAngularSpeed");
	tArray.append("disableLinearSpeed");
	tArray.append("disableTime");
	tArray.append("enabled");
	tArray.append("fixedRotationAxis");
	tArray.append("fixed");
	tArray.append("forces");
	tArray.append("inertia");
	tArray.append("linearDampingFactor");
	tArray.append("linearVelocity");
	tArray.append("mass");
	tArray.append("orientation");
	tArray.append("position");
	tArray.append("torques");
	tArray.append("useFiniteRotation");
	tArray.append("useGlobalGravity");
	return tArray;
}

MStringArray	web3dExportMethods::getRBCFields()
{
	MStringArray tArray;
	tArray.append("autoDisable");
	tArray.append("constantForceMix");
	tArray.append("contactSurfaceThickness");
	tArray.append("disableAngularSpeed");
	tArray.append("disableLinearSpeed");
	tArray.append("disableTime");
	tArray.append("enabled");
	tArray.append("errorCorrection");
	tArray.append("gravity");
	tArray.append("iterations");
	tArray.append("maxCorrectionSpeed");
	tArray.append("preferAccuracy");
	return tArray;
}
MStringArray	web3dExportMethods::getIFSFields()
{
	MStringArray tArray;
	tArray.append("ccw");
	tArray.append("coordIndex");
	tArray.append("colorIndex");
	tArray.append("colorPerVertex");
	tArray.append("convex");
	tArray.append("creaseAngle");
	tArray.append("normalIndex");
	tArray.append("normalPerVertex");
	tArray.append("solid");
	tArray.append("texCoordIndex");
	return tArray;
}
MStringArray	web3dExportMethods::getColorFields()
{
	MStringArray tArray;
	tArray.append("color");
	return tArray;
}
MStringArray	web3dExportMethods::CRGBA_Fields()
{
	MStringArray tArray;
	return tArray;
}
MStringArray	web3dExportMethods::getNormal_Fields()
{
	MStringArray tArray;
	tArray.append("vector");
	return tArray;
}
MStringArray	web3dExportMethods::getTextCoordFields()
{
	MStringArray tArray;
	tArray.append("point");
	return tArray;
}
MStringArray	web3dExportMethods::getCoord_Fields()
{
	MStringArray tArray;
	tArray.append("point");
	return tArray;
}
MStringArray	web3dExportMethods::getBoxFields()
{
	MStringArray tArray;
	tArray.append("size");
	if(exEncoding!=VRML97ENC) tArray.append("solid");
	return tArray;
}
MStringArray	web3dExportMethods::getSphereFields()
{
	MStringArray tArray;

	tArray.append("radius");
	if(exEncoding != VRML97ENC)	tArray.append("solid");

	return tArray;
}
MStringArray	web3dExportMethods::getConeFields()
{
	MStringArray tArray;
	tArray.append("bottom");
	tArray.append("bottomRadius");
	tArray.append("height");
	tArray.append("side");
	if(exEncoding!=VRML97ENC) tArray.append("solid");
	return tArray;
}
MStringArray	web3dExportMethods::getCylinderFields()
{
	MStringArray tArray;

	tArray.append("bottom");
	tArray.append("height");
	tArray.append("radius");
	tArray.append("side");
	if(exEncoding != VRML97ENC)	tArray.append("solid");
	tArray.append("top");

	return tArray;
}
MStringArray	web3dExportMethods::getViewpointFields()
{
	MStringArray tArray;
	if(exEncoding != VRML97ENC) tArray.append("centerOfRotation");//Not in VRML
	tArray.append("description");
	tArray.append("fieldOfView");
	tArray.append("jump");
	tArray.append("orientation");
	tArray.append("position");
	return tArray;
}
MStringArray	web3dExportMethods::getDirLightFields()
{
	MStringArray tArray;

	tArray.append("ambientIntensity");
	tArray.append("color");
	tArray.append("direction");
	tArray.append("intensity");
	tArray.append("on");

	return tArray;
}
MStringArray	web3dExportMethods::getSpotLightFields()
{
	MStringArray tArray;
	tArray.append("ambientIntensity");
	tArray.append("attenuation");
	tArray.append("beamWidth");
	tArray.append("color");
	tArray.append("cutOffAngle");
	tArray.append("direction");
	tArray.append("intensity");
	tArray.append("location");
	tArray.append("on");
	tArray.append("radius");

	return tArray;
}
MStringArray	web3dExportMethods::getPointLightFields()
{
	MStringArray tArray;

	tArray.append("ambientIntensity");
	tArray.append("attenuation");
	tArray.append("color");
	tArray.append("intensity");
	tArray.append("location");
	tArray.append("on");
	tArray.append("radius");

	return tArray;
}

MStringArray web3dExportMethods::getInlineFields()
{
	MStringArray tArray;
	tArray.append("load");
	tArray.append("url");
	return tArray;
}

MString web3dExportMethods::getSFColorRGBA(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);

	unsigned int childNum;
	childNum = aPlug.numChildren();
	unsigned int i;
	float cFloat[4];
	for(i=0;i<childNum;i++)
	{
		MPlug tPlug = aPlug.child(i);
		tPlug.getValue(cFloat[i]);
		if(cFloat[i] > 1) cFloat[i] = 1;
	}
	cValue.set(cFloat[0]);
	cValue.operator +=(" ");
	cValue.operator +=(cFloat[1]);
	cValue.operator +=(" ");
	cValue.operator +=(cFloat[2]);
	cValue.operator +=(" ");
	cValue.operator +=(cFloat[3]);

	return cValue;
}

MString web3dExportMethods::getMFColorRGBA(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	for(i=0;i<vLength;i++)
	{
		MPlug nPlug = kvPlug.child(i);
		MPlug rPlug = nPlug.child(0);
		MPlug gPlug = nPlug.child(1);
		MPlug bPlug = nPlug.child(2);
		MPlug aPlug = nPlug.child(3);

		double tVal[4];
		rPlug.getValue(tVal[0]);
		gPlug.getValue(tVal[1]);
		bPlug.getValue(tVal[2]);
		aPlug.getValue(tVal[3]);

		cValue.operator +=(tVal[0]);
		cValue.operator +=(" ");
		cValue.operator +=(tVal[1]);
		cValue.operator +=(" ");
		cValue.operator +=(tVal[2]);
		cValue.operator +=(" ");
		cValue.operator +=(tVal[3]);
		if(i!=vLength-1) cValue.operator +=(",\n");
	}

	return cValue;
}

MString web3dExportMethods::getSFFloat(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);

	float fValue;
	aPlug.getValue(fValue);
	double dValue = (double)fValue;
	cValue.set(dValue);

	return cValue;
}

MString web3dExportMethods::getSFDouble(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);

	double dValue;
	aPlug.getValue(dValue);
	cValue.set(dValue);

	return cValue;
}

MString web3dExportMethods::getSFImage(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue = getSFString(sValue, depNode);
	return cValue;
}

MString web3dExportMethods::getMFImage(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
	for(i=0;i<vLength;i++)
	{
		MPlug dPlug = kvPlug.child(i);
		MString sVal;
		dPlug.getValue(sVal);

		cValue.operator +=(sVal);

		if(i!=vLength-1) cValue.operator +=(",\n");
	}

	return cValue;
}

MString web3dExportMethods::getMFDouble(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
	for(i=0;i<vLength;i++)
	{
		MPlug dPlug = kvPlug.child(i);
		double dVal;
		dPlug.getValue(dVal);

		MString dsVal;
		dsVal.set(dVal);
		cValue.operator +=(dsVal);

		if(j==5) j=0;
		if(i!=vLength-1)
		{
			if(j==4) cValue.operator +=("\n");
			else cValue.operator +=(" ");
			j=j+1;
		}
	}

	return cValue;
}

MString web3dExportMethods::getMFDoubleNonScript(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
	for(i=0;i<vLength;i++)
	{
		MPlug dPlug = kvPlug.elementByPhysicalIndex(i);
		double dVal;
		dPlug.getValue(dVal);

		MString dsVal;
		dsVal.set(dVal);
		cValue.operator +=(dsVal);

		if(j==5) j=0;
		if(i!=vLength-1)
		{
			if(j==4) cValue.operator +=("\n");
			else cValue.operator +=(" ");
			j=j+1;
		}
	}

	return cValue;
}

MString web3dExportMethods::getSFBool(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue("FALSE");
	if(exEncoding == X3DENC || exEncoding == X3DBENC) cValue.set("false");
	aPlug = depNode.findPlug(sValue);

	bool bValue;
	aPlug.getValue(bValue);
	
	if(bValue)
	{
		if(exEncoding == X3DENC || exEncoding == X3DBENC) cValue.set("true");
		else cValue.set("TRUE");
 	}

	return cValue;
}

MString web3dExportMethods::getMFBoolNonScript(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue;
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
	for(i=0;i<=vLength;i++)
	{
		MPlug bPlug = kvPlug.elementByPhysicalIndex(i);
		int tInt;
		bPlug.getValue(tInt);

		if(tInt==0)
		{
			if(exEncoding == X3DENC || exEncoding == X3DBENC) cValue.operator +=("false");
			else cValue.operator +=("FALSE");
		}
		else
		{
			if(exEncoding == X3DENC || exEncoding == X3DBENC) cValue.operator +=("true");
			else cValue.operator +=("TRUE");
		}
		if(j==5) j=0;
		if(i!=vLength)
		{
			if(j==4) cValue.operator +=("\n");
			else cValue.operator +=(" ");
			j=j+1;
		}
	}

	return cValue;
}

MString web3dExportMethods::getMFBool(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue;
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
	for(i=0;i<vLength;i++)
	{
		MPlug bPlug = kvPlug.elementByPhysicalIndex(i);
		int tInt;
		bPlug.getValue(tInt);

		if(tInt==0)
		{
			if(exEncoding == X3DENC || exEncoding == X3DBENC) cValue.operator +=("false");
			else cValue.operator +=("FALSE");
		}
		else
		{
			if(exEncoding == X3DENC || exEncoding == X3DBENC) cValue.operator +=("true");
			else cValue.operator +=("TRUE");
		}
		if(j==5) j=0;
		if(i!=vLength-1)
		{
			if(j==4) cValue.operator +=("\n");
			else cValue.operator +=(" ");
			j=j+1;
		}
	}

	return cValue;
}

MString web3dExportMethods::getSFInt32(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);

	int iValue;
	aPlug.getValue(iValue);
	cValue.set(iValue);

	return cValue;
}

MString web3dExportMethods::getMFInt32(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
	for(i=0;i<vLength;i++)
	{
		MPlug iPlug = kvPlug.child(i);
		int iVal;
		iPlug.getValue(iVal);

		MString isVal;
		isVal.set(iVal);
		cValue.operator +=(isVal);

		if(j==5) j=0;
		if(i!=vLength-1)
		{
			if(j==4) cValue.operator +=("\n");
			else cValue.operator +=(" ");
			j=j+1;
		}
	}

	return cValue;
}

MString web3dExportMethods::getMFInt32Metadata(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
	for(i=0;i<vLength;i++)
	{
		MPlug iPlug = kvPlug.elementByPhysicalIndex(i);
		int iVal;
		iPlug.getValue(iVal);

		MString isVal;
		isVal.set(iVal);
		cValue.operator +=(isVal);

		if(j==5) j=0;
		if(i!=vLength-1)
		{
			if(j==4) cValue.operator +=("\n");
			else cValue.operator +=(" ");
			j=j+1;
		}
	}

	return cValue;
}

MString web3dExportMethods::getMFInt32NonScript(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
	for(i=0;i<=vLength;i++)
	{
		MPlug iPlug = kvPlug.elementByPhysicalIndex(i);
		int iVal;
		iPlug.getValue(iVal);

		MString isVal;
		isVal.set(iVal);
		cValue.operator +=(isVal);

		if(j==5) j=0;
		if(i!=vLength)
		{
			if(j==4) cValue.operator +=("\n");
			else cValue.operator +=(" ");
			j=j+1;
		}
	}

	return cValue;
}

MString web3dExportMethods::getSFTime(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);

	double dValue;
	aPlug.getValue(dValue);
	cValue.set(dValue);

	return cValue;
}

MString web3dExportMethods::getMFTime(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue = getMFDouble(sValue, depNode);
	return cValue;
}

MString web3dExportMethods::getSFVec3f(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);

	unsigned int i;
	float cFloat[3];
	for(i=0;i<3;i++)
	{
		MPlug tPlug = aPlug.child(i);
		tPlug.getValue(cFloat[i]);
	}
	cValue.set(cFloat[0]);
	cValue.operator +=(" ");
	cValue.operator +=(cFloat[1]);
	cValue.operator +=(" ");
	cValue.operator +=(cFloat[2]);

	return cValue;
}

MString web3dExportMethods::getSFVec3fWorld(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug = depNode.findPlug(sValue);
	MString cValue;
	MObject obj = aPlug.node();
	MFnTransform tform(obj);

	MVector avec = tform.translation(MSpace::kWorld);

	cValue.set(avec.x);
	cValue.operator +=(" ");
	cValue.operator +=(avec.y);
	cValue.operator +=(" ");
	cValue.operator +=(avec.z);

	return cValue;
}

MString web3dExportMethods::getSFVec3fHAnim(MString sValue, MFnDependencyNode &depNode, double pVal[])
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);

	unsigned int i;
	float cFloat[3];
	float sFloat[3];
	for(i=0;i<3;i++)
	{
		MPlug tPlug = aPlug.child(i);
		tPlug.getValue(cFloat[i]);
		sFloat[i] = pVal[i] + cFloat[i];
	}
	cValue.set(sFloat[0]);
	cValue.operator +=(" ");
	cValue.operator +=(sFloat[1]);
	cValue.operator +=(" ");
	cValue.operator +=(sFloat[2]);

	return cValue;
}

MString web3dExportMethods::getSFVec3d(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);

	unsigned int i;
	float cDouble[3];
	for(i=0;i<3;i++)
	{
		MPlug tPlug = aPlug.child(i);
		tPlug.getValue(cDouble[i]);
	}
	cValue.set(cDouble[0]);
	cValue.operator +=(" ");
	cValue.operator +=(cDouble[1]);
	cValue.operator +=(" ");
	cValue.operator +=(cDouble[2]);

	return cValue;
}

MString web3dExportMethods::getSFVec2f(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);

	unsigned int i;
	float cFloat[2];
	for(i=0;i<2;i++)
	{
		MPlug tPlug = aPlug.child(i);
		tPlug.getValue(cFloat[i]);
	}
	cValue.set(cFloat[0]);
	cValue.operator +=(" ");
	cValue.operator +=(cFloat[1]);

	return cValue;
}

MString web3dExportMethods::getSFVec2d(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);

	unsigned int i;
	double cDouble[2];
	for(i=0;i<2;i++)
	{
		MPlug tPlug = aPlug.child(i);
		tPlug.getValue(cDouble[i]);
	}
	cValue.set(cDouble[0]);
	cValue.operator +=(" ");
	cValue.operator +=(cDouble[1]);

	return cValue;
}

MString web3dExportMethods::getMFVec3f(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	for(i=0;i<vLength;i++)
	{
		MPlug nPlug = kvPlug.child(i);
		MPlug xPlug = nPlug.child(0);
		MPlug yPlug = nPlug.child(1);
		MPlug zPlug = nPlug.child(2);

		float fVec[3];
		xPlug.getValue(fVec[0]);
		yPlug.getValue(fVec[1]);
		zPlug.getValue(fVec[2]);

		cValue.operator +=(fVec[0]);
		cValue.operator +=(" ");
		cValue.operator +=(fVec[1]);
		cValue.operator +=(" ");
		cValue.operator +=(fVec[2]);
		if(i!=vLength-1) cValue.operator +=(",\n");
	}

	return cValue;
}

MString web3dExportMethods::getMFVec3fNonScript(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	for(i=0;i<=vLength;i++)
//	for(i=0;i<vLength;i++)
	{
		MPlug nPlug = kvPlug.elementByPhysicalIndex(i);
		MPlug xPlug = nPlug.child(0);
		MPlug yPlug = nPlug.child(1);
		MPlug zPlug = nPlug.child(2);

		float fVec[3];
		xPlug.getValue(fVec[0]);
		yPlug.getValue(fVec[1]);
		zPlug.getValue(fVec[2]);

		cValue.operator +=(fVec[0]);
		cValue.operator +=(" ");
		cValue.operator +=(fVec[1]);
		cValue.operator +=(" ");
		cValue.operator +=(fVec[2]);
		if(i!=vLength) cValue.operator +=(",\n");
	}

	return cValue;
}

MString web3dExportMethods::getMFVec2f(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	for(i=0;i<vLength;i++)
	{
		MPlug nPlug = kvPlug.child(i);
		MPlug xPlug = nPlug.child(0);
		MPlug yPlug = nPlug.child(1);

		float fVec[2];
		xPlug.getValue(fVec[0]);
		yPlug.getValue(fVec[1]);

		cValue.operator +=(fVec[0]);
		cValue.operator +=(" ");
		cValue.operator +=(fVec[1]);
		if(i!=vLength-1) cValue.operator +=(",\n");
	}

	return cValue;
}

MString web3dExportMethods::getMFVec2d(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	for(i=0;i<vLength;i++)
	{
		MPlug nPlug = kvPlug.child(i);
		MPlug xPlug = nPlug.child(0);
		MPlug yPlug = nPlug.child(1);

		double dVec[2];
		xPlug.getValue(dVec[0]);
		yPlug.getValue(dVec[1]);

		cValue.operator +=(dVec[0]);
		cValue.operator +=(" ");
		cValue.operator +=(dVec[1]);
		if(i!=vLength-1) cValue.operator +=(",\n");
	}

	return cValue;
}

MString web3dExportMethods::getMFVec3d(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	for(i=0;i<vLength;i++)
	{
		MPlug nPlug = kvPlug.child(i);
		MPlug xPlug = nPlug.child(0);
		MPlug yPlug = nPlug.child(1);
		MPlug zPlug = nPlug.child(2);

		double dVec[3];
		xPlug.getValue(dVec[0]);
		yPlug.getValue(dVec[1]);
		zPlug.getValue(dVec[2]);

		cValue.operator +=(dVec[0]);
		cValue.operator +=(" ");
		cValue.operator +=(dVec[1]);
		cValue.operator +=(" ");
		cValue.operator +=(dVec[2]);
		if(i!=vLength-1) cValue.operator +=(",\n");
	}

	return cValue;
}

MString web3dExportMethods::getMultipleMFVec3f(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString ccsString = sValue;
	ccsString.operator +=("_cc_s");
	MPlug ccsPlug = depNode.findPlug(ccsString);

	int ccs;
	ccsPlug.getValue(ccs);
	unsigned int vsLen = ccs;

	unsigned int i;
	unsigned int j = 0;
//	for(i=0;i<=vsLen;i++)
	for(i=0;i<vsLen;i++)
	{
		MPlug vPlug = kvPlug.elementByPhysicalIndex(i);
		MPlug xPlug = vPlug.child(0);
		MPlug yPlug = vPlug.child(1);
		MPlug zPlug = vPlug.child(2);

		float fVec[3];

		xPlug.getValue(fVec[0]);
		yPlug.getValue(fVec[1]);
		zPlug.getValue(fVec[2]);

		cValue.operator +=(fVec[0]);
		cValue.operator +=(" ");
		cValue.operator +=(fVec[1]);
		cValue.operator +=(" ");
		cValue.operator +=(fVec[2]);
//		if(i!=vsLen) cValue.operator +=(",\n");
		if(i!=vsLen-1) cValue.operator +=(",\n");
 		else cout << "field data write complete..." << endl;
	}
	return cValue;
}

MString web3dExportMethods::getMFFloat(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
	for(i=0;i<vLength;i++)
	{
		MPlug fPlug = kvPlug.child(i);
		float fVal;
		fPlug.getValue(fVal);

		MString fsVal;
		fsVal.set(fVal);
		cValue.operator +=(fsVal);

		if(j==5) j=0;
		if(i!=vLength-1)
		{
			if(j==4) cValue.operator +=("\n");
			else cValue.operator +=(" ");
			j=j+1;
		}
	}

	return cValue;
}

MString web3dExportMethods::getMFFloatNonScript(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
	for(i=0;i<=vLength;i++)
//	for(i=0;i<vLength;i++)
	{
		MPlug fPlug = kvPlug.elementByPhysicalIndex(i);
		float fVal;
		fPlug.getValue(fVal);

		MString fsVal;
		fsVal.set(fVal);
		cValue.operator +=(fsVal);

		if(j==5) j=0;
		if(i!=vLength)
		{
			if(j==4) cValue.operator +=("\n");
			else cValue.operator +=(" ");
			j=j+1;
		}
	}

	return cValue;
}

MString web3dExportMethods::getMFFloatMetadata(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
//	for(i=0;i<=vLength;i++)
	for(i=0;i<vLength;i++)
	{
		MPlug fPlug = kvPlug.elementByPhysicalIndex(i);
		float fVal;
		fPlug.getValue(fVal);

		MString fsVal;
		fsVal.set(fVal);
		cValue.operator +=(fsVal);

		if(j==5) j=0;
		if(i!=vLength-1)
		{
			if(j==4) cValue.operator +=("\n");
			else cValue.operator +=(" ");
			j=j+1;
		}
	}

	return cValue;
}

MString web3dExportMethods::getMFRotation(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	for(i=0;i<vLength;i++)
	{
		MPlug nPlug = kvPlug.child(i);
		MPlug xPlug = nPlug.child(0);
		MPlug yPlug = nPlug.child(1);
		MPlug zPlug = nPlug.child(2);

		double dVec[3];
		xPlug.getValue(dVec[0]);
		yPlug.getValue(dVec[1]);
		zPlug.getValue(dVec[2]);

		double cv[3] = { cos(dVec[2]/2), cos(dVec[1]/2), cos(dVec[0]/2) };
		double sv[3] = { sin(dVec[2]/2), sin(dVec[1]/2), sin(dVec[0]/2) }; 
	
		double aCosDouble = ( cv[0] * cv[1] * cv[2] ) + ( sv[0] * sv[1] * sv[2] );
		double wVec = 2 * acos( aCosDouble );
		double xVec = ( cv[0] * cv[1] * sv[2] ) - ( sv[0] * sv[1] * cv[2]); 
		double yVec = ( cv[0] * sv[1] * cv[2] ) + ( sv[0] * cv[1] * sv[2]);
		double zVec = ( sv[0] * cv[1] * cv[2] ) - ( cv[0] * sv[1] * sv[2]);
	
		double denominator = (xVec * xVec) + (yVec * yVec) + (zVec * zVec);
		double xVec1 = 0;
		double yVec1 = 0;
		double zVec1 = 1;
		double wVec1 = 0;
		if(denominator != 0)
		{
			double dSqrt = sqrt(denominator);
			xVec1 = xVec/dSqrt;
			yVec1 = yVec/dSqrt;
			zVec1 = zVec/dSqrt;
			wVec1 = wVec;
		}

		cValue.operator +=(xVec1);
		cValue.operator +=(" ");
		cValue.operator +=(yVec1);
		cValue.operator +=(" ");
		cValue.operator +=(zVec1);
		cValue.operator +=(" ");
		cValue.operator +=(wVec1);

		if(i!=vLength-1) cValue.operator +=(",\n");
	}

	return cValue;
}

MString web3dExportMethods::getMFRotationNonScript(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	for(i=0;i<=vLength;i++)
//	for(i=0;i<vLength;i++)
	{
		MPlug nPlug = kvPlug.elementByPhysicalIndex(i);
		MPlug xPlug = nPlug.child(0);
		MPlug yPlug = nPlug.child(1);
		MPlug zPlug = nPlug.child(2);

		double dVec[3];
		xPlug.getValue(dVec[0]);
		yPlug.getValue(dVec[1]);
		zPlug.getValue(dVec[2]);

		double cv[3] = { cos(dVec[2]/2), cos(dVec[1]/2), cos(dVec[0]/2) };
		double sv[3] = { sin(dVec[2]/2), sin(dVec[1]/2), sin(dVec[0]/2) }; 
	
		double aCosDouble = ( cv[0] * cv[1] * cv[2] ) + ( sv[0] * sv[1] * sv[2] );
		double wVec = 2 * acos( aCosDouble );
		double xVec = ( cv[0] * cv[1] * sv[2] ) - ( sv[0] * sv[1] * cv[2]); 
		double yVec = ( cv[0] * sv[1] * cv[2] ) + ( sv[0] * cv[1] * sv[2]);
		double zVec = ( sv[0] * cv[1] * cv[2] ) - ( cv[0] * sv[1] * sv[2]);
	
		double denominator = (xVec * xVec) + (yVec * yVec) + (zVec * zVec);
		double xVec1 = 0;
		double yVec1 = 0;
		double zVec1 = 1;
		double wVec1 = 0;
		if(denominator != 0)
		{
			double dSqrt = sqrt(denominator);
			xVec1 = xVec/dSqrt;
			yVec1 = yVec/dSqrt;
			zVec1 = zVec/dSqrt;
			wVec1 = wVec;
		}

		cValue.operator +=(xVec1);
		cValue.operator +=(" ");
		cValue.operator +=(yVec1);
		cValue.operator +=(" ");
		cValue.operator +=(zVec1);
		cValue.operator +=(" ");
		cValue.operator +=(wVec1);

		if(i!=vLength) cValue.operator +=(",\n");
	}

	return cValue;
}

MString web3dExportMethods::getSFColor(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);

	unsigned int childNum;
	childNum = aPlug.numChildren();
	unsigned int i;
	float cFloat[3];
	for(i=0;i<childNum;i++)
	{
		MPlug tPlug = aPlug.child(i);
		tPlug.getValue(cFloat[i]);
		if(cFloat[i] > 1) cFloat[i] = 1;
	}
	cValue.set(cFloat[0]);
	cValue.operator +=(" ");
	cValue.operator +=(cFloat[1]);
	cValue.operator +=(" ");
	cValue.operator +=(cFloat[2]);

	return cValue;
}

MString web3dExportMethods::getMFColor(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	for(i=0;i<vLength;i++)
	{
		MPlug nPlug = kvPlug.child(i);
		MPlug rPlug = nPlug.child(0);
		MPlug gPlug = nPlug.child(1);
		MPlug bPlug = nPlug.child(2);

		double tVal[3];
		rPlug.getValue(tVal[0]);
		gPlug.getValue(tVal[1]);
		bPlug.getValue(tVal[2]);

		cValue.operator +=(tVal[0]);
		cValue.operator +=(" ");
		cValue.operator +=(tVal[1]);
		cValue.operator +=(" ");
		cValue.operator +=(tVal[2]);
		if(i!=vLength-1) cValue.operator +=(",\n");
	}

	return cValue;
}

MString web3dExportMethods::getMFColorNonScript(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	for(i=0;i<=vLength;i++)
//	for(i=0;i<vLength;i++)
	{
		MPlug nPlug = kvPlug.elementByPhysicalIndex(i);
		MPlug rPlug = nPlug.child(0);
		MPlug gPlug = nPlug.child(1);
		MPlug bPlug = nPlug.child(2);

		double tVal[3];
		rPlug.getValue(tVal[0]);
		gPlug.getValue(tVal[1]);
		bPlug.getValue(tVal[2]);

		cValue.operator +=(tVal[0]);
		cValue.operator +=(" ");
		cValue.operator +=(tVal[1]);
		cValue.operator +=(" ");
		cValue.operator +=(tVal[2]);
		if(i!=vLength) cValue.operator +=(",\n");
	}

	return cValue;
}

MString web3dExportMethods::getSFFloatFromSFVec3f(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);

	unsigned int childNum;
	childNum = aPlug.numChildren();
	unsigned int i;
	float cFloat[3];
	for(i=0;i<childNum;i++)
	{
		MPlug tPlug = aPlug.child(i);
		tPlug.getValue(cFloat[i]);
	}
	float tFloat = cFloat[0] + cFloat[1] + cFloat[2];
	tFloat = tFloat/3;
	cValue.set(tFloat);

	return cValue;
}

//MString web3dExportMethods::getSFRotation(MString sValue, MFnDependencyNode &depNode)
//{
//	return getSFRotation(sValue, depNode, false);
//}

//MString web3dExportMethods::getSFRotation(MString sValue, MFnDependencyNode &depNode, bool isLight)
MString web3dExportMethods::getSFRotationHAnim(MString, MFnDependencyNode &depNode)
{
//	MPlug aPlug = depNode.findPlug(sValue);
//	MObject obj = aPlug.node();
	MString cValue;
	MFnIkJoint jointNode(depNode.object());
//	MFnTransform tform(obj);
	MEulerRotation euler;
	jointNode.getRotation(euler);
	
//	tform.getRotation(euler);

	double cv[3] = { cos(euler[2]/2), cos(euler[1]/2), cos(euler[0]/2) };
	double sv[3] = { sin(euler[2]/2), sin(euler[1]/2), sin(euler[0]/2) }; 
	
	double aCosDouble = ( cv[0] * cv[1] * cv[2] ) + ( sv[0] * sv[1] * sv[2] );
	double wVec = 2 * acos( aCosDouble );
	double xVec = ( cv[0] * cv[1] * sv[2] ) - ( sv[0] * sv[1] * cv[2]); 
	double yVec = ( cv[0] * sv[1] * cv[2] ) + ( sv[0] * cv[1] * sv[2]);
	double zVec = ( sv[0] * cv[1] * cv[2] ) - ( cv[0] * sv[1] * sv[2]);
	
	double denominator = (xVec * xVec) + (yVec * yVec) + (zVec * zVec);
	double xVec1 = 0;
	double yVec1 = 0;
	double zVec1 = 1;
	double wVec1 = 0;
	if(denominator != 0)
	{
		double dSqrt = sqrt(denominator);
		xVec1 = xVec/dSqrt;
		yVec1 = yVec/dSqrt;
		zVec1 = zVec/dSqrt;
		wVec1 = wVec;
	}

	cValue.set(xVec1);
	cValue.operator +=(" ");
	cValue.operator +=(yVec1);
	cValue.operator +=(" ");
	cValue.operator +=(zVec1);
	cValue.operator +=(" ");
	cValue.operator +=(wVec1);

	return cValue;
}

MString web3dExportMethods::getSFRotation(MString sValue, MFnDependencyNode &depNode)
{

	MPlug aPlug = depNode.findPlug(sValue);
	MObject obj = aPlug.node();
	MString cValue;
	MFnTransform tform(obj);
	MEulerRotation euler;
	tform.getRotation(euler);

	double cv[3] = { cos(euler[2]/2), cos(euler[1]/2), cos(euler[0]/2) };
	double sv[3] = { sin(euler[2]/2), sin(euler[1]/2), sin(euler[0]/2) }; 
	
	double aCosDouble = ( cv[0] * cv[1] * cv[2] ) + ( sv[0] * sv[1] * sv[2] );
	double wVec = 2 * acos( aCosDouble );
	double xVec = ( cv[0] * cv[1] * sv[2] ) - ( sv[0] * sv[1] * cv[2]); 
	double yVec = ( cv[0] * sv[1] * cv[2] ) + ( sv[0] * cv[1] * sv[2]);
	double zVec = ( sv[0] * cv[1] * cv[2] ) - ( cv[0] * sv[1] * sv[2]);
	
	double denominator = (xVec * xVec) + (yVec * yVec) + (zVec * zVec);
	double xVec1 = 0;
	double yVec1 = 0;
	double zVec1 = 1;
	double wVec1 = 0;
	if(denominator != 0)
	{
		double dSqrt = sqrt(denominator);
		xVec1 = xVec/dSqrt;
		yVec1 = yVec/dSqrt;
		zVec1 = zVec/dSqrt;
		wVec1 = wVec;
	}

	cValue.set(xVec1);
	cValue.operator +=(" ");
	cValue.operator +=(yVec1);
	cValue.operator +=(" ");
	cValue.operator +=(zVec1);
	cValue.operator +=(" ");
	cValue.operator +=(wVec1);

	return cValue;
}

MString web3dExportMethods::getSFRotationWorld(MString sValue, MFnDependencyNode &depNode)
{

	MPlug aPlug = depNode.findPlug(sValue);
	MObject obj = aPlug.node();
	MString cValue;
	MFnTransform tform(obj);
	MQuaternion quat;
	tform.getRotation(quat, MSpace::kWorld);
	MEulerRotation euler = quat.asEulerRotation();

	double cv[3] = { cos(euler[2]/2), cos(euler[1]/2), cos(euler[0]/2) };
	double sv[3] = { sin(euler[2]/2), sin(euler[1]/2), sin(euler[0]/2) }; 
	
	double aCosDouble = ( cv[0] * cv[1] * cv[2] ) + ( sv[0] * sv[1] * sv[2] );
	double wVec = 2 * acos( aCosDouble );
	double xVec = ( cv[0] * cv[1] * sv[2] ) - ( sv[0] * sv[1] * cv[2]); 
	double yVec = ( cv[0] * sv[1] * cv[2] ) + ( sv[0] * cv[1] * sv[2]);
	double zVec = ( sv[0] * cv[1] * cv[2] ) - ( cv[0] * sv[1] * sv[2]);
	
	double denominator = (xVec * xVec) + (yVec * yVec) + (zVec * zVec);
	double xVec1 = 0;
	double yVec1 = 0;
	double zVec1 = 1;
	double wVec1 = 0;
	if(denominator != 0)
	{
		double dSqrt = sqrt(denominator);
		xVec1 = xVec/dSqrt;
		yVec1 = yVec/dSqrt;
		zVec1 = zVec/dSqrt;
		wVec1 = wVec;
	}

	cValue.set(xVec1);
	cValue.operator +=(" ");
	cValue.operator +=(yVec1);
	cValue.operator +=(" ");
	cValue.operator +=(zVec1);
	cValue.operator +=(" ");
	cValue.operator +=(wVec1);

	return cValue;
}

MString web3dExportMethods::getDirection(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue;
	MPlug aPlug = depNode.findPlug(sValue);
	double value[3];

	MPlug plug = aPlug.child(0);
	plug.getValue(value[0]);
	plug = aPlug.child(1);
	plug.getValue(value[1]);
	plug = aPlug.child(2);
	plug.getValue(value[2]);
	double conv = M_PI/180;
	value[0] = value[0] * conv;
	value[1] = value[1] * conv;
	value[2] = value[2] * conv;
	MEulerRotation eul(value[0], value[1], value[2], MEulerRotation::kXYZ);
	double matD[4][4];
	MMatrix mmat = eul.asMatrix();
	mmat.get(matD);

	MFloatVector aPoint(0, 0, 1);
	MFloatMatrix fMat(matD);

	MFloatVector direction = aPoint.operator *(fMat);

	double nValue[3] = {0, 0, 1};

	nValue[0] = direction.x;
	nValue[1] = direction.y;
	nValue[2] = direction.z;

	cValue.set(nValue[0]);
	cValue.operator +=(" ");
	cValue.operator +=(nValue[1]);
	cValue.operator +=(" ");
	cValue.operator +=(nValue[2]);

	return cValue;
}

//MString web3dExportMethods::getMFRotation(MString sValue, MFnDependencyNode &depNode)
//{
//	return getSFRotation(sValue, depNode);
//}

MString web3dExportMethods::getSFString(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);
	aPlug.getValue(cValue);
	MString retString = specCharProcessor(cValue);

	return retString;
}

MString web3dExportMethods::getMFString(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
	for(i=0;i<vLength;i++)
	{
		MPlug dPlug = kvPlug.child(i);
		MString sVal;
		dPlug.getValue(sVal);

		MString dsVal;
		dsVal.set("\"");
		dsVal.operator +=(specCharProcessor(sVal));
		dsVal.operator +=("\"");
		cValue.operator +=(dsVal);

		if(i!=vLength-1) cValue.operator +=("\n");
	}

	return cValue;
}

MString web3dExportMethods::getMFStringNonScript(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue("");
	MPlug kvPlug = depNode.findPlug(sValue);
	MString cString = sValue;
	cString.operator +=("_cc");
	MPlug ccPlug = depNode.findPlug(cString);

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	unsigned int j=0;
	for(i=0;i<vLength;i++)
	{
		MPlug dPlug = kvPlug.elementByPhysicalIndex(i);
		MString sVal;
		dPlug.getValue(sVal);

		MString dsVal;
		dsVal.set("\"");
		dsVal.operator +=(specCharProcessor(sVal));
		dsVal.operator +=("\"");
		cValue.operator +=(dsVal);

		if(i!=vLength-1) cValue.operator +=("\n");
	}

	return cValue;
}

MString web3dExportMethods::getLODRanges(MFnDependencyNode &depNode)
{
	MString rValue("");
	MPlug aPlug = depNode.findPlug("threshold");
	unsigned int length = aPlug.numElements();
	unsigned int i;
	for(i=0;i<length; i++)
	{
		MPlug tPlug = aPlug.elementByLogicalIndex(i);
		float value;
		tPlug.getValue(value);
		MString tString;
		tString.set(value, 5);
		rValue.operator +=(tString);
		if(i!=length-1) rValue.operator +=(" ");
	}
	return rValue;
}

MString web3dExportMethods::getFieldOfView(MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug("horizontalFilmAperture");
	float hAper;
	aPlug.getValue(hAper);

	float focal;
	aPlug = depNode.findPlug("focalLength");
	aPlug.getValue(focal);

	double fov = (0.5 * hAper) / (focal * 0.03937);
	fov = 2.0 * atan (fov);
	fov = 57.29578 * fov; 

	double convVal = M_PI/180;
	fov = fov * convVal;
	
	cValue.set(fov, 5);
    return cValue;
}

MString web3dExportMethods::getLightAttenuation(MFnDependencyNode &depNode)
{
	MString cValue("1 0 0");
//	MStatus stat;
//	MPlug aPlug = depNode.findPlug("attenuation", stat);
//	if(MStatus::kSuccess = stat) 
	return cValue;
}

MString web3dExportMethods::getDirection(MFnDependencyNode &depNode)
{
	MString cValue;
	MPlug aPlug = depNode.findPlug("message");
	MObject thisObj = aPlug.node();
//	MFnDagNode thisDag(thisObj);
//	MObject parentObj = thisDag.parent(0);
//	MFnDependencyNode tform(parentObj);

	MFnLight aLight(thisObj);
	MFloatVector direction = aLight.lightDirection(0, MSpace::kTransform);
	float dirFloat[3];
	direction.get(dirFloat);
	cValue.set(dirFloat[0]);
	cValue.operator +=(" ");
	cValue.operator += (dirFloat[1]);
	cValue.operator +=(" ");
	cValue.operator += (dirFloat[2]);

	return cValue;
}

MString web3dExportMethods::getParentSFRotation(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue;
	MPlug aPlug = depNode.findPlug("message");
	MObject thisObj = aPlug.node();
	MFnDagNode thisDag(thisObj);
	MObject parentObj = thisDag.parent(0);
	MFnDependencyNode tform(parentObj);
	cValue = getSFRotation(sValue, tform);

	return cValue;
}

MString web3dExportMethods::getParentSFVec3f(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue;
	MPlug aPlug = depNode.findPlug("message");
	MObject thisObj = aPlug.node();
	MFnDagNode thisDag(thisObj);
	MObject parentObj = thisDag.parent(0);
	MFnDependencyNode tform(parentObj);
	cValue = getSFVec3f(sValue, tform);
	return cValue;
}

MString web3dExportMethods::getLightRadius(MFnDependencyNode &depNode)
{
	MString cValue;
	MPlug aPlug = depNode.findPlug("centerOfIllumination");
	aPlug.getValue(cValue);
	return cValue;
}

MString	web3dExportMethods::getLightIntensity(MString sValue, MFnDependencyNode &depNode)
{
	MPlug aPlug;
	MString cValue;
	aPlug = depNode.findPlug(sValue);
	float fValue;
	aPlug.getValue(fValue);

	if(fValue < 0) fValue = 0;
	if(fValue > 10) fValue = 10;

	fValue = fValue/10;
	cValue.set(fValue);

	return cValue;
}

MString web3dExportMethods::getRadianAngle(MString sValue, MFnDependencyNode &depNode)
{
	MString cValue;
	MPlug aPlug = depNode.findPlug(sValue);
	aPlug.getValue(cValue);

	return cValue;
}

MFloatVectorArray web3dExportMethods::getComparedFloatVectorArray(MFloatVectorArray normalValues)
{
	MFloatVectorArray compareVal;

	unsigned int i;
	for(i=0;i<normalValues.length();i++)
	{
		float vec1[3];
		normalValues.operator [](i).get(vec1);

		float vec2[3];
		float vec3[3] = {0, 0, 0};
		unsigned int j;
		bool found = false;

		for(j=0;j<compareVal.length(); j++)
		{
			compareVal.operator [](j).get(vec2);
			if(vec1[0] == vec2[0] && vec1[1] == vec2[1] && vec1[2] == vec2[2])
			{
				found = true;
			}
		}
		if(!found)
		{
			MFloatVector newVector(vec1);
			compareVal.append(newVector);
		}
	}
	
	return compareVal;
}

MString			web3dExportMethods::getAudioURLs(MFnDependencyNode &depNode)
{
	MString retString("");
	MPlug filePlug = depNode.findPlug("filename");
	MString fileString;
	filePlug.getValue(fileString);
	if(fileString.operator !=(""))
	{

		MStringArray parts;
		fileString.split('/', parts);
		MString newUrl("\"");

		MString aFileName = parts.operator [](parts.length()-1);
		newUrl.operator +=(aFileName);
		newUrl.operator +=("\"");

		if(!conMedia)
		{
			newUrl.operator +=(" \"");
			newUrl.operator +=(fileString);
			newUrl.operator +=("\"");
		}
		else
		{
			if(audioDir.length() > 0)
			{
				newUrl.operator +=(" \"");
				newUrl.operator +=(audioDir);
				newUrl.operator +=(aFileName);
				newUrl.operator +=("\"");
			}
			if(baseUrl.length() > 0)
			{
				newUrl.operator +=(" \"");
				newUrl.operator +=(baseUrl);
				if(audioDir.length() > 0) newUrl.operator +=(audioDir);
				newUrl.operator +=(aFileName);
				newUrl.operator +=("\"");
			}
		}
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
		{
			retString.set("[ ");
			retString.operator +=(newUrl);
			retString.operator +=(" ]");
		} else retString = newUrl;
	}
	return retString;
}

MString			web3dExportMethods::getInlineURLs(MFnDependencyNode &depNode)
{
	MString retString("");
	MPlug filePlug = depNode.findPlug("url");
	MString fileString;
	filePlug.getValue(fileString);
	if(fileString.operator !=(""))
	{

		MStringArray parts;
		fileString.split('/', parts);
		MString newUrl("\"");

		MString fName = parts.operator [](parts.length()-1);
		MStringArray pieces;
		fName.split('.', pieces);
		unsigned int pLen = pieces.length();
		unsigned int i;

		MString aFileName("");
		for(i=0;i<pLen;i++)
		{
			if(i!=pLen-1)
			{
				aFileName.operator +=(pieces.operator [](i));
				aFileName.operator +=(".");
			}
			else
			{
				switch(exEncoding)
				{
				case X3DVENC:
					aFileName.operator +=("x3dv");
					break;
				case VRML97ENC:
					aFileName.operator +=("wrl");
					break;
				case X3DBENC:
					aFileName.operator +=("x3db");
					break;
				default:
					aFileName.operator +=("x3d");
					break;
				}
			}
		}

		newUrl.operator +=(aFileName);
		newUrl.operator +=("\"");

		if(!conMedia)
		{
			newUrl.operator +=(" \"");
			unsigned int parLen = parts.length();
			for(i=0; i<parLen;i++)
			{
				if(i!= parLen-1) 
				{
					newUrl.operator +=(parts.operator [](i));
					newUrl.operator +=("/");
				}
			}
			newUrl.operator +=(aFileName);
			newUrl.operator +=("\"");
		}
		else
		{
			if(inlineDir.length() > 0)
			{
				newUrl.operator +=(" \"");
				newUrl.operator +=(inlineDir);
				newUrl.operator +=(aFileName);
				newUrl.operator +=("\"");
			}
			if(baseUrl.length() > 0)
			{
				newUrl.operator +=(" \"");
				newUrl.operator +=(baseUrl);
				if(inlineDir.length() > 0) newUrl.operator +=(inlineDir);
				newUrl.operator +=(aFileName);
				newUrl.operator +=("\"");
			}
		}
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
		{
			retString.set("[ ");
			retString.operator +=(newUrl);
			retString.operator +=(" ]");
		} else retString = newUrl;
	}
	return retString;
}

MString			web3dExportMethods::getImageURLs(MFnDependencyNode &depNode, unsigned int msType)
{
	MString retString("");
	MPlug filePlug = depNode.findPlug("fileTextureName");
	MString fileString;
	filePlug.getValue(fileString);
	if(fileString.operator !=(""))
	{
		MStringArray parts;
		fileString.split('/', parts);

		MString aFileName1 = parts.operator [](parts.length()-1);
		MStringArray fParts;
		aFileName1.split('.', fParts);

		MString aFileName = fParts.operator [](0);
		aFileName.operator +=(".");
		unsigned int i;
		for(i=1;i<fParts.length()-1;i++)
		{
			aFileName.operator +=(fParts.operator [](i));
			aFileName.operator +=(".");
		}

		int ltf = 0;
//		bool ltff = false;
		MPlug aPlug;
		aPlug = depNode.findPlug("fChoice");
		aPlug.getValue(ltf);
		switch(ltf)
		{
			case 1:
				aFileName.operator +=("gif");
				break;
			case 2:
				aFileName.operator +=("jpg");
				break;
			case 3:
				aFileName.operator +=("png"); 
				break;
			default:
				aFileName.operator +=(fParts.operator [](fParts.length()-1));
				break;
		}

		MString newUrl("");
		MStringArray nuArray;
		if(useRelURL == true)
		{
			MString tString1;
			tString1.set("\"");
			tString1.operator +=(aFileName);
			tString1.operator +=("\"");
			nuArray.append(tString1);
		}

		if(!conMedia)
		{
			MString tString1;
			tString1.set("\"");
			tString1.operator +=(fileString);
			tString1.operator +=("\"");
			nuArray.append(tString1);
		}
		else
		{
			if(imageDir.length() > 0 && useRelURLW == true)
			{
				MString tString1;
				tString1.set("\"");
				tString1.operator +=(imageDir);
				tString1.operator +=(aFileName);
				tString1.operator +=("\"");
				nuArray.append(tString1);
			}

			if(baseUrl.length() > 0)
			{
				MString tString1;
				tString1.set("\"");
				tString1.operator +=(baseUrl);
				if(imageDir.length() > 0) tString1.operator +=(imageDir);
				tString1.operator +=(aFileName);
				tString1.operator +=("\"");
				nuArray.append(tString1);
			}
		}
		unsigned int z;
		for(z=0;z<nuArray.length();z++)
		{
			newUrl.operator +=(nuArray.operator [](z));
			if(z != nuArray.length()-1) newUrl.operator +=(" ");
		}

		if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
		{
			retString.set("[ ");
			retString.operator +=(newUrl);
			retString.operator +=(" ]");
		} else retString = newUrl;
	}
	return retString;
}

MStringArray web3dExportMethods::getFieldNamesTexture(MFnDependencyNode &depNode, MString textureType)
{
	MStringArray newStringArray;
	if(textureType.operator ==(msPixelTexture))
	{
		newStringArray.append("image");
	}
	else if(textureType.operator ==(msImageTexture))
	{
		newStringArray.append("url");
	}
	else if(textureType.operator ==(msMovieTexture))
	{
		newStringArray.append("loop");
		if(exEncoding != VRML97ENC) newStringArray.append("resumeTime");
		if(exEncoding != VRML97ENC) newStringArray.append("pauseTime");
		newStringArray.append("speed");
		newStringArray.append("startTime");
		newStringArray.append("stopTime");
		newStringArray.append("url");
	}
	newStringArray.append("repeatS");
	newStringArray.append("repeatT");
	return newStringArray;
}

MStringArray web3dExportMethods::getFieldValuesTexture(MFnDependencyNode &depNode, MString textureType)
{
	MStringArray newStringArray;
	MStatus nStat;
	MPlug aPlug;
	MString value;
	if(textureType.operator ==(msPixelTexture))
	{
		//newStringArray.append(extractPixelValues(depNode));
	}
	else if(textureType.operator ==(msImageTexture))
	{
		MString urlData = getImageURLs(depNode, 0);
		newStringArray.append(urlData);
	}
	else if(textureType.operator ==(msMovieTexture))
	{
		MString mloop("FALSE");
		if(exEncoding == X3DENC || exEncoding == X3DBENC) mloop.set("false");
		mloop = getSFBool("loop", depNode);
		if(exEncoding == X3DENC || exEncoding == X3DBENC)
		{
			if(mloop.operator ==("FALSE")) mloop.set("");
		}
		else
		{
			if(mloop.operator == ("false")) mloop.set("");
		}
		newStringArray.append(mloop);

		MString oData("");
		if(exEncoding != VRML97ENC)
		{
			oData = getSFTime("resumeTime", depNode);
			if(oData.operator == ("0")) oData.set("");
			newStringArray.append(oData);
		} else newStringArray.append("");

		oData.set("");
		if(exEncoding != VRML97ENC)
		{
			oData = getSFTime("pauseTime", depNode);
			if(oData.operator == ("0")) oData.set("");
			newStringArray.append(oData);
		} else newStringArray.append("");

		oData.set("");
		oData = getSFTime("speed", depNode);
		if(oData.operator == ("1")) oData.set("");
		newStringArray.append(oData);
 
		oData.set("");
		oData = getSFTime("startTime", depNode);
		if(oData.operator == ("0")) oData.set("");
		newStringArray.append(oData);

		oData.set("");
		oData = getSFTime("stopTime", depNode);
		if(oData.operator == ("0")) oData.set("");
		newStringArray.append(oData);

		MString urlData = getImageURLs(depNode, 1);
		newStringArray.append(urlData);
	}


	MStringArray nodeNameParts;
	char splitter2 = '_';
	depNode.name().split(splitter2, nodeNameParts);

	bool isExternal = true;
	bool useDefaultWrap = true;

	if(nodeNameParts.length() > 1)
	{
		if(nodeNameParts.operator [](nodeNameParts.length()-2) == "rawkee" && nodeNameParts.operator [](nodeNameParts.length()-1) == "export")
		{
			if(exEncoding == X3DENC || exEncoding == X3DBENC)
			{
				newStringArray.append("true");
				newStringArray.append("true");
			}
			else
			{
				newStringArray.append("TRUE");
				newStringArray.append("TRUE");
			}
			isExternal = false;
			useDefaultWrap = false;
		}
	}

	if(isExternal)
	{
		MPlug UVPlug = depNode.findPlug("uvCoord");
		MItDependencyGraph depIt(UVPlug, MFn::kPlace2dTexture, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);

		while(!depIt.isDone() && useDefaultWrap != false)
		{
			
			MObject pObj = depIt.thisNode();
			MFnDependencyNode pDepFn(pObj);
			bool isWrapU;
			bool isWrapV;
			MPlug uRep = pDepFn.findPlug("wrapU");
			uRep.getValue(isWrapU);

			if(isWrapU)
			{
				if(exEncoding == X3DENC || exEncoding == X3DBENC) newStringArray.append("true");
				else newStringArray.append("TRUE");
			}
			else
			{
				if(exEncoding == X3DENC || exEncoding == X3DBENC) newStringArray.append("false");
				else newStringArray.append("FALSE");
			}

			MPlug vRep = pDepFn.findPlug("wrapV");
			vRep.getValue(isWrapV);

			if(isWrapV)
			{
				if(exEncoding == X3DENC || exEncoding == X3DBENC) newStringArray.append("true");
				else newStringArray.append("TRUE");
			}
			else
			{
				if(exEncoding == X3DENC || exEncoding == X3DBENC) newStringArray.append("false");
				else newStringArray.append("FALSE");
			}

			useDefaultWrap = false;
			
			depIt.next();
		}
	}

	if(useDefaultWrap)
	{
			if(exEncoding == X3DENC || exEncoding == X3DBENC)
			{
				newStringArray.append("true");
				newStringArray.append("true");
			}
			else
			{
				newStringArray.append("TRUE");
				newStringArray.append("TRUE");
			}
	}
	return newStringArray;
}

MImage web3dExportMethods::getImageObject(MFnDependencyNode &depNode)
{
//	MPlug aPlug;
//	MStatus nStat;
//	aPlug = depNode.findPlug("fileTextureName", &nStat);
//	MObject textureNode = aPlug.node();

	MImage fImage;
	fImage.readFromTextureNode(depNode.object());
/*
	bool adjTex;
	MPlug adjPlug = depNode.findPlug("adjsize");
	adjPlug.getValue(adjTex);

	int xw = 0;
	MPlug xwp = depNode.findPlug("imgdimw");
	xwp.getValue(xw);

	int xh = 0;
	MPlug xhp = depNode.findPlug("imgdimh");
	xhp.getValue(xh);

	if(adjTex)
	{
		MStatus iStat = fImage.resize(xw, xh, false);
	}
*/
	return fImage;
}

int web3dExportMethods::getPixelLength(MFnDependencyNode &depNode)
{
	int pLen = 2;
	MPlug pLenPlug = depNode.findPlug("pLength");
	pLenPlug.getValue(pLen);
	return pLen + 1;
}

MString web3dExportMethods::extractPixelValues(MFnDependencyNode &depNode)
{
	MString pixels;
	
	MPlug aPlug;
	MStatus nStat;
	aPlug = depNode.findPlug("fileTextureName", &nStat);
	MObject textureNode = aPlug.node();

	MImage fImage;
	fImage.readFromTextureNode(textureNode);

	bool adjTex;
	MPlug adjPlug = depNode.findPlug("adjsize");
	adjPlug.getValue(adjTex);

	int xw = 0;
	MPlug xwp = depNode.findPlug("imgdimw");
	xwp.getValue(xw);

	int xh = 0;
	MPlug xhp = depNode.findPlug("imgdimh");
	xhp.getValue(xh);

	if(adjTex)
	{
		MStatus iStat = fImage.resize(xw, xh, false);
	}

	int pLen = 2;
	MPlug pLenPlug = depNode.findPlug("pLength");
	pLenPlug.getValue(pLen);
	pLen = pLen + 1;

	unsigned int myWidth;
	unsigned int myHeight;
	MStatus status = fImage.getSize(myWidth, myHeight);

	MString mh;
	mh.set(myHeight);

	pixels.set(myWidth);
	pixels.operator +=(" ");
	pixels.operator +=(mh);
	pixels.operator +=(" ");
	pixels.operator +=(pLen);

	unsigned char* myColor = fImage.pixels();
	unsigned int i;
	unsigned int j;

	unsigned char rValue, gValue, bValue, aValue;
	char valueBuffer[17];

	cout << "Writing Out Pixel Texture" << endl;
	cout << "Please Be Patient" << endl;

	double denom = myHeight;

	unsigned int rlimit = 0;
	for(j=0; j<myHeight; j++)
	{
		for(i=0; i<myWidth; i++)
		{
			rValue = myColor[j * myWidth * 4 + i * 4 + 0];
			gValue = myColor[j * myWidth * 4 + i * 4 + 1];
			bValue = myColor[j * myWidth * 4 + i * 4 + 2];
			aValue = myColor[j * myWidth * 4 + i * 4 + 3];
			if(pLen==1) sprintf(valueBuffer," 0x%02X",rValue);
			else if(pLen==2) sprintf(valueBuffer," 0x%02X%02X",rValue,gValue);
			else if(pLen==3) sprintf(valueBuffer," 0x%02X%02X%02X",rValue,gValue,bValue);
			else sprintf(valueBuffer," 0x%02X%02X%02X%02X",rValue,gValue,bValue,aValue);
			pixels.operator +=(valueBuffer);
			if(rlimit == 7)
			{
				if(j < myHeight-1) pixels.operator +=("\n");
				else if(i < myWidth-1) pixels.operator +=("\n");
				rlimit = 0;
			}
			else
			{
				rlimit = rlimit+1;
			}

		}
		double perc = j/denom;
		perc = perc * 100;

		cout << "Pixel Texture Export - "<< perc << "% Complete!" << endl;
	}
	return pixels;
}

MStringArray	web3dExportMethods::getAudioClipFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//description
	MString holdStr = getSFString("description", depNode);
	MString desStr("");
	if(holdStr.operator !=("") && holdStr.operator !=(" "))
	{
		if(exEncoding != X3DENC) desStr.set("\"");
		desStr.operator +=(holdStr);
		if(exEncoding != X3DENC) desStr.operator +=("\"");
	}
	tArray.append(desStr);

	//loop
	desStr.set("FALSE");
	if(exEncoding == X3DENC || exEncoding == X3DBENC) desStr.set("false");
	desStr = getSFBool("loop", depNode);
	if(exEncoding == X3DENC || exEncoding == X3DBENC)
	{
		if(desStr.operator ==("FALSE")) desStr.set("");
	}
	else
	{
		if(desStr.operator == ("false")) desStr.set("");
	}
	tArray.append(desStr);

	//pauseTime
	desStr.set("0");
	desStr = getSFTime("pauseTime", depNode);
	if(desStr.asFloat() == 0) desStr.set("");
	tArray.append(desStr);

	//pitch
	desStr.set("1.0");
	desStr = getSFFloat("pitch", depNode);
	if(desStr.asFloat() == 1.0) desStr.set("");
	tArray.append(desStr);

	//resumeTime
	desStr.set("0");
	desStr = getSFTime("resumeTime", depNode);
	if(desStr.asFloat() == 0) desStr.set("");
	tArray.append(desStr);

	//startTime
	desStr.set("0");
	desStr = getSFTime("startTime", depNode);
	if(desStr.asFloat() == 0) desStr.set("");
	tArray.append(desStr);

	//stopTime
	desStr.set("0");
	desStr = getSFTime("stopTime", depNode);
	if(desStr.asFloat() == 0) desStr.set("");
	tArray.append(desStr);

	//url;
	desStr.set("");
	desStr = getAudioURLs(depNode);
	if(desStr.operator ==(" ")) desStr.set("");
	tArray.append(desStr);

	return tArray;
}

MStringArray	web3dExportMethods::getTransFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//center
	MString tString("0 0 0");
	MString tString2 = getSFVec3f("rotatePivot", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//rotation
	tString.set("0 0 1 0");
	tString2 = getSFRotation("rotate", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");
	
	//scale - this will need to change if a
	//        method for getting the scaleOrientation is
	//        implemented as scale and scaleOrientation are
	//        closely related.
	tString.set("1 1 1");
	tString2 = getSFVec3f("scale", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//scaleOrientation
//	tString.set("0 0 1 0");
//	tString2 = getSFRotation("shear", depNode);
//	if(tString2.operator !=(tString)) tArray.append(tString2);
//	else tArray.append("");
	tArray.append("");

	//translation
	tString.set("0 0 0");
	tString2 = getSFVec3f("translate", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getHAnimHumanoidFieldValues(MFnDagNode &dagNode, unsigned int subNode)
{
	MStringArray tArray;

	tArray.append("");

	//center
	MString tString("0 0 0");
	MString tString2 = getSFVec3f("rotatePivot", dagNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//rotation
	tString.set("0 0 1 0");
	tString2 = getSFRotation("rotate", dagNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");
	
	//scale - this will need to change if a
	//        method for getting the scaleOrientation is
	//        implemented as scale and scaleOrientation are
	//        closely related.
	tString.set("1 1 1");
	tString2 = getSFVec3f("scale", dagNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//scaleOrientation
//	tString.set("0 0 1 0");
//	tString2 = getSFRotation("shear", depNode);
//	if(tString2.operator !=(tString)) tArray.append(tString2);
//	else tArray.append("");
	tArray.append("");

	//translation
	tString.set("0 0 0");
	tString2 = getSFVec3f("translate", dagNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

//MStringArray	web3dExportMethods::getJointFieldValues(MFnDependencyNode &depNode, unsigned int subNode, MString humanName, double pVal[])
//MStringArray	web3dExportMethods::getJointFieldValues(MFnIkJoint ikjNode, unsigned int subNode, MString humanName, double pVal[])
MStringArray	web3dExportMethods::getJointFieldValues(MObject mObj, unsigned int subNode, MString humanName, double pVal[])
{
	MFnIkJoint ikjNode(mObj);

	MStringArray tArray;
	MFnDependencyNode depNode(ikjNode.object());
	MString gName("hanim_");
	gName.operator +=(depNode.name());
//	MFnDependencyNode ghostNode = getMyDepNode(gName);
	MFnDependencyNode ghostNode(getMyDepNodeObj(gName));

	//name - temporary addition Dec 6, 2005
	MString tStringha("\"");
	tStringha.operator +=(humanName);
	tStringha.operator +=("_x_");
	tStringha.operator +=(depNode.name());
	tStringha.operator +=("\"");
	tArray.append(tStringha);

	//center
	MString tString("0 0 0");
	MString tString2("");
	if(ghostNode.name().operator ==(gName)) tString2 = getSFVec3f("rotatePivot", ghostNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//rotation
	tString.set("0 0 1 0");
	tString2.set("");
	if(ghostNode.name().operator ==(gName)) tString2 = getSFRotationHAnim("rotate", ghostNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");
	
	//scale - this will need to change if a
	//        method for getting the scaleOrientation is
	//        implemented as scale and scaleOrientation are
	//        closely related.
	tString.set("1 1 1");
	tString2.set("");
	if(ghostNode.name().operator ==(gName)) tString2 = getSFVec3f("scale", ghostNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//scaleOrientation
//	tString.set("0 0 1 0");
//	tString2 = getSFRotation("shear", depNode);
//	if(tString2.operator !=(tString)) tArray.append(tString2);
//	else tArray.append("");
	tArray.append("");

	//translation
	tString.set("0 0 0");
//	MVector cenVec = ikjNode.translation(MSpace::kWorld);
//	tString2.set("");
//	tString2.operator +=(cenVec.x);
//	tString2.operator +=(" ");
//	tString2.operator +=(cenVec.y);
//	tString2.operator +=(" ");
//	tString2.operator +=(cenVec.z);
	tString2.set("");
//	if(ghostNode.name().operator ==(gName)) tString2 = getSFVec3fHAnim("translate", ghostNode, pVal);
	if(ghostNode.name().operator ==(gName)) tString2 = getSFVec3fHAnim("hanimCenter", ghostNode, pVal);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getSiteFieldValues(MFnDependencyNode &depNode, unsigned int subNode, MString humanName, double pVal[], bool nsHAnim)
{
	MStringArray tArray;

	//name - temporary addition Dec 6, 2005
	MString tStringha(humanName);
	if(nsHAnim)
	{
		tStringha.operator +=("_x_");
		tStringha.operator +=(depNode.name());
		tStringha.operator +=("_pt");
	}
	else tStringha.operator =(depNode.name());
	tArray.append(tStringha);

	//center
	MString tString("0 0 0");
	MString tString2 = getSFVec3f("rotatePivot", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//rotation
	tString.set("0 0 1 0");
	tString2 = getSFRotation("rotate", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");
	
	//scale - this will need to change if a
	//        method for getting the scaleOrientation is
	//        implemented as scale and scaleOrientation are
	//        closely related.
	tString.set("1 1 1");
	tString2 = getSFVec3f("scale", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//scaleOrientation
//	tString.set("0 0 1 0");
//	tString2 = getSFRotation("shear", depNode);
//	if(tString2.operator !=(tString)) tArray.append(tString2);
//	else tArray.append("");
	tArray.append("");

	//translation
	tString.set("0 0 0");
//	MVector cenVec = ikjNode.translation(MSpace::kWorld);
//	tString2.set("");
//	tString2.operator +=(cenVec.x);
//	tString2.operator +=(" ");
//	tString2.operator +=(cenVec.y);
//	tString2.operator +=(" ");
//	tString2.operator +=(cenVec.z);
	tString2 = getSFVec3fHAnim("translate", depNode, pVal);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getAnchorFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//description
	MString holdStr = getSFString("description", depNode);
	MString desStr("");
	if(holdStr.operator !=("") && holdStr.operator !=(" "))
	{
		if(exEncoding == X3DVENC) desStr.set("\"");
		desStr.operator +=(holdStr);
		if(exEncoding == X3DVENC) desStr.operator +=("\"");
	}
	tArray.append(desStr);

	//parameter
	MString paraStr("");
	holdStr.set("");
	holdStr = getMFStringNonScript("parameter", depNode);
	if(holdStr.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) paraStr.operator +=("[ ");
		paraStr.operator +=(holdStr);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) paraStr.operator +=(" ]");
	}
	tArray.append(paraStr);

	//url
	MString urlStr("");
	holdStr.set("");
	holdStr = getMFStringNonScript("url", depNode);
	if(holdStr.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) urlStr.operator +=("[ ");
		urlStr.operator +=(holdStr);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) urlStr.operator +=(" ]");
	}
	tArray.append(urlStr);

	return tArray;
}

MStringArray	web3dExportMethods::getSoundFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	
	//direction
	MString tString("0 0 1");
	MString tString2 = getDirection("direction", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//intensity
	tString.set("1");
	tString2 = getSFFloat("intensity", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//location
	tString.set("0 0 0");
	tString2 = getSFVec3f("location", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//maxBack
	tString.set("10");
	tString2 = getSFFloat("maxBack", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//maxFront
	tString.set("10");
	tString2 = getSFFloat("maxFront", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//minBack
	tString.set("1");
	tString2 = getSFFloat("minBack", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//minFront
	tString.set("1");
	tString2 = getSFFloat("minFront", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//priority
	tString.set("0");
	tString2 = getSFFloat("priority", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//spatialize
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("spatialize", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getTextureTransformFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	if(depNode.name() == "")
	{
		tArray.append("");
		tArray.append("");
		tArray.append("");
		tArray.append("");
	}
	else
	{
		tArray.append("");

		MPlug aPlug1 = depNode.findPlug("rotateUV");
		double rotation;
		aPlug1.getValue(rotation);
		rotation = rotation * (360/M_PI);
		MString rotString;
		rotString.set(rotation, 5);
		if(rotString == "0") rotString.set("");
		tArray.append(rotString);

		MPlug aPlug2 = depNode.findPlug("coverage");
		MPlug aPlug2u = aPlug2.child(0);
		MPlug aPlug2v = aPlug2.child(1);
		float floatU;
		float floatV;
		aPlug2u.getValue(floatU);
		aPlug2v.getValue(floatV);
		MString valString;
		valString.set(floatU);
		valString.operator +=(" ");
		valString.operator +=(floatV);
		if(valString == "1 1") valString.set("");
		tArray.append(valString);

		MPlug aPlug3 = depNode.findPlug("offset");
		aPlug2u = aPlug3.child(0);
		aPlug2v = aPlug3.child(1);
		aPlug2u.getValue(floatU);
		aPlug2v.getValue(floatV);

		MString valString2;
		valString2.set(floatU);
		valString2.operator +=(" ");
		valString2.operator +=(floatV);
		if(valString2 == "0 0") valString2.set("");
		tArray.append(valString2);
	}
	return tArray;
}

MStringArray	web3dExportMethods::getMaterialFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	MPlug mColor = depNode.findPlug("color");
	MPlug mDiffuse = depNode.findPlug("diffuse");
	MPlug mAmbient = depNode.findPlug("ambientColor");
	MPlug mEmissive = depNode.findPlug("incandescence");

	MPlugArray mShininess;
	mShininess.append(depNode.findPlug("eccentricity"));
	mShininess.append(depNode.findPlug("specularRollOff"));
	mShininess.append(depNode.findPlug("cosinePower"));
	mShininess.append(depNode.findPlug("roughness"));
	mShininess.append(depNode.findPlug("highlightSize"));

	MPlug mTransparency = depNode.findPlug("transparency");


	setAmbientIntensity(mAmbient, tArray);
	setDiffuseColor(mColor, mDiffuse, tArray);
	setEmissiveColor(mEmissive, tArray);
	setShininess(depNode, mShininess, tArray);

	if(depNode.typeName() != "lambert")
	{
		MPlug mSpecular = depNode.findPlug("specularColor");
		setSpecularColor(mSpecular, tArray);
	}
	else tArray.append("");

	setTransparency(mTransparency, tArray);

	return tArray;
}

MStringArray	web3dExportMethods::getShapeFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	tArray.append("");

	return tArray;
}
MStringArray	web3dExportMethods::getProxFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//enabled
	MString tString;
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");

	MString tString2 = getSFBool("enabled", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//center - transform position field
	tString.set("0 0 0");
	tString2 = getSFVec3f("proxCenter", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//size - transform scale field
	tString.set("1 1 1");
	tString2 = getSFVec3f("proxSize", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getVisFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//enabled
	MString tString;
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");

	MString tString2 = getSFBool("enabled", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//center - transform position field
	tString.set("0 0 0");
	tString2 = getSFVec3f("visCenter", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//size - transform scale field
	tString.set("1 1 1");
	tString2 = getSFVec3f("visSize", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getTiSFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//cycleInterval
	MString tString("1");
	MString tString2 = getSFFloat("cycleInterval", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//enabled
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("enabled", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//loop
	tString.set("FALSE");
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("false");
	tString2 = getSFBool("loop", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	if(exEncoding != VRML97ENC)
	{
		//pauseTime
		tString.set("0");
		tString2 = getSFFloat("pauseTime", depNode);
		if(tString2.operator !=(tString)) tArray.append(tString2);
		else tArray.append("");

		//resumeTime
		tString.set("0");
		tString2 = getSFFloat("resumeTime", depNode);
		if(tString2.operator !=(tString)) tArray.append(tString2);
		else tArray.append("");
	}

	//startTime
	tString.set("0");
	tString2 = getSFFloat("startTime", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//stopTime
	tString.set("0");
	tString2 = getSFFloat("stopTime", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}
MStringArray	web3dExportMethods::getToSFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	
	if(exEncoding != VRML97ENC)
	{
		//description
		MString holdStr = getSFString("description", depNode);
		MString desStr("");
		if(holdStr.operator !=("") && holdStr.operator !=(" "))
		{
			if(exEncoding == X3DVENC) desStr.set("\"");
			desStr.operator +=(holdStr);
			if(exEncoding == X3DVENC) desStr.operator +=("\"");
		}
		tArray.append(desStr);
	}

	//enabled
	MString tString;
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	MString tString2 = getSFBool("enabled", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getGamepadSFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	
	//description
	MString holdStr = getSFString("x3dName", depNode);
	MString desStr("");
	if(holdStr.operator !=("") && holdStr.operator !=(" "))
	{
		if(exEncoding == X3DVENC) desStr.set("\"");
		desStr.operator +=(holdStr);
		if(exEncoding == X3DVENC) desStr.operator +=("\"");
	}
	tArray.append(desStr);

	//enabled
	MString tString;
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	MString tString2 = getSFBool("enabled", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getCylSensorFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//autoOffset
	MString tString;
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	MString tString2 = getSFBool("autoOffset", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	if(exEncoding != VRML97ENC)
	{
		//description
		MString holdStr = getSFString("description", depNode);
		MString desStr("");
		if(holdStr.operator !=("") && holdStr.operator !=(" "))
		{
			if(exEncoding == X3DVENC) desStr.set("\"");
			desStr.operator +=(holdStr);
			if(exEncoding == X3DVENC) desStr.operator +=("\"");
		}
		tArray.append(desStr);
	}

	//diskAngle
	double diskVal = M_PI/12;
	tString.set(diskVal);
	tString2 = getSFFloat("diskAngle", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//enabled
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("enabled", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//maxAngle
	double degVal = -1;
	tString.set(degVal);
	tString2 = getSFFloat("maxAngle", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//minAngle
	tString.set("0");
	tString2 = getSFFloat("minAngle", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//offset
	tString.set("0");
	tString2 = getSFFloat("offset", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getPlaneSensorFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	//autoOffset
	MString tString;
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	MString tString2 = getSFBool("autoOffset", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	if(exEncoding != VRML97ENC)
	{
		//description
		MString holdStr = getSFString("description", depNode);
		MString desStr("");
		if(holdStr.operator !=("") && holdStr.operator !=(" "))
		{
			if(exEncoding == X3DVENC) desStr.set("\"");
			desStr.operator +=(holdStr);
			if(exEncoding == X3DVENC) desStr.operator +=("\"");
		}
		tArray.append(desStr);
	}

	//enabled
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("enabled", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//maxPosition 888 999
	tString.set("-1 -1");
	tString2 = getSFVec2f("maxPosition", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//minPosition
	tString.set("0 0");
	tString2 = getSFVec2f("maxPosition", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//offset
	tString.set("0 0 0");
	tString2 = getSFVec3f("offset", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getSphereSensorFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//autoOffset
	MString tString;
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	MString tString2 = getSFBool("autoOffset", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	if(exEncoding != VRML97ENC)
	{
		//description
		MString holdStr = getSFString("description", depNode);
		MString desStr("");
		if(holdStr.operator !=("") && holdStr.operator !=(" "))
		{
			if(exEncoding == X3DVENC) desStr.set("\"");
			desStr.operator +=(holdStr);
			if(exEncoding == X3DVENC) desStr.operator +=("\"");
		}
		tArray.append(desStr);
	}

	//enabled
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("enabled", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//offset
	tString.set("0 0 1 0");
	tString2 = getSFRotation("offset", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getKeySensorFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	//enabled
	MString tString;
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	MString tString2 = getSFBool("enabled", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getLoadSensorFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	//enabled
	MString tString;
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	MString tString2 = getSFBool("enabled", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//timeOut
	tString.set("0");
	tString2 = getSFTime("timeOut", depNode);
	if(tString2.operator ==("0")) tString.set("");
	else tString = tString2;
	tArray.append(tString);
	
	return tArray;
}

MStringArray	web3dExportMethods::getStringSensorFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	//deletionAllowed
	MString tString;
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	MString tString2 = getSFBool("deletionAllowed", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//enabled
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("enabled", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getNIFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//avatarSize
	MString tString("0.25 1.6 0.75");
	MString tString2 = getSFVec3f("avatarSize", depNode);
	if(tString2.operator !=(tString))
	{
		MString asStr;
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) asStr.operator +=("[ ");
		asStr.operator +=(tString2);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) asStr.operator +=(" ]");
		tArray.append(asStr);
	}
	else tArray.append("");

	//headlight
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("headlight", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//speed
	tString.set("1.0");
	tString2 = getSFFloat("speed", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	if(exEncoding != VRML97ENC)
	{
		//transitionType
		tString2 = getMFStringNonScript("transitionType", depNode);
		MString ttStr;
		if(tString2.operator !=(msEmpty))
		{
			if(exEncoding == X3DVENC) ttStr.operator +=("[ ");
			ttStr.operator +=(tString2);
			if(exEncoding == X3DVENC) ttStr.operator +=(" ]");
		}
		tArray.append(ttStr);
	}

	//type
	tString2 = getMFStringNonScript("type", depNode);

	MStringArray vrmlCheck;
	tString2.split(' ', vrmlCheck);
	unsigned int vcLen = vrmlCheck.length();
	unsigned int i;

	MString tyStr("");
	MString compStr("");
	if(exEncoding == X3DVENC || exEncoding == VRML97ENC) tyStr.operator +=("[ ");
	for(i=0;i<vcLen;i++)
	{
		MString lookStr("\"LOOKAT\"");
		MString cLookStr = specCharProcessor(lookStr);
		if(vrmlCheck.operator [](i) != cLookStr)
		{
			compStr.operator +=(vrmlCheck.operator [](i));
			unsigned int j = i+1;
			if(i!=vcLen-1)
			{
				if(vrmlCheck.operator [](j) != cLookStr) compStr.operator +=(" ");
			}
		}
	}
	if(exEncoding != VRML97ENC) compStr = tString2;
	tyStr.operator +=(compStr);
	if(exEncoding == X3DVENC || exEncoding == VRML97ENC) tyStr.operator +=(" ]");
	tArray.append(tyStr);

	//visibilityLimit
	tString.set("0.0");
	tString2 = getSFFloat("visibilityLimit", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}
MStringArray	web3dExportMethods::getWIFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//title
	MString titStr("");
	MString holdStr = getSFString("title", depNode);
	if(holdStr.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) titStr.operator +=("\"");
		titStr.operator +=(holdStr);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) titStr.operator +=("\"");
	}
	tArray.append(titStr);

	//info
	MString infoStr("");
	holdStr.set("");
	holdStr = getMFStringNonScript("info", depNode);
	if(holdStr.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) infoStr.operator +=("[ ");
		infoStr.operator +=(holdStr);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) infoStr.operator +=(" ]");
	}
	tArray.append(infoStr);
	return tArray;
}

MStringArray	web3dExportMethods::getPIFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	MString keyStr("");
	MString kValue = getMFFloatNonScript("key", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=("[ ");
		keyStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=(" ]");
	}
	tArray.append(keyStr);

	MString keyVStr("");
	kValue.set("");
	kValue = getMFVec3fNonScript("keyValue", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=("[ ");
		keyVStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=(" ]");
	}
	tArray.append(keyVStr);

	return tArray;
}

MStringArray	web3dExportMethods::getOIFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	MString keyStr("");
	MString kValue = getMFFloatNonScript("key", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=("[ ");
		keyStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=(" ]");
	}
	tArray.append(keyStr);

	MString keyVStr("");
	kValue.set("");
	kValue = getMFRotationNonScript("keyValue", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=("[ ");
		keyVStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=(" ]");
	}
	tArray.append(keyVStr);

	return tArray;
}

MStringArray	web3dExportMethods::getColorIFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	MString keyStr("");
	MString kValue = getMFFloatNonScript("key", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=("[ ");
		keyStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=(" ]");
	}
	tArray.append(keyStr);

	MString keyVStr("");
	kValue.set("");
	kValue = getMFColorNonScript("keyValue", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=("[ ");
		keyVStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=(" ]");
	}
	tArray.append(keyVStr);

	return tArray;
}

MStringArray	web3dExportMethods::getCoordIFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	MString keyStr("");
	MString kValue = getMFFloatNonScript("key", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=("[ ");
		keyStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=(" ]");
	}
	tArray.append(keyStr);

	MString keyVStr("");
	kValue.set("");
	kValue = getMultipleMFVec3f("keyValue", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=("[ ");
		keyVStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=(" ]");
	}
	tArray.append(keyVStr);

	return tArray;
}

MStringArray	web3dExportMethods::getScalarIFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	MString keyStr("");
	MString kValue = getMFFloatNonScript("key", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=("[ ");
		keyStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=(" ]");
	}
	tArray.append(keyStr);

	MString keyVStr("");
	kValue.set("");
	kValue = getMFFloatNonScript("keyValue", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=("[ ");
		keyVStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=(" ]");
	}
	tArray.append(keyVStr);

	return tArray;
}

MStringArray	web3dExportMethods::getNormalIFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	MString keyStr("");
	MString kValue = getMFFloatNonScript("key", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=("[ ");
		keyStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=(" ]");
	}
	tArray.append(keyStr);

	MString keyVStr("");
	kValue.set("");
	kValue = getMultipleMFVec3f("keyValue", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=("[ ");
		keyVStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=(" ]");
	}
	tArray.append(keyVStr);

	return tArray;
}

MStringArray	web3dExportMethods::getBoolSFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	MString keyStr("");
	MString kValue = getMFFloatNonScript("key", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=("[ ");
		keyStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=(" ]");
	}
	tArray.append(keyStr);

	MString keyVStr("");
	kValue.set("");
	kValue = getMFBoolNonScript("keyValue", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=("[ ");
		keyVStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=(" ]");
	}
	tArray.append(keyVStr);

	return tArray;
}

MStringArray	web3dExportMethods::getIntSFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	MString keyStr("");
	MString kValue = getMFFloatNonScript("key", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=("[ ");
		keyStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyStr.operator +=(" ]");
	}
	tArray.append(keyStr);

	MString keyVStr("");
	kValue.set("");
	kValue = getMFInt32NonScript("keyValue", depNode);
	if(kValue.operator !=(""))
	{
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=("[ ");
		keyVStr.operator +=(kValue);
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC) keyVStr.operator +=(" ]");
	}
	tArray.append(keyVStr);

	return tArray;
}

MStringArray	web3dExportMethods::getBoolToggleFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	MString tString("FALSE");
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("false");
	MString tString2 = getSFBool("toggle", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");
	return tArray;
}

MStringArray	web3dExportMethods::getIntTriggerFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	MString tString("-1");
	MString tString2 = getSFInt32("integerKey", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");
	return tArray;
}

MStringArray	web3dExportMethods::getScriptFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	//directOutput
	MString tString("FALSE");
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("false");
	MString tString2 = getSFBool("directOutput", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//mustEvaluate
	tString2 = getSFBool("mustEvaluate", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//URL
	MStringArray remoteURLs = getScriptRemoteURLs(depNode);
	MStringArray localURLs;
	if(exEncoding != X3DENC) localURLs = getScriptLocalURLs(depNode);

	MStringArray totalURLs;

	MString urlString("");
	unsigned int i;
	unsigned int j = remoteURLs.length();
	for(i=0;i<j;i++)
	{
		MString remStr("\"");
		remStr.operator +=(remoteURLs.operator [](i));
		remStr.operator +=("\"");
		totalURLs.append(remStr);
	}

	//binary script issues begin here
	j = localURLs.length();
	for(i=0;i<j;i++)
	{
		MString locStr("\"");
		
		if(exEncoding == X3DBENC)
		{
			locStr.operator +=(depNode.name());
			locStr.operator +=("_");
			MString snumStr;
			snumStr.set(i);
			locStr.operator +=(snumStr);
			locStr.operator +=(".js");
		}
		else
		{
		
			locStr.operator +=(localURLs.operator [](i));
		
		}
		
		locStr.operator +=("\"");
		totalURLs.append(locStr);
	}
	//
	j = totalURLs.length();
	

	if(exEncoding == X3DVENC || exEncoding == VRML97ENC && j>1) urlString.operator +=("[ ");
	for(i=0;i<j;i++)
	{
		urlString.operator +=(totalURLs.operator [](i));
		if(i!=j-1) urlString.operator +=("\n");
	}
	if(exEncoding == X3DVENC || exEncoding == VRML97ENC && j>1) urlString.operator +=(" ]");

	tArray.append(urlString);

	return tArray;
}

MStringArray	web3dExportMethods::getGroupFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	tArray.append("");
	return tArray;
}

MStringArray	web3dExportMethods::getBillboardFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	//axisOfRotation
	MString tString("0 0 0");
	MString tStringA("0 1 0");
	MString tString2 = getSFVec3f("axisOfRotation", depNode);
	if(tString2.operator !=(tString) && tString2.operator !=(tStringA)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getSwitchFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	MString tString("-1");
	MString tString2 = getSFInt32("whichChoice", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}
MStringArray	web3dExportMethods::getCollisionFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
//	if(exEncoding != VRML97ENC)
//	{
		MString tString;
		if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
		else tString.set("TRUE");
		MString tString2 = getSFBool("enabled", depNode);
//		MString tString2 = getSFBool("collide", depNode);
		if(tString2.operator !=(tString)) tArray.append(tString2);
		else tArray.append("");
//	}
	return tArray;
}
MStringArray	web3dExportMethods::getLODFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	//center
	MString tString("0 0 0");
	MString tString2 = getSFVec3f("rotatePivot", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//range
	MString ranStr;
	if(exEncoding == X3DVENC || exEncoding == VRML97ENC) ranStr.operator +=("[ ");
	ranStr.operator +=(getLODRanges(depNode));
	if(exEncoding == X3DVENC || exEncoding == VRML97ENC) ranStr.operator +=(" ]");
	tArray.append(ranStr);

	return tArray;
}

MStringArray	web3dExportMethods::getHAnimIFSFieldValues(MDagPath dagpath, unsigned int subNode, MStringArray sca, MFloatVectorArray cna, bool istb)
{
	MStringArray tArray;
	tArray.append(getCCW(dagpath, subNode));

	MString coordStr;
	cout << "Before getHAnimCoordIndex" << endl;
	if(istb == false) tArray.append(getHAnimCoordIndex(dagpath, subNode, sca));
	cout << "After getHAnimCoordIndex" << endl;
	tArray.append("");//getColorIndex(dagpath, subNode));
	tArray.append(getColorPerVertex(dagpath, subNode));
	tArray.append(getConvex(dagpath, subNode));
	tArray.append(getCreaseAngle(dagpath, subNode));
//	tArray.append(getHAnimNormalIndex(dagpath, subNode, cna));
	tArray.append(getNormalIndex(dagpath, subNode));
	tArray.append(getNormalPerVertex(dagpath, subNode));
	tArray.append(getSolid(dagpath, subNode));
	tArray.append(getTexCoordIndex(dagpath, subNode));

	return tArray;
}

MStringArray	web3dExportMethods::getIFSFieldValues(MDagPath dagpath, unsigned int subNode)
{
	MStringArray tArray;

	tArray.append(getCCW(dagpath, subNode));

	MString coordStr;
	tArray.append(getCoordIndex(dagpath, subNode));
	tArray.append("");//getColorIndex(dagpath, subNode));
	tArray.append(getColorPerVertex(dagpath, subNode));
	tArray.append(getConvex(dagpath, subNode));
	tArray.append(getCreaseAngle(dagpath, subNode));
	tArray.append(getNormalIndex(dagpath, subNode));
	tArray.append(getNormalPerVertex(dagpath, subNode));
	tArray.append(getSolid(dagpath, subNode));
	tArray.append(getTexCoordIndex(dagpath, subNode));

	return tArray;
}
MStringArray	web3dExportMethods::getColorFieldValues(MDagPath dagpath, unsigned int subNode)
{
	MStringArray tArray;

	MFnMesh mesh(dagpath.node());

	MColorArray colorValues;
#if MAYA_API_VERSION >= 700
	MString cColorSet;
	mesh.getCurrentColorSetName(cColorSet);
    mesh.getVertexColors(colorValues, &cColorSet);
#else
	mesh.getVertexColors(colorValues);
#endif //Maya Versioning End

	MString catStr = postProcessColorArray(colorValues, false);

	if(catStr != ""){
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
		{
			MString catStr1("[ ");
			catStr1.operator +=(catStr);
			catStr1.operator +=(" ]");
			catStr = catStr1;
		}
	}

	tArray.append(catStr);

	return tArray;
}
MStringArray	web3dExportMethods::CRGBA_FieldValues(MDagPath dagpath, unsigned int subNode)
{
	MStringArray tArray;
	return tArray;
}
MStringArray	web3dExportMethods::getNormal_FieldValues(MDagPath dagpath, unsigned int subNode)
{
	MStringArray tArray;
	MFnMesh mesh(dagpath.node());

	MFloatVectorArray normalValues;

	mesh.getNormals(normalValues, MSpace::kObject);
	MFloatVectorArray compareVal = getComparedFloatVectorArray(normalValues);
	
	MString catStr = postProcessVectorArray(compareVal);

	if(catStr != ""){
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
		{
			MString catStr1("[ ");
			catStr1.operator +=(catStr);
			catStr1.operator +=(" ]");
			catStr = catStr1;
		}
	}

	tArray.append(catStr);

	return tArray;
}

MStringArray	web3dExportMethods::getTextCoordFieldValues(MDagPath dagpath, MString usedUVSet, bool isMulti, unsigned int subNode)
{
	MStringArray tArray;
	
	MFnMesh mesh(dagpath.node());

	MFloatArray uCoord;
	MFloatArray vCoord;

	MObjectArray uvTextureAssoc;

	mesh.getUVs(uCoord, vCoord, &usedUVSet);

	MString catStr = compileTextureCoordinates(dagpath, usedUVSet, subNode, isMulti);

	if(catStr != ""){
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
		{
			MString catStr1("[ ");
			catStr1.operator +=(catStr);
			catStr1.operator +=(" ]");
			catStr = catStr1;
		}
	}

	tArray.append(catStr);

	return tArray;
}

MStringArray	web3dExportMethods::getCoord_FieldValues(MDagPath dagpath, unsigned int subNode)
{
	MStringArray tArray;
	MFnMesh mesh(dagpath.node());

	MFloatPointArray coordValues;
	mesh.getPoints(coordValues, MSpace::kObject);

	MString catStr = postProcessFloatPointArray(coordValues, 3);

	if(catStr != ""){
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
		{
			MString catStr1("[ ");
			catStr1.operator +=(catStr);
			catStr1.operator +=(" ]");
			catStr = catStr1;
		}
	}

	tArray.append(catStr);

	return tArray;
}

MStringArray	web3dExportMethods::getBoxFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//size
	MString tString("2 2 2");
	MString tString2 = getSFVec3f("size", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	if(exEncoding != VRML97ENC)
	{
		//solid
		if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
		else tString.set("TRUE");
		tString2 = getSFBool("solid", depNode);
		if(tString2.operator !=(tString)) tArray.append(tString2);
		else tArray.append("");
	}

	return tArray;
}
MStringArray	web3dExportMethods::getSphereFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//radius
	MString tString("1");
	MString tString2 = getSFFloat("radius", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	if(exEncoding != VRML97ENC)
	{
		//solid
		if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
		else tString.set("TRUE");
		tString2 = getSFBool("solid", depNode);
		if(tString2.operator !=(tString)) tArray.append(tString2);
		else tArray.append("");
	}
	return tArray;
}
MStringArray	web3dExportMethods::getConeFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	//bottom
	MString tString;
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	MString tString2 = getSFBool("bottom", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//bottomRadius
	tString.set("1");
	tString2 = getSFFloat("bottomRadius", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//height
	tString.set("2");
	tString2 = getSFFloat("height", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//side
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("side", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	if(exEncoding != VRML97ENC)
	{
		//solid
		if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
		else tString.set("TRUE");
		tString2 = getSFBool("solid", depNode);
		if(tString2.operator !=(tString)) tArray.append(tString2);
		else tArray.append("");
	}

	return tArray;
}
MStringArray	web3dExportMethods::getCylinderFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//bottom
	MString tString;
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	MString tString2 = getSFBool("bottom", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//height
	tString.set("2");
	tString2 = getSFFloat("height", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//radius
	tString.set("1");
	tString2 = getSFFloat("radius", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//side
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("side", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	if(exEncoding != VRML97ENC)
	{
		//solid
		if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
		else tString.set("TRUE");
		tString2 = getSFBool("solid", depNode);
		if(tString2.operator !=(tString)) tArray.append(tString2);
		else tArray.append("");
	}

	//top
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("top", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getViewpointFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	MString tString("0 0 0");
	MString tString2 = getParentSFVec3f("rotatePivot", depNode);

	if(exEncoding != VRML97ENC)
	{
		//centerOfRotation
		if(tString2.operator !=(tString)) tArray.append(tString2);
		else tArray.append("");
	}

	//description
	MString holdStr = getSFString("description", depNode);
	MString desStr("");
	if(holdStr.operator !=("") && holdStr.operator !=(" "))
	{
		if(exEncoding != X3DENC) desStr.set("\"");
		desStr.operator +=(holdStr);
		if(exEncoding != X3DENC) desStr.operator +=("\"");
	}
	tArray.append(desStr);

	//fieldOfView
	tString.set("0.785398");
	tString2 = getFieldOfView(depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//jump
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("jump", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//orientation
	tString.set("0 0 1 0");
	tString2 = getParentSFRotation("rotate", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");


	//position
	tString.set("0 0 10");
	tString2 = getParentSFVec3f("translate", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getDirLightFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//ambientIntensity
	MString tString("0");
	MString tString2 = getLightIntensity("ambientIntensity", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//color
	tString.set("1 1 1");
	tString2 = getSFColor("color", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//direction
	tString.set("0 0 -1");
	tString2 = getDirection(depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//intensity
	tString.set("1");
	tString2 = getLightIntensity("intensity", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//on
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("on", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getSpotLightFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//ambientIntensity
	MString tString("0");
	MString tString2 = getLightIntensity("ambientIntensity", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	tString.set("1 0 0");
	tString2 = getLightAttenuation(depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//beamWidth
	tString.set("1.570797");
	tString2 = getRadianAngle("coneAngle", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//color
	tString.set("1 1 1");
	tString2 = getSFColor("color", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//cutOffAngle  
	tString.set("0.785398");
	tString2 = getRadianAngle("penumbraAngle", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//direction
	tString.set("0 0 -1");
	tString2 = getDirection(depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//intensity
	tString.set("1");
	tString2 = getLightIntensity("intensity", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//locaton
	tString.set("0 0 0");
	tString2 = getParentSFVec3f("translate", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//on
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("on", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//radius
	tString.set("100");
	tString2 = getLightRadius(depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray	web3dExportMethods::getPointLightFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//ambientIntensity
	MString tString("0");
	MString tString2 = getLightIntensity("ambientIntensity", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//attenuation
	tString.set("1 0 0");
	tString2 = getLightAttenuation(depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//color
	tString.set("1 1 1");
	tString2 = getSFColor("color", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//intensity
	tString.set("1");
	tString2 = getLightIntensity("intensity", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//locaton
	tString.set("0 0 0");
	tString2 = getParentSFVec3f("translate", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//on
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("on", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//radius
	tString.set("100");
	tString2 = getLightRadius(depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");


	return tArray;
}

MStringArray	web3dExportMethods::getCollisionCollectionFieldValues(MFnDependencyNode &depNode)
{
	MStringArray tArray;
	tArray.append("");
	tArray.append("");
	tArray.append("");
	tArray.append("");
	tArray.append("");
	tArray.append("");
	tArray.append("");
	tArray.append("");
	tArray.append("");
	return tArray;
}

MStringArray	web3dExportMethods::getCollisionSpaceFieldValues(MFnDependencyNode &depNode)
{
	MStringArray tArray;
	tArray.append("");
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tArray.append("true");
	else tArray.append("TRUE");
	return tArray;
}

MStringArray	web3dExportMethods::getCollisionSensorFieldValues(MFnDependencyNode &depNode)
{
	MStringArray tArray;
	tArray.append("");
	return tArray;
}

MStringArray	web3dExportMethods::getRigidBodyFieldValues(MFnDagNode &dagNode, MFnDagNode &parent)
{
	MStringArray tArray;

//	angularDampingFactor
	MPlug aPlug = dagNode.findPlug("damping");
	double damp;
	aPlug.getValue(damp);
	if(damp > 0)
	{
		MString dStr;
		dStr.set(damp);
		tArray.append(dStr);
	}
	else tArray.append("");

//	angularVelocity
	MPlug avxPlug = dagNode.findPlug("isx");
	MPlug avyPlug = dagNode.findPlug("isy");
	MPlug avzPlug = dagNode.findPlug("isz");
	double avx = 0;
	double avy = 0;
	double avz = 0;

	avxPlug.getValue(avx);
	avyPlug.getValue(avy);
	avzPlug.getValue(avz);

	MString avxs;
	MString avys;
	MString avzs;
	avxs.set(avx);
	avys.set(avy);
	avzs.set(avz);
	avxs.operator +=(" ");
	avxs.operator +=(avys);
	avxs.operator +=(" ");
	avxs.operator +=(avzs);
	if(avxs.operator ==("0 0 0")) tArray.append("");
	else tArray.append(avxs);

//	autoDamp
	tArray.append("");

//	autoDisable
	tArray.append("");

//	centerOfMass
	MPlug cmxPlug = dagNode.findPlug("cmx");
	MPlug cmyPlug = dagNode.findPlug("cmy");
	MPlug cmzPlug = dagNode.findPlug("cmz");
	double cmx = 0;
	double cmy = 0;
	double cmz = 0;

	cmxPlug.getValue(cmx);
	cmyPlug.getValue(cmy);
	cmzPlug.getValue(cmz);

	MString cmxs;
	MString cmys;
	MString cmzs;
	cmxs.set(cmx);
	cmys.set(cmy);
	cmzs.set(cmz);
	cmxs.operator +=(" ");
	cmxs.operator +=(cmys);
	cmxs.operator +=(" ");
	cmxs.operator +=(cmzs);
	if(cmxs.operator ==("0 0 0")) tArray.append("");
	else tArray.append(cmxs);

//	disableAngularSpeed
	tArray.append("");

//	disableLinearSpeed
	tArray.append("");

//	disableTime
	tArray.append("");

//	enabled
	MPlug enPlug = dagNode.findPlug("collisions");
	bool enbool = true;
	enPlug.getValue(enbool);
	if(enbool==false)
	{
		if(exEncoding == X3DENC || exEncoding == X3DBENC) tArray.append("false");
		else tArray.append("FALSE");
	}
	else tArray.append("");

//	fixedRotationAxis
	tArray.append("");

//	fixed
	tArray.append("");

//	forces
	tArray.append("");

//	inertia
	tArray.append("");

//	linearDampingFactor
	if(damp > 0)
	{
		MString dStr;
		dStr.set(damp);
		tArray.append(dStr);
	}
	else tArray.append("");

//	linearVelocity
	MPlug lvxPlug = dagNode.findPlug("ivx");
	MPlug lvyPlug = dagNode.findPlug("ivy");
	MPlug lvzPlug = dagNode.findPlug("ivz");
	double lvx = 0;
	double lvy = 0;
	double lvz = 0;

	lvxPlug.getValue(lvx);
	lvyPlug.getValue(lvy);
	lvzPlug.getValue(lvz);

	MString lvxs;
	MString lvys;
	MString lvzs;
	lvxs.set(lvx);
	lvys.set(lvy);
	lvzs.set(lvz);
	lvxs.operator +=(" ");
	lvxs.operator +=(lvys);
	lvxs.operator +=(" ");
	lvxs.operator +=(lvzs);
	if(lvxs.operator ==("0 0 0")) tArray.append("");
	else tArray.append(lvxs);

//	mass
	MPlug maPlug = dagNode.findPlug("mass");
	double massD = 1;
	maPlug.getValue(massD);
	if(massD==1) tArray.append("");
	else
	{
		MString mdStr;
		mdStr.set(massD);
		tArray.append(mdStr);
	}

//	orientation
	MString rot = getSFRotation("rotate", parent);
	if(rot.operator ==("0 0 1 0")) tArray.append("");
	else tArray.append(rot);

//	position
	MString pos = getSFVec3f("translate", parent);
	if(pos.operator ==("0 0 0")) tArray.append("");
	else tArray.append(pos);

//	torques
	tArray.append("");

//	useFiniteRotation
	tArray.append("");

//	useGlobalGravity
	MPlug igPlug = dagNode.findPlug("ingore");
	bool hasGrav = true;
	igPlug.getValue(hasGrav);
	if(hasGrav) tArray.append("");
	else
	{
		if(exEncoding == X3DENC || exEncoding == X3DBENC) tArray.append("false");
		else tArray.append("FALSE");
	}

	return tArray;
}

MStringArray	web3dExportMethods::getRBCFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	tArray.append("");//autoDisable
	tArray.append("");//constantForceMix
	tArray.append("");//contactSurfaceThickness
	tArray.append("");//disableAngularSpeed
	tArray.append("");//disableLinearSpeed
	tArray.append("");//disableTime

	bool value = true;
	MPlug enab = depNode.findPlug("state");
	enab.getValue(value);
	if(value) tArray.append("");//enabled")
	else
	{
		if(exEncoding == X3DENC || exEncoding == X3DBENC) tArray.append("false");
		else tArray.append("FALSE");
	}

	int errorInt = 0;
	MPlug errPlug = depNode.findPlug("solverMethod");
	errPlug.getValue(errorInt);
	switch(errorInt)
	{
		case 0:
			tArray.append("0.5");
			break;
		case 1:
			tArray.append("");
			break;
		default:
			tArray.append("1");
			break;
	}

	MPlug gForce = depNode.findPlug("generalForce");
	MItDependencyGraph gravIt(gForce, MFn::kGravity, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	bool gFound = false;
	MFnDependencyNode gravity;
	while(!gravIt.isDone() && gFound == false)
	{
		gravity.setObject(gravIt.thisNode());
		if(gravity.typeName().operator ==("gravityField")) gFound = true;
		gravIt.next();
	}
	if(gFound)
	{
		double m = 0;
		double x = 0;
		double y = 0;
		double z = 0;
		MPlug vPlug = gravity.findPlug("magnitude");
		vPlug.getValue(m);
		vPlug = gravity.findPlug("directionX");
		vPlug.getValue(x);
		vPlug = gravity.findPlug("directionY");
		vPlug.getValue(y);
		vPlug = gravity.findPlug("directionZ");
		vPlug.getValue(z);
		x = x*m;
		y = y*m;
		z = z*m;
		MString xm;
		MString ym;
		MString zm;
		xm.set(x);
		ym.set(y);
		zm.set(z);
		MString val(xm);
		val.operator +=(" ");
		val.operator +=(ym);
		val.operator +=(" ");
		val.operator +=(zm);
		if(val.operator ==("0 -9.8 0")) tArray.append("");
		else tArray.append(val);
	}else tArray.append("0 0 0");//gravity

	MPlug iters = depNode.findPlug("stepSize");
	double ss = 10;
	iters.getValue(ss);
	if(ss = 10)	tArray.append("");//iterations"
	else
	{
		MString tString;
		tString.set(ss);
		tArray.append(tString);
	}
	tArray.append("");//maxCorrectionSpeed

	if(errorInt==2)
	{
		if(exEncoding == X3DENC || exEncoding == X3DBENC) tArray.append("true");
		else tArray.append("TRUE");
	}
	else tArray.append("");//preferAccuracy
	return tArray;
}

MStringArray	web3dExportMethods::getAPointLightFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;
	//ambientIntensity
	MString tString("0");
	MString tString2 = getLightIntensity("intensity", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//attenuation
	tString.set("1 0 0");
	tString2 = getLightAttenuation(depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//color
	tString.set("1 1 1");
	tString2 = getSFColor("color", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//intensity
	tString.set("1");
	tString2 = getLightIntensity("intensity", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//locaton
	tString.set("0 0 0");
	tString2 = getParentSFVec3f("translate", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	//on
	if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
	else tString.set("TRUE");
	tString2 = getSFBool("on", depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");


	//radius
	tString.set("100");
	tString2 = getLightRadius(depNode);
	if(tString2.operator !=(tString)) tArray.append(tString2);
	else tArray.append("");

	return tArray;
}

MStringArray web3dExportMethods::getInlineFieldValues(MFnDependencyNode &depNode, unsigned int subNode)
{
	MStringArray tArray;

	//load
	if(exEncoding != VRML97ENC)
	{
		MString tString;
		if(exEncoding == X3DENC || exEncoding == X3DBENC) tString.set("true");
		else tString.set("TRUE");
		MString tString2 = getSFBool("load", depNode);
		if(tString2.operator !=(tString)) tArray.append(tString2);
		else tArray.append("");
	}else tArray.append("");

	//url
	MString url("");
	url = getInlineURLs(depNode);
	if(url.operator ==(" ")) url.set("");
	tArray.append(url);


	return tArray;
}

void	web3dExportMethods::setDiffuseColor(MPlug mColor, MPlug mDiffuse, MStringArray & tArray)
{
	MPlug rColor = mColor.child(0);
	MPlug gColor = mColor.child(1);
	MPlug bColor = mColor.child(2);
	MPlugArray plugs;

	bool hasConTexture = false;

	float colors[3];
	rColor.getValue(colors[0]);
	gColor.getValue(colors[1]);
	bColor.getValue(colors[2]);

	float diffuse;
	mDiffuse.getValue(diffuse);

	if(mColor.connectedTo(plugs, true, false))
	{
		unsigned int i;
		for(i=0; i< plugs.length(); i++)
		{
			MFnDependencyNode depFn(plugs.operator [](i).node());
			if(depFn.typeName() == "file") hasConTexture = true;
			if(depFn.typeName() == "buldge") hasConTexture = true;
			if(depFn.typeName() == "checker") hasConTexture = true;
			if(depFn.typeName() == "cloth") hasConTexture = true;
			if(depFn.typeName() == "fractal") hasConTexture = true;
			if(depFn.typeName() == "grid") hasConTexture = true;
			if(depFn.typeName() == "mountain") hasConTexture = true;
			if(depFn.typeName() == "movie") hasConTexture = true;
			if(depFn.typeName() == "noise") hasConTexture = true;
			if(depFn.typeName() == "ocean") hasConTexture = true;
			if(depFn.typeName() == "ramp") hasConTexture = true;
			if(depFn.typeName() == "water") hasConTexture = true;
			if(depFn.typeName() == "layeredTexture") hasConTexture = true;
		}
	}

	colors[0] = colors[0] * diffuse;
	colors[1] = colors[1] * diffuse;
	colors[2] = colors[2] * diffuse;

	if(hasConTexture)
	{
		colors[0] = diffuse;
		colors[1] = diffuse;
		colors[2] = diffuse;
	}

	MString colorValue;
	MString color1;
	MString color2;
	MString color3;
	color1.set(colors[0], 5);
	color2.set(colors[1], 5);
	color3.set(colors[2], 5);

	colorValue = color1;
	colorValue.operator +=(" ");
	colorValue.operator +=(color2);
	colorValue.operator +=(" ");
	colorValue.operator +=(color3);
	if(colorValue == "0.8 0.8 0.8") colorValue.set("");

	tArray.append(colorValue);

}
void	web3dExportMethods::setAmbientIntensity(MPlug mAmbient, MStringArray & tArray)
{
	MPlug am1 = mAmbient.child(0);
	MPlug am2 = mAmbient.child(1);
	MPlug am3 = mAmbient.child(2);
	float value[3];
	am1.getValue(value[0]);
	am2.getValue(value[1]);
	am3.getValue(value[2]);

	float newValue = (value[0] + value[1] + value[2])/3;

	MString amValue;
	amValue.set(newValue, 5);
	if(amValue == "0.2") amValue.set("");
	tArray.append(amValue);

}
void	web3dExportMethods::setEmissiveColor(MPlug mEmissive, MStringArray & tArray)
{
	MPlug rColor = mEmissive.child(0);
	MPlug gColor = mEmissive.child(1);
	MPlug bColor = mEmissive.child(2);

	float colors[3];
	rColor.getValue(colors[0]);
	gColor.getValue(colors[1]);
	bColor.getValue(colors[2]);

	MString colorValue;
	MString color1;
	MString color2;
	MString color3;
	color1.set(colors[0], 5);
	color2.set(colors[1], 5);
	color3.set(colors[2], 5);

	colorValue = color1;
	colorValue.operator +=(" ");
	colorValue.operator +=(color2);
	colorValue.operator +=(" ");
	colorValue.operator +=(color3);
	if(colorValue == "0 0 0" || colorValue == "0.0 0.0 0.0") colorValue.set("");
	tArray.append(colorValue);
}
void	web3dExportMethods::setShininess(MFnDependencyNode &depFn, MPlugArray mShininess, MStringArray & tArray)
{
	const unsigned int lambert = MFn::kLambert;
	const unsigned int phong =  MFn::kPhong;
	const unsigned int blinn = MFn::kBlinn;
	const unsigned int aniso = MFn::kAnisotropy;
	const unsigned int phongE = MFn::kPhongExplorer;
	unsigned int matVal = depFn.type();
	float eccFloat;
	float sRollFloat;
	float cosFloat;
	float roughFloat;
	float hlsFloat;

	mShininess.operator [](0).getValue(eccFloat);
	mShininess.operator [](1).getValue(sRollFloat);
	mShininess.operator [](2).getValue(cosFloat);
	if(cosFloat > 100) cosFloat = 100;
	cosFloat = cosFloat/100;
	mShininess.operator [](3).getValue(roughFloat);
	mShininess.operator [](4).getValue(hlsFloat);
	
	float shininess;

	switch(matVal)
	{
		case lambert:
			shininess = 0.0f;
			break;
		case phong:
			shininess = cosFloat;
			break;
		case phongE:
			shininess = roughFloat * hlsFloat;
			break;
		case aniso:
//			shininess = eccFloat * sRollFloat;
			break;
		case blinn:
			shininess = eccFloat * sRollFloat;
			break;
		default:
			shininess = 0.2f;
			break;
	}

	MString shineValue;
	shineValue.set(shininess, 5);
	if(shineValue == "0.2") shineValue.set("");
	tArray.append(shineValue);

}
void	web3dExportMethods::setSpecularColor(MPlug mSpecular, MStringArray & tArray)
{
	MPlug rColor = mSpecular.child(0);
	MPlug gColor = mSpecular.child(1);
	MPlug bColor = mSpecular.child(2);
	MPlugArray plugs;

	bool hasConTexture = false;

	float colors[3];
	rColor.getValue(colors[0]);
	gColor.getValue(colors[1]);
	bColor.getValue(colors[2]);

	if(mSpecular.connectedTo(plugs, true, false))
	{
		unsigned int i;
		for(i=0; i< plugs.length(); i++)
		{
			MFnDependencyNode depFn(plugs.operator [](i).node());
			if(depFn.typeName() == "file") hasConTexture = true;
			if(depFn.typeName() == "buldge") hasConTexture = true;
			if(depFn.typeName() == "checker") hasConTexture = true;
			if(depFn.typeName() == "cloth") hasConTexture = true;
			if(depFn.typeName() == "fractal") hasConTexture = true;
			if(depFn.typeName() == "grid") hasConTexture = true;
			if(depFn.typeName() == "mountain") hasConTexture = true;
			if(depFn.typeName() == "movie") hasConTexture = true;
			if(depFn.typeName() == "noise") hasConTexture = true;
			if(depFn.typeName() == "ocean") hasConTexture = true;
			if(depFn.typeName() == "ramp") hasConTexture = true;
			if(depFn.typeName() == "water") hasConTexture = true;
			if(depFn.typeName() == "layeredTexture") hasConTexture = true;
		}
	}

	if(hasConTexture)
	{
		colors[0] = 0;
		colors[1] = 0;
		colors[2] = 0;
	}

//	if(colors[0] > 1 || colors[0] < 0) colors[0] = 0;
//	if(colors[1] > 1 || colors[1] < 0) colors[1] = 0;
//	if(colors[2] > 1 || colors[2] < 0) colors[2] = 0;

	MString colorValue;
	MString color1;
	MString color2;
	MString color3;
	color1.set(colors[0], 5);
	color2.set(colors[1], 5);
	color3.set(colors[2], 5);

	colorValue = color1;
	colorValue.operator +=(" ");
	colorValue.operator +=(color2);
	colorValue.operator +=(" ");
	colorValue.operator +=(color3);

	if(colorValue == "0.0 0.0 0.0" || colorValue =="0 0 0") colorValue.set("");
	tArray.append(colorValue);

}

void	web3dExportMethods::setTransparency(MPlug mTransparency, MStringArray & tArray)
{
	float newValue[3];
	MPlug tp0 = mTransparency.child(0);
	MPlug tp1 = mTransparency.child(1);
	MPlug tp2 = mTransparency.child(2);
	tp0.getValue(newValue[0]);
	tp1.getValue(newValue[1]);
	tp2.getValue(newValue[2]);
	float sFloat = (newValue[0] + newValue[1] + newValue[2])/3;

	MString transValue;
	transValue.set(sFloat);
	if(transValue == "0" || transValue == "0.0") transValue.set("");
	tArray.append(transValue);

}

MString	web3dExportMethods::compileTextureCoordinates(MDagPath dagpath, MString usedUVSet, unsigned int sn, bool isMulti)
{
	MFloatArray uCoord;
	MFloatArray vCoord;

	MObjectArray shaders;
	MObjectArray groups;
	MFnMesh mesh(dagpath.node());
	mesh.getConnectedSetsAndMembers(0, shaders, groups, true);

	MItMeshPolygon pIter(dagpath, groups.operator [](sn));

	mesh.getUVs(uCoord, vCoord, &usedUVSet);

	MPointArray pIndex;
	float lostU;
	float lostV;
//	getLostUV(lostU, lostV, uCoord, vCoord);
	MPlug lPlug = mesh.findPlug("lostUV");
	MPlug lPlug1 = lPlug.child(0);
	MPlug lPlug2 = lPlug.child(1);
	lPlug1.getValue(lostU);
	lPlug2.getValue(lostV);

	float lostFloat[4];
	lostFloat[0]=lostU;
	lostFloat[1]=lostV;
	lostFloat[2]=0.0f;
	lostFloat[3]=0.0f;
	MPoint lostP(lostFloat);

	if(isMulti)
	{
		while(!pIter.isDone())
		{
			bool isUV = pIter.hasUVs(usedUVSet);
			unsigned int vc = pIter.polygonVertexCount();
//			MIntArray cVertInd;
//			pIter.getVertices(cVertInd);
			unsigned int i;
//			for(i=0;i<cVertInd.length();i++)
			for(i=0;i<vc;i++)
			{
				if(isUV){
					float2 newFloats;
					pIter.getUV(i, newFloats, &usedUVSet);//getUV(cVertInd.operator [](i), newFloats, &usedUVSet);

					float tpfloats[4];
					tpfloats[0] = newFloats[0];
					tpfloats[1] = newFloats[1];
					tpfloats[2] = 0.0f;
					tpfloats[3] = 0.0f;
					MPoint tPoint(tpfloats);
					pIndex.append(tPoint);
				}
				else
				{
					MPoint tPoint(lostP);
					pIndex.append(tPoint);
				}
			}
			pIter.next();
		}
	}
	else//8888899999
	{
		pIndex.append(lostP);
		
		MFloatArray uStorage;
		MFloatArray vStorage;

		mesh.getUVs(uStorage, vStorage, &usedUVSet);
		unsigned int i;
		for(i=0; i<uStorage.length();i++)
		{
			float tpfloats[4];
			tpfloats[0] = uStorage.operator [](i);
			tpfloats[1] = vStorage.operator [](i);
			tpfloats[2] = 0.0f;
			tpfloats[3] = 0.0f;
			MPoint tPoint(tpfloats);
			pIndex.append(tPoint);
		}
	}

	return postProcessPointArray(pIndex, 2);
}

void web3dExportMethods::getLostUV(float & lostU, float & lostV, MFloatArray uCoord, MFloatArray vCoord)
{
	float minU;
	float maxU;
	float minV;
	float maxV;
	getExtremes(minU, maxU, minV, maxV, uCoord, vCoord);

	float du = maxU - minU;
	float dv = maxV - minV;

	lostU = maxU + ceil(2*du);
	lostV = maxV + ceil(2*dv);
}

void web3dExportMethods::getExtremes(float & minU, float & maxU, float & minV, float & maxV, MFloatArray uCoord, MFloatArray vCoord)
{
	minU = uCoord.operator [](0);
	maxU = uCoord.operator [](0);

	minV = vCoord.operator [](0);
	maxV = vCoord.operator [](0);
	unsigned int i;
	for(i=1; i<uCoord.length(); i++)
	{
		if(uCoord.operator [](i) > maxU) maxU = uCoord.operator [](i);
		if(uCoord.operator [](i) < minU) minU = uCoord.operator [](i);
		if(vCoord.operator [](i) > maxV) maxV = vCoord.operator [](i);
		if(vCoord.operator [](i) < minV) minV = vCoord.operator [](i);
	}
}

MString	web3dExportMethods::getCCW(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");
	MFnDagNode dagFn(dagpath);
	MPlug oppPlug = dagFn.findPlug("opposite");
	bool oppVal = true;
	oppPlug.getValue(oppVal);
	if(oppVal)
	{
		if(exEncoding == X3DENC || exEncoding == X3DBENC) retVal.set("false");
		else retVal.set("FALSE");
	}
/*
	unsigned int i;
	int j = -1;

	MFnDagNode dagFn(dagpath);
	for(i=0; i< dagFn.childCount(); i++)
	{
		MFnDependencyNode cNode(dagFn.child(i));
		if(cNode.typeName() == "x3dIndexedFaceSet") j = i;
	}

	if(j>-1)
	{
		MFnDependencyNode cNode(dagFn.child(j));
		MPlug aPlug = cNode.findPlug("ccw");
		bool value;
		aPlug.getValue(value);
		if(!value) retVal.set("FALSE");
	}
	*/
	return retVal;
}

MString	web3dExportMethods::getColorIndex(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");

	unsigned int i;
	int j = -1;
	MFnDagNode dagFn(dagpath);
	for(i=0; i< dagFn.childCount(); i++)
	{
		MFnDependencyNode cNode(dagFn.child(i));
		if(cNode.typeName() == "x3dIndexedFaceSet") j = i;
	}

	if(j>-1)
	{
		MFnDependencyNode cNode(dagFn.child(j));
		MPlug aPlug = cNode.findPlug("cpv");
		bool value;
		aPlug.getValue(value);
		if(value) retVal = computeColorI(dagpath, sn);
	}
	else if(globalCPV) retVal = computeColorI(dagpath, sn);

	return retVal;
}
#if MAYA_API_VERSION >= 700 //For versions of Maya 7.0 and up
MString	web3dExportMethods::getColorPerVertex(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");
	MFnMesh mesh(dagpath);

	MString cColorSet;
	mesh.getCurrentColorSetName(cColorSet);
	int cValue = mesh.numColors(cColorSet);
	bool cpvVal = false;
	if(cValue > 0) cpvVal = true;

	if(!cpvVal)
	{
		if(exEncoding == X3DENC || exEncoding == X3DBENC) retVal.set("false");
		else retVal.set("FALSE");
	}
	return retVal;
}
#else //For versions of Maya below 7.0
MString	web3dExportMethods::getColorPerVertex(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");
	unsigned int i = 0;
	MFnMesh mesh(dagpath);
	MColorArray colors;
	mesh.getVertexColors(colors);

	bool cpvVal = false;
	while(i<colors.length() && cpvVal == false)
	{
		float fcVal = colors.operator [](i).r * colors.operator [](i).g * colors.operator [](i).b;
		if(fcVal != -1) cpvVal = true;
		else i = i+1;
	}

	if(!cpvVal)
	{
		if(exEncoding == X3DENC || exEncoding == X3DBENC) retVal.set("false");
		else retVal.set("FALSE");
	}
	return retVal;
}
#endif //End of Maya versioning

MString	web3dExportMethods::getConvex(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");
//	unsigned int i;
//	int j = -1;
	MFnDagNode dagFn(dagpath);

	MStatus mstat;
	MPlug conPlug = dagFn.findPlug("x3dConvex", &mstat);//*mstat
//	dagFn.findPlug(

	if(mstat == MStatus::kSuccess)
	{
		bool hasCon = true;
		conPlug.getValue(hasCon);
		if(!hasCon)
		{
			if(exEncoding == X3DENC || exEncoding == X3DBENC) retVal.set("false");
			else retVal.set("FALSE");
		}
	}
/*
	for(i=0; i< dagFn.childCount(); i++)
	{
		MFnDependencyNode cNode(dagFn.child(i));
		if(cNode.typeName() == "x3dIndexedFaceSet") j = i;
	}

	if(j>-1)
	{
		MFnDependencyNode cNode(dagFn.child(j));
		MPlug aPlug = cNode.findPlug("convex");
		bool value;
		aPlug.getValue(value);
		if(!value) retVal.set("FALSE");
	}
*/
	return retVal;
}

MString	web3dExportMethods::getCoordIndex(MDagPath dagpath, unsigned int sn)
{
	MString retVal = computeCoordI(dagpath, sn);
	if(retVal != ""){
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
		{
			MString retVal1("[ ");
			retVal1.operator +=(retVal);
			retVal1.operator +=(" ]");
			retVal = retVal1;
		}
	}
	return retVal;
}

MString	web3dExportMethods::getHAnimCoordIndex(MDagPath dagpath, unsigned int sn, MStringArray sca)
{
	cout << "Before computeHAnimCoordI" << endl;
	MString retVal = computeHAnimCoordI(dagpath, sn, sca);
	cout << "After computeHAnimCoordI" << endl;
	if(retVal != ""){
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
		{
			MString retVal1("[ ");
			retVal1.operator +=(retVal);
			retVal1.operator +=(" ]");
			retVal = retVal1;
		}
	}
	return retVal;
}

MString	web3dExportMethods::getCreaseAngle(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");
//	unsigned int i;
//	int j = -1;
	MFnDagNode dagFn(dagpath);

	MPlug ulPlug = dagFn.findPlug("useLocalX3dCreaseAngle");
	bool ulBool = false;
	ulPlug.getValue(ulBool);
	if(ulBool)
	{
		MStatus mstat;
		MPlug conPlug = dagFn.findPlug("x3dCreaseAngle", &mstat);

		if(mstat == MStatus::kSuccess)
		{
			float caVal = 0;
			conPlug.getValue(caVal);
			if(caVal != 0) retVal.operator +=(caVal);
		}
	}
	else
	{
		if(globalCA != 0) retVal.operator +=(globalCA);
	}

	return retVal;
}

MString	web3dExportMethods::getNormalIndex(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");
/*
	unsigned int i;
	int j = -1;
	MFnDagNode dagFn(dagpath);
	for(i=0; i< dagFn.childCount(); i++)
	{
		MFnDependencyNode cNode(dagFn.child(i));
		if(cNode.typeName() == "x3dIndexedFaceSet") j = i;
	}

	if(j>-1)
	{
		MFnDependencyNode cNode(dagFn.child(j));
		MPlug aPlug = cNode.findPlug("npv");
		bool value;
		aPlug.getValue(value);
		if(value) retVal = computeNI(dagpath, sn);
	}
*/

	MString valset = getNormalPerVertex(dagpath, sn);
	if(valset.operator == ("")) retVal = computeNI(dagpath, sn);

	if(retVal != ""){
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
		{
			MString retVal1("[ ");
			retVal1.operator +=(retVal);
			retVal1.operator +=(" ]");
			retVal = retVal1;
		}
	}

	return retVal;
}
//9990009991
MString	web3dExportMethods::getHAnimNormalIndex(MDagPath dagpath, unsigned int sn, MFloatVectorArray cna)
{
	MString retVal("");

	MString valset = getNormalPerVertex(dagpath, sn);
	if(valset.operator == (""))	retVal = computeHAnimNI(dagpath, sn, cna);

	if(retVal != ""){
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
		{
			MString retVal1("[ ");
			retVal1.operator +=(retVal);
			retVal1.operator +=(" ]");
			retVal = retVal1;
		}
	}

	
	return retVal;
}

MString	web3dExportMethods::getNormalPerVertex(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");

	bool hasNormalMap = false;
	MFnMesh mesh(dagpath);
	MObjectArray shaders;
	MObjectArray groups;
	mesh.getConnectedSetsAndMembers(0, shaders, groups, true);
	MObject shaderObj = shaders.operator [](sn);
	MFnDependencyNode depFn(shaderObj);

	MPlug aPlug = depFn.findPlug("surfaceShader");
	MPlugArray plugs;
	MStatus mstat;
	aPlug.connectedTo(plugs, true, false, &mstat);
	if(mstat == MStatus::kSuccess)
	{
		if(plugs.length() > 0)
		{
			MObject shaderNodeObj = plugs.operator [](0).node();
			MFnDependencyNode shaderNode(shaderNodeObj);

			MPlugArray plugs2;
			MStatus mstat2;
			MPlug nmPlug = shaderNode.findPlug("normalCamera");
			nmPlug.connectedTo(plugs2, true, false, &mstat2);

			if(plugs2.length() > 0)
			{
				if(mstat2 == MStatus::kSuccess)
				{
					if(exEncoding != VRML97ENC) hasNormalMap = true;
				}
			}
		}
	}



/*
	unsigned int i;
	int j = -1;
	MFnDagNode dagFn(dagpath);
	for(i=0; i< dagFn.childCount(); i++)
	{
		MFnDependencyNode cNode(dagFn.child(i));
		if(cNode.typeName() == "x3dIndexedFaceSet") j = i;
	}

	if(j>-1)
	{
		MFnDependencyNode cNode(dagFn.child(j));
		MPlug aPlug = cNode.findPlug("npv");
		bool value;
		aPlug.getValue(value);
		if(!value) retVal.set("FALSE");
	}
	else if(!globalNPV) retVal.set("FALSE");
*/
	if(globalNPV == false || hasNormalMap == true)
	{
		if(exEncoding == X3DENC || exEncoding == X3DBENC) retVal.set("false");
		else retVal.set("FALSE");
	}
	return retVal;
}

MString	web3dExportMethods::getSolid(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");
//	unsigned int i;
//	int j = -1;
	MFnDagNode dagFn(dagpath);

	MPlug dsPlug = dagFn.findPlug("doubleSided");
	bool dsVal = true;
	dsPlug.getValue(dsVal);
	if(dsVal)
	{
		if(exEncoding == X3DENC || exEncoding == X3DBENC) retVal.set("false");
		else retVal.set("FALSE");
	}
/*
	for(i=0; i< dagFn.childCount(); i++)
	{
		MFnDependencyNode cNode(dagFn.child(i));
		if(cNode.typeName() == "x3dIndexedFaceSet") j = i;
	}

	if(j>-1)
	{
		MFnDependencyNode cNode(dagFn.child(j));
		MPlug aPlug = cNode.findPlug("solid");
		bool value;
		aPlug.getValue(value);
		if(!value) retVal.set("FALSE");
	}
	else if(!globalSolid) retVal.set("FALSE");
*/
	return retVal;
}

MString	web3dExportMethods::getTexCoordIndex(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");

	MFloatArray uCoord;
	MFloatArray vCoord;

	MObjectArray uvTextureAssoc;

	MString uvSetName;
	MStringArray uvSetNames;

	MObjectArray se;
	MObjectArray comps;

	MFnMesh mesh(dagpath.node());
	mesh.getUVSetNames(uvSetNames);
	mesh.getConnectedSetsAndMembers(0, se, comps, true);

	bool hasT = false;

	MStringArray usedUVSets = getUsedUVSetsInOrder(mesh.object(), hasT, uvSetNames, sn);
	
	bool hasMultiUVSets = false;
	if(usedUVSets.length() > 1)
	{
		unsigned int i;
		for(i=0;i<usedUVSets.length();i++)
		{
			if(usedUVSets.operator [](0).operator !=(usedUVSets.operator [](i))) hasMultiUVSets = true;
		}
	}

	if((exEncoding == VRML97ENC || hasMultiUVSets == false) && hasT == true)
	{
		retVal = computeTexCoordI(dagpath, usedUVSets, sn, false);
	}
	else if(hasT)
	{
		retVal = computeTexCoordI(dagpath, usedUVSets, sn, true);
	}

	if(retVal != ""){
		if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
		{
			MString retVal1("[ ");
			retVal1.operator +=(retVal);
			retVal1.operator +=(" ]");
			retVal = retVal1;
		}
	}

	return retVal;
}

MString	web3dExportMethods::computeColorI(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");
	MObjectArray shaders;
	MObjectArray groups;
	MFnMesh mesh(dagpath.node());
	mesh.getConnectedSetsAndMembers(0, shaders, groups, true);

	MItMeshPolygon pIter(dagpath, groups.operator [](sn));
	MIntArray bIndex;


	while(!pIter.isDone())
	{
		int pIndex = pIter.index();
		MIntArray pVertInd;

		pIter.getVertices(pVertInd);
		unsigned int i;
		for(i=0;i<pVertInd.length();i++)
		{
			int addValue = 0;
			mesh.getFaceVertexColorIndex(pIndex, pVertInd.operator [](i), addValue);
			bIndex.append(addValue);
		}
		bIndex.append(-1);
		pIter.next();
	}
	retVal = postProcessIndices(bIndex);
	return retVal;
}

MString	web3dExportMethods::computeNI(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");
	MObjectArray shaders;
	MObjectArray groups;
	MFnMesh mesh(dagpath.node());
	mesh.getConnectedSetsAndMembers(0, shaders, groups, true);
	MItMeshPolygon pIter(dagpath, groups.operator [](sn));
	MIntArray bIndex;

	MFloatVectorArray normalValues;
	mesh.getNormals(normalValues);
	MFloatVectorArray compareVal = getComparedFloatVectorArray(normalValues);
	
	while(!pIter.isDone())
	{

		int vc = pIter.polygonVertexCount();
		if(vc<0) vc = 0;
		unsigned int vcLen = vc;
		unsigned int i;
		for(i=0;i<vcLen;i++)
		{
			double vec1d[3];
			float vec2[3];
			MVector nVector;
			pIter.getNormal(i, nVector, MSpace::kObject);
			nVector.get(vec1d);
			float vec1[3];
			vec1[0] = (float)vec1d[0];
			vec1[1] = (float)vec1d[1];
			vec1[2] = (float)vec1d[2];

			unsigned int j;
			for(j=0; j<compareVal.length(); j++)
			{
				compareVal.operator [](j).get(vec2);
				if(vec1[0] == vec2[0] && vec1[1] == vec2[1] && vec1[2] == vec2[2])
				{
					int newValue = j;
					bIndex.append(newValue);
				}
			}
		}
		bIndex.append(-1);
		pIter.next();
	}
	
	retVal = postProcessIndices(bIndex);
	return retVal;
}

MString	web3dExportMethods::computeHAnimNI(MDagPath dagpath, unsigned int sn, MFloatVectorArray cna)
{
	MString retVal("");
	MObjectArray shaders;
	MObjectArray groups;
	MFnMesh mesh(dagpath.node());

	MFloatVectorArray tnArray;
	mesh.getNormals(tnArray, MSpace::kObject);

	mesh.getConnectedSetsAndMembers(0, shaders, groups, true);
	MItMeshPolygon pIter(dagpath, groups.operator [](sn));
	MIntArray bIndex;

	while(!pIter.isDone())
	{

		int vc = pIter.polygonVertexCount();
		if(vc<0) vc = 0;
		unsigned int vcLen = vc;
		unsigned int i;
		for(i=0;i<vcLen;i++)
		{
			int ni = pIter.normalIndex(i);
			ni = ni + cna.length();
			bIndex.append(ni);
		}
		bIndex.append(-1);
		pIter.next();
	}
	
	retVal = postProcessIndices(bIndex);

	unsigned int i;
	for(i=0;i<tnArray.length();i++)
	{
		cna.append(tnArray.operator [](i));
	}
	return retVal;
}

MString	web3dExportMethods::computeCoordI(MDagPath dagpath, unsigned int sn)
{
	MString retVal("");

	MObjectArray shaders;
	MObjectArray groups;

	MFnMesh mesh(dagpath.node());
	mesh.getConnectedSetsAndMembers(0, shaders, groups, true);

	MItMeshPolygon pIter(dagpath, groups.operator [](sn));
	MIntArray bIndex;
	
	while(!pIter.isDone())
	{
		MIntArray cVertInd;
		pIter.getVertices(cVertInd);

		unsigned int i;
		for(i=0;i<cVertInd.length();i++) bIndex.append(cVertInd.operator [](i));
		bIndex.append(-1);
		pIter.next();
	}
	retVal = postProcessIndices(bIndex);
	return retVal;
}

MString	web3dExportMethods::computeHAnimCoordI(MDagPath dagpath, unsigned int sn, MStringArray sca)
{
	MString retVal("");

	MObjectArray shaders;
	MObjectArray groups;

	MFnMesh mesh(dagpath.node());

	MStringArray offset;
	unsigned int q = 0;
	bool ldag = true;
	bool fdag = false;
	while(ldag == true || fdag == true)
	{
		MStringArray chopped;
		sca.operator [](q).split('*', chopped);

//		cout << chopped.operator [](0) << ", Mesh Name: " << mesh.name() << endl;
		if(chopped.operator [](0).operator ==(mesh.name()))
		{
			if(fdag == false)
			{
				fdag = true;
				ldag = false;
			}
//			offset.append(chopped.operator [](2));
			offset.append(chopped.operator [](3));
			q=q+1;
		}
		else
		{
			if(fdag == true) fdag = false;
			q=q+1;
		}
	}

	mesh.getConnectedSetsAndMembers(0, shaders, groups, true);

	MItMeshPolygon pIter(dagpath, groups.operator [](sn));
	MIntArray bIndex;
	
	while(!pIter.isDone())
	{
		MIntArray cVertInd;
		pIter.getVertices(cVertInd);

		unsigned int i;
		for(i=0;i<cVertInd.length();i++)
		{
			bIndex.append(offset.operator [](cVertInd.operator [](i)).asInt());
		}
		bIndex.append(-1);
		pIter.next();
	}

	retVal = postProcessIndices(bIndex);
	return retVal;
}

MString web3dExportMethods::computeTexCoordI(MDagPath dagpath, MStringArray usedMaps, unsigned int sn, bool isMulti)
{
	MString retVal("");
	MObjectArray shaders;
	MObjectArray groups;
	MFnMesh mesh(dagpath.node());
	mesh.getConnectedSetsAndMembers(0, shaders, groups, true);
	MItMeshPolygon pIter(dagpath, groups.operator [](sn));
	MIntArray bIndex;


	if(isMulti)
	{
		int cVal = 0;
		while(!pIter.isDone())
		{
			unsigned int vc = pIter.polygonVertexCount();
			unsigned int i;
			for(i=0;i<vc;i++)
			{
				bIndex.append(cVal);
				cVal = cVal +1;
			}
			bIndex.append(-1);
			pIter.next();
		}
	}
	else
	{
	
	while(!pIter.isDone())
	{
		unsigned int vc = pIter.polygonVertexCount();
		bool testForMapping = pIter.hasUVs(usedMaps.operator [](0));
		unsigned int i;
		for(i=0;i<vc;i++)
		{
			int tValue = 0;
			if(testForMapping)
			{
				pIter.getUVIndex(i, tValue, &usedMaps.operator [](0));
				tValue = tValue+1;
				bIndex.append(tValue);
			}
			else bIndex.append(0);
		}
		bIndex.append(-1);
		pIter.next();
	}

	}

	retVal = postProcessIndices(bIndex);
	return retVal;
}

MString web3dExportMethods::postProcessColorArray(MColorArray cArray, bool hasAlpha)
{
	MString retVal("");
	unsigned int i;
	for(i=0; i<cArray.length();i++)
	{
		float values[4];
		MColor tColor = cArray.operator [](i);
		tColor.get(values);

		MString tValue;
		if(values[0] < 0) values[0] = 0.0f;
		tValue.set(values[0], 5);
		retVal.operator +=(tValue);
		retVal.operator +=(" ");
		
		if(values[1] < 0) values[1] = 0.0f;
		tValue.set(values[1], 5);
		retVal.operator +=(tValue);
		retVal.operator +=(" ");
		
		if(values[2] < 0) values[2] = 0.0f;
		tValue.set(values[2], 5);
		retVal.operator +=(tValue);

		if(hasAlpha)
		{
			retVal.operator +=(" ");
			if(values[3] < 0) values[3] = 0.0f;
			tValue.set(values[3], 5);
			retVal.operator +=(tValue);
		}

		if(i!=cArray.length()-1) retVal.operator +=(",\n");
	}
	return retVal;
}

MString web3dExportMethods::postProcessVectorArray(MFloatVectorArray vArray)
{
	MString retVal("");
	unsigned int i;
	float sumFloat[3];
	sumFloat[0] = 0.0f;
	sumFloat[1] = 0.0f;
	sumFloat[2] = 0.0f;

	for(i=0; i<vArray.length();i++)
	{
		float values[3];
		MFloatVector tVector = vArray.operator [](i);
		tVector.normalize();
		tVector.get(values);

		MString tValue;
		tValue.set(values[0], 5);
		retVal.operator +=(tValue);
		retVal.operator +=(" ");
		
		tValue.set(values[1], 5);
		retVal.operator +=(tValue);
		retVal.operator +=(" ");
		
		tValue.set(values[2], 5);
		retVal.operator +=(tValue);
		if(i!=vArray.length()-1) retVal.operator +=(",\n");
	}
	return retVal;
}

MString web3dExportMethods::postProcessPointArray(MPointArray pArray, unsigned int vl)
{
	MString retVal("");
	unsigned int i;
	for(i=0; i<pArray.length();i++)
	{
		float values[4];
		MPoint tPoint = pArray.operator [](i);
		tPoint.get(values);

		MString tValue;
		tValue.set(values[0], 5);
		retVal.operator +=(tValue);
		if(vl>1)
		{
			retVal.operator +=(" ");
			tValue.set(values[1], 5);
			retVal.operator +=(tValue);
			if(vl>2)
			{
				retVal.operator +=(" ");
				tValue.set(values[2], 5);
				retVal.operator +=(tValue);
				if(vl > 3)
				{
					retVal.operator +=(" ");
					tValue.set(values[3], 5);
					retVal.operator +=(tValue);
				}
			}
		}
		if(i!=pArray.length()-1) retVal.operator +=(",\n");
	}
	return retVal;
}

MString web3dExportMethods::postProcessFloatPointArray(MFloatPointArray pArray, unsigned int vl)
{
	MString retVal("");
	unsigned int i;
	for(i=0; i<pArray.length();i++)
	{
		float values[4];
		MFloatPoint tPoint = pArray.operator [](i);
		tPoint.get(values);

		MString tValue;
		tValue.set(values[0], 5);
		retVal.operator +=(tValue);
		if(vl>1)
		{
			retVal.operator +=(" ");
			tValue.set(values[1], 5);
			retVal.operator +=(tValue);
			if(vl>2)
			{
				retVal.operator +=(" ");
				tValue.set(values[2], 5);
				retVal.operator +=(tValue);
				if(vl > 3)
				{
					retVal.operator +=(" ");
					tValue.set(values[3], 5);
					retVal.operator +=(tValue);
				}
			}
		}
		if(i!=pArray.length()-1) retVal.operator +=(",\n");
	}
	return retVal;
}

MString web3dExportMethods::postProcessIndices(MIntArray bIndex)
{
	MString retVal("");
	unsigned int i;
	for(i=0; i<bIndex.length();i++)
	{
		retVal.operator +=(bIndex.operator [](i));
		if(i!=bIndex.length()-1)
		{
			if(bIndex.operator [](i) == -1) retVal.operator +=("\n");
			else retVal.operator +=(" ");
		}
	}
	return retVal;
}

//MStringArray web3dExportMethods::getUsedUVSetsInOrder(MFnMesh mesh, bool & hasT, MStringArray uvSetNames, unsigned int val)
MStringArray web3dExportMethods::getUsedUVSetsInOrder(MObject mObj, bool & hasT, MStringArray uvSetNames, unsigned int val)
{
	MFnMesh mesh(mObj);
	MStringArray newArray;
	MStringArray textureList = getShaderTexturesInOrder(mesh.object(), val);
	
	if(textureList.length() == 0)
	{
		hasT = false;
	}
	else
	{
		unsigned int i;
		for(i=0;i<textureList.length();i++)
		{
			newArray.append("map1");
		}

		for(i=0;i<uvSetNames.length();i++)
		{
			MObjectArray assocTexture;
			mesh.getAssociatedUVSetTextures(uvSetNames.operator [](i), assocTexture);
			if(assocTexture.length()>0)
			{
				hasT = true;
			}

			unsigned int j;
			for(j=0;j<assocTexture.length();j++)
			{
				MFnDependencyNode depFn(assocTexture.operator [](j));
				unsigned int k;
				for(k=0; k<textureList.length();k++)
				{
					if(depFn.name() == textureList.operator [](k))
					{
						newArray.operator [](k) = uvSetNames.operator [](i);
					}
				}
			}
		}
	}
	return newArray;
}

//MStringArray web3dExportMethods::getShaderTexturesInOrder(MFnMesh mesh, unsigned int val)
MStringArray web3dExportMethods::getShaderTexturesInOrder(MObject mObj, unsigned int val)
{
	MFnMesh mesh(mObj);
	MStringArray tNames;
	MObjectArray se;
	MObjectArray groups;
	mesh.getConnectedSetsAndMembers(0, se, groups, true);

	MString compStr(groups.operator [](val).apiTypeStr());

	MFnDependencyNode depFn(se.operator [](val));

	MPlug aPlug = depFn.findPlug("surfaceShader");

	bool hasLS = false;
	MItDependencyGraph appIter(aPlug, MFn::kLayeredShader, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	while(!appIter.isDone())
	{
		MFnDependencyNode lsTest(appIter.thisNode());
		if(lsTest.typeName() == "layeredShader") hasLS = true;
		appIter.next();
	}
	MString shaderType = depFn.typeName();
	if(hasLS)
	{
	}
	else
	{
		MFnDependencyNode shader;
		bool nFound = true;
		MItDependencyGraph shIter1(aPlug, MFn::kLambert,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
		while(!shIter1.isDone())
		{
			MFnDependencyNode lambertTest(shIter1.thisNode());
			if(lambertTest.typeName() == "lambert")
			{
				shader.setObject(lambertTest.object());
				nFound = false;
			}
			shIter1.next();
		}
		if(nFound)
		{
			MItDependencyGraph shIter2(aPlug, MFn::kBlinn,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!shIter2.isDone())
			{
				MFnDependencyNode blinnTest(shIter2.thisNode());
				if(blinnTest.typeName() == "blinn")
				{
					shader.setObject(blinnTest.object());
					nFound = false;
				}
				shIter2.next();
			}
		}
		if(nFound)
		{
			MItDependencyGraph shIter3(aPlug, MFn::kPhong,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!shIter3.isDone())
			{
				MFnDependencyNode phongTest(shIter3.thisNode());
				if(phongTest.typeName() == "phong")
				{
					shader.setObject(phongTest.object());
					nFound = false;
				}
				shIter3.next();
			}
		}
		if(nFound)
		{
			MItDependencyGraph shIter4(aPlug, MFn::kPhongExplorer,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!shIter4.isDone())
			{
				MFnDependencyNode phongETest(shIter4.thisNode());
				if(phongETest.typeName() == "phongE")
				{
					shader.setObject(phongETest.object());
					nFound = false;
				}
				shIter4.next();
			}
		}
		if(!nFound)
		{
			MStringArray throwData;

			MFnDependencyNode thisShader(shader.object()); // Not sure if this is the right thing to do.
			MPlug mSpecular = thisShader.findPlug("specularColor");
			MPlug mBump = thisShader.findPlug("normalCamera");
			MPlug mColor = thisShader.findPlug("color");

			bool hasAnother = false;
			bool hasSpec = findSpecularMap(mSpecular, tNames, throwData);
			bool hasBump = findBumpMap(mBump, tNames, throwData);
			if(hasSpec == true || hasBump == true) hasAnother = true;
			bool hasColor = findColorMap(mColor, tNames, throwData, hasAnother);
		}
	}
	return tNames;
}

bool web3dExportMethods::findSpecularMap(MPlug mSpecular, MStringArray & tArray, MStringArray & mArray)
{
	bool localBool = false;

	MStringArray tempTArray;
	MStringArray tempMArray;

	MItDependencyGraph depGraph(mSpecular, MFn::kLayeredTexture, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	MStatus stat;
	MObject layT = depGraph.thisNode(&stat);
	if(stat == MStatus::kSuccess)
	{
		MFnDependencyNode depFn(layT);
		MPlug inputs = depFn.findPlug("inputs");
		unsigned int inpEle = inputs.numElements();

		unsigned int i;
		for(i=0;i<inpEle;i++)
		{
			MPlug eleInput = inputs.elementByPhysicalIndex(i);

			MPlug colPlug = eleInput.child(0);

			MItDependencyGraph depGraph2(colPlug, MFn::kTexture2d, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!depGraph2.isDone())
			{
				localBool = true;
				MObject aNode2 = depGraph2.thisNode();
				MFnDependencyNode depNode2(aNode2);
				tempTArray.append(depNode2.name());
				tempMArray.append("REPLACE");
				depGraph2.next();
			}
		}
	}
	else
	{
		MItDependencyGraph depGraph2(mSpecular, MFn::kTexture2d, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
		while(!depGraph2.isDone())
		{
			localBool = true;
			MObject aNode2 = depGraph2.thisNode();
			MFnDependencyNode depNode2(aNode2);
			tempTArray.append(depNode2.name());
			tempMArray.append("REPLACE");//WAS ADD
			depGraph2.next();
		}
	}
	unsigned int i;
	unsigned int newVals = tempTArray.length()-1;
	for(i=0; i<tempTArray.length();i++)
	{
		unsigned int ni = newVals-i;
		MString tempStr(tempTArray.operator [](ni));
		tArray.append(tempStr);
		MString tempStr1(tempMArray.operator [](ni));
		mArray.append(tempStr1);
	}
	return localBool;
}

bool web3dExportMethods::findColorMap(MPlug mColor, MStringArray & tArray, MStringArray & mArray, bool hasAnother)
{
	bool localBool = false;

	MStringArray tempTArray;
	MStringArray tempMArray;

	MItDependencyGraph depGraph(mColor, MFn::kLayeredTexture, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	MStatus stat;
	MObject layT = depGraph.thisNode(&stat);
	if(stat == MStatus::kSuccess)
	{
		MFnDependencyNode depFn(layT);
		MPlug inputs = depFn.findPlug("inputs");
		unsigned int inpEle = inputs.numElements();

		unsigned int i;
		for(i=0;i<inpEle;i++)
		{
			MPlug eleInput = inputs.elementByPhysicalIndex(i);
			bool fTex = false;

			MPlug colPlug = eleInput.child(0);

			MItDependencyGraph depGraph2(colPlug, MFn::kTexture2d, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!depGraph2.isDone())
			{
				localBool = true;
				fTex = true;
				MObject aNode2 = depGraph2.thisNode();
				MFnDependencyNode depNode2(aNode2);

				tempTArray.append(depNode2.name());
				depGraph2.next();
			}
			if(fTex)
			{
				MPlug blendPlug = eleInput.child(2);
				int value;
				blendPlug.getValue(value);
				MString mString;
				if(hasAnother != true) mString = assignMode(value);
				else mString.set("MODULATE");
				tempMArray.append(mString);
			}
		}
	}
	else
	{
		MItDependencyGraph depGraph2(mColor, MFn::kTexture2d, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
		while(!depGraph2.isDone())
		{
			MObject aNode2 = depGraph2.thisNode();
			MFnDependencyNode depNode2(aNode2);
			if(depNode2.typeName().operator !=("movie"))
			{
				if(depNode2.typeName().operator !=("file"))
				{
					MString eString(depNode2.name());
					eString.operator +=("_rawkee_export");
					MFnDependencyNode depNode3 = findNonExportTexture(eString);
					depNode2.setObject(depNode3.object());
				}
				cout << "Texture Info - Name: " << depNode2.name() << ", Type: " << depNode2.typeName() << endl;  
				tempTArray.append(depNode2.name());

				int maIndex = tempMArray.length();
				tempMArray.append("EMPTY");


				int maVal = 0;
				MPlug maPlug = depNode2.findPlug("stMode");
				maPlug.getValue(maVal);

				switch(maVal)
				{
					case 1:
						tempMArray.operator [](maIndex).operator =("REPLACE");
						break;
					case 2:
						tempMArray.operator [](maIndex).operator =("MODULATE");
						break;
					case 3:
						tempMArray.operator [](maIndex).operator =("ADD");
						break;
					default:
						tempMArray.operator [](maIndex).operator =("EMPTY");// WAS "EMTPY"
						break;
				}
				if(tempMArray.operator [](maIndex).operator !=("EMPTY"))
				{
//					tempMArray.operator [](maIndex).operator =("MODULATE");
//				}
//				else 
//				{
					localBool = true;
				}
				else tempMArray.operator [](maIndex).operator =("MODULATE");
			}

			depGraph2.next();
		}
	}

	unsigned int i;
	unsigned int newVals = tempTArray.length()-1;
	for(i=0; i<tempTArray.length();i++)
	{
		unsigned int ni = newVals-i;
		MString tempStr(tempTArray.operator [](ni));
		tArray.append(tempStr);
		MString tempStr1(tempMArray.operator [](ni));
		mArray.append(tempStr1);
	}
	return localBool;
}

MString web3dExportMethods::assignMode(int value)
{
	MString retVal("");
	switch(value)
	{
		case 0:
			retVal.set("REPLACE");
			break;
		case 1:
			retVal.set("REPLACE");
			break;
		case 2:
			retVal.set("BLENDTEXTUREALPHA");
			break;
		case 3:
			retVal.set("MODULATEALPHA_ADDCOLOR");
			break;
		case 4:
			retVal.set("ADD");
			break;
		case 5:
			retVal.set("SUBTRACT");
			break;
		case 6:
			retVal.set("MODULATE");
			break;
		case 7:
			retVal.set("MODULATEINVALPHA_ADDCOLOR");
			break;
		case 8:
			retVal.set("ADDSIGNED2X");
			break;
		case 9:
			retVal.set("MODULATE2X");
			break;
		case 10:
			retVal.set("REPLACE");
			break;
		case 11:
			retVal.set("SUBTRACT");
			break;
		case 12:
			retVal.set("MODULATE4X");
			break;
		default:
			break;
	}
	return retVal;
}
bool web3dExportMethods::findBumpMap(MPlug mBump, MStringArray & tArray, MStringArray & mArray)
{
	bool localBool = false;

	MStringArray tempTArray;
	MStringArray tempMArray;

	MItDependencyGraph depGraph(mBump, MFn::kLayeredTexture, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	MStatus stat;
	MObject layT = depGraph.thisNode(&stat);
	if(stat == MStatus::kSuccess)
	{
		MFnDependencyNode depFn(layT);
		MPlug inputs = depFn.findPlug("inputs");
		unsigned int inpEle = inputs.numElements();

		unsigned int i;
		for(i=0;i<inpEle;i++)
		{
			MPlug eleInput = inputs.elementByPhysicalIndex(i);

			MPlug colPlug = eleInput.child(0);

			MItDependencyGraph depGraph2(colPlug, MFn::kTexture2d, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!depGraph2.isDone())
			{
				localBool = true;
				MObject aNode2 = depGraph2.thisNode();
				MFnDependencyNode depNode2(aNode2);
				tempTArray.append(depNode2.name());
				tempMArray.append("DOTPRODUCT3");
				depGraph2.next();
			}
		}
	}
	else
	{
		MItDependencyGraph depGraph2(mBump, MFn::kTexture2d, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
		while(!depGraph2.isDone())
		{
			localBool = true;
			MObject aNode2 = depGraph2.thisNode();
			MFnDependencyNode depNode2(aNode2);
			tempTArray.append(depNode2.name());
			tempMArray.append("DOTPRODUCT3");
			depGraph2.next();
		}
	}
	unsigned int i;
	unsigned int newVals = tempTArray.length()-1;
	for(i=0; i<tempTArray.length();i++)
	{
		unsigned int ni = newVals-i;
		MString tempStr(tempTArray.operator [](ni));
		tArray.append(tempStr);
		MString tempStr1(tempMArray.operator [](ni));
		mArray.append(tempStr1);
	}
	return localBool;
}

void	web3dExportMethods::setGlobalCPV(bool value)
{
	globalCPV = value;
}

void	web3dExportMethods::setGlobalNPV(bool value)
{
	globalNPV = value;
}

void	web3dExportMethods::setGlobalSolid(bool value)
{
	globalSolid = value;
}

void	web3dExportMethods::setGlobalCA(float value)
{
	globalCA = value;
}

void	web3dExportMethods::setExportEncoding(int value)
{
	exEncoding = value;
}

void	web3dExportMethods::setAudioDir(MString aDir)
{
	audioDir = aDir;
}

void	web3dExportMethods::setInlineDir(MString inDir)
{
	inlineDir = inDir;
}

void	web3dExportMethods::setImageDir(MString iDir)
{
	imageDir = iDir;
}

void	web3dExportMethods::setBaseUrl(MString bUrl)
{
	baseUrl.operator =(bUrl);
}

void	web3dExportMethods::setTF(MString extension)
{
	exTextureFormat = extension;
}

//void	web3dExportMethods::setAdjTexture(bool at)
//{
//	adjTexture = at;
//}

void	web3dExportMethods::setTW(int twVal)
{
	x3dTextureWidth = twVal;
}

void	web3dExportMethods::setTH(int thVal)
{
	x3dTextureHeight = thVal;
}

void	web3dExportMethods::setConsolidate(bool conVal)
{
	conMedia = conVal;
}

void	web3dExportMethods::setUseRelURL(bool value)
{
	useRelURL = value;
}

bool	web3dExportMethods::getUseRelURL()
{
	return useRelURL;
}

void	web3dExportMethods::setUseRelURLW(bool value)
{
	useRelURLW = value;
}

bool	web3dExportMethods::getUseRelURLW()
{
	return useRelURLW;
}

MString	web3dExportMethods::specCharProcessor(MString pString)
{
	MString retString("");
	const char* characters = pString.asChar();
	int length = pString.length();
//	unsigned int bc = 0;
	for(int i=0; i<length; i++)
	{
		switch(characters[i])
		{
			case '<':
				retString.operator +=("&lt;");
				break;
			case '>':
				retString.operator +=("&gt;");
				break;
			case '&':
				retString.operator +=("&amp;");
				break;
			case '\'':
				retString.operator +=("&apos;");
				break;
			case '\"':
				retString.operator +=("&quot;");
				break;
			default:
//				MString charString(""+characters[i]);
				retString.operator +=(pString.substring(i, i));
				break;
		}
//		if(bc==49 && i!=length-1)
//		{
//			retString.operator +=("\n");
//			bc=0;
//		}
//		else
//		{
//			bc = bc+1;
//		}
	}
	return retString;
}
MString			web3dExportMethods::replaceNewLines(MString cString)
{
	MString newString("");
	MStringArray chopped;
	char nline = '\n';
	cString.split(nline, chopped);
	unsigned int cLen = chopped.length();
	unsigned int i;
	for(i=0;i<cLen;i++)
	{
		newString.operator +=(chopped.operator [](i));
		if(i<cLen-1) newString.operator +=("\n");
	}
	return newString;
}

MStringArray	web3dExportMethods::getScriptLocalURLs(MFnDependencyNode &sNode)
{
	MStringArray urls;

	MPlug scrPlug = sNode.findPlug("localScript");
	MPlug ccPlug = sNode.findPlug("localScript_cc");

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	for(i=0;i<vLength;i++)
	{
		MPlug lsPlug = scrPlug.elementByPhysicalIndex(i);
		MString sVal;
		lsPlug.getValue(sVal);
		urls.append(sVal);
	}

	return urls;
}

MStringArray	web3dExportMethods::getScriptRemoteURLs(MFnDependencyNode &sNode)
{
	MStringArray urls;

	MPlug scrPlug = sNode.findPlug("remoteScript");
	MPlug ccPlug = sNode.findPlug("remoteScript_cc");

	int cc;
	ccPlug.getValue(cc);
	unsigned int vLength = cc;

	unsigned int i;
	for(i=0;i<vLength;i++)
	{
		MPlug lsPlug = scrPlug.elementByPhysicalIndex(i);
		MString sVal;
		lsPlug.getValue(sVal);
		urls.append(sVal);
	}

	return urls;
}

MStringArray	web3dExportMethods::getScriptCustomFieldNames(MFnDagNode &sNode)
{
	MStringArray fNames;
	MPlug aPlug = sNode.findPlug("fieldName");
	MPlug lPlug = sNode.findPlug("x3dFieldCount");
	int lVal;
	lPlug.getValue(lVal);
	unsigned int cLen = lVal;
	unsigned int i;
	for(i=0;i<cLen;i++)
	{
		MPlug cPlug = aPlug.elementByPhysicalIndex(i);//probable cause of error 999111999
		MString tName;
		cPlug.getValue(tName);
		fNames.append(tName);
	}
	return fNames;
}

MStringArray	web3dExportMethods::getScriptCustomFieldTypes(MFnDagNode &sNode)
{
	MStringArray fTypes;
	MPlug aPlug = sNode.findPlug("fieldType");
	MPlug lPlug = sNode.findPlug("x3dFieldCount");
	int lVal;
	lPlug.getValue(lVal);
	unsigned int cLen = lVal;
	unsigned int i;
	for(i=0;i<cLen;i++)
	{
		MPlug cPlug = aPlug.elementByPhysicalIndex(i);
		MString tType;
		cPlug.getValue(tType);
		fTypes.append(tType);
	}
	return fTypes;
}

MStringArray	web3dExportMethods::getScriptCustomFieldAccess(MFnDagNode &sNode)
{
	MStringArray fAccess;
	MPlug aPlug = sNode.findPlug("fieldAccess");
	MPlug lPlug = sNode.findPlug("x3dFieldCount");
	int lVal;
	lPlug.getValue(lVal);
	unsigned int cLen = lVal;
	unsigned int i;
	for(i=0;i<cLen;i++)
	{
		MPlug cPlug = aPlug.elementByPhysicalIndex(i);
		MString tAcc;
		cPlug.getValue(tAcc);
		fAccess.append(tAcc);
	}
	return fAccess;
}

MString			web3dExportMethods::getScriptCustomValue(MFnDagNode &sNode, unsigned int index)
{
	MString fValue;
	MStringArray tsa = getScriptCustomFieldTypes(sNode);
	MStringArray nsa = getScriptCustomFieldNames(sNode);
	MStringArray asa = getScriptCustomFieldAccess(sNode);
	MString ftype = tsa.operator [](index);
	MString fname("x3d_");
	fname.operator +=(nsa.operator [](index));
	MString fAccess(asa.operator [](index));
	if( ftype == "MFNode" || ftype == "SFNode" || fAccess == "inputOnly" || fAccess == "outputOnly") fValue.set("");
	else
	{
		if(ftype == "SFBool") fValue = getSFBool(fname, sNode);
		else if(ftype == "SFColor") fValue = getSFColor(fname, sNode);
		else if(ftype == "SFColorRGBA") fValue = getSFColorRGBA(fname, sNode);
		else if(ftype == "SFDouble") fValue = getSFDouble(fname, sNode);
		else if(ftype == "SFFloat") fValue = getSFFloat(fname, sNode);
		else if(ftype == "SFImage") fValue = getSFImage(fname, sNode);
		else if(ftype == "SFInt32") fValue = getSFInt32(fname, sNode);
		else if(ftype == "SFRotation") fValue = getSFRotation(fname, sNode);
		else if(ftype == "SFString")
		{
			MString tString = getSFString(fname, sNode);
			if(tString.operator ==("")) fValue.set("\"\"");
			else fValue = tString;
		}
		else if(ftype == "SFTime") fValue = getSFTime(fname, sNode);
		else if(ftype == "SFVec2f") fValue = getSFVec2f(fname, sNode);
		else if(ftype == "SFVec2d") fValue = getSFVec2d(fname, sNode);
		else if(ftype == "SFVec3f") fValue = getSFVec3f(fname, sNode);
		else if(ftype == "SFVec3d") fValue = getSFVec3d(fname, sNode);
		else if(ftype == "MFBool") fValue = getMFBool(fname, sNode);
		else if(ftype == "MFColor") fValue = getMFColor(fname, sNode);
		else if(ftype == "MFColorRGBA") fValue = getMFColorRGBA(fname, sNode);
		else if(ftype == "MFDouble") fValue = getMFDouble(fname, sNode);
		else if(ftype == "MFFloat") fValue = getMFFloat(fname, sNode);
		else if(ftype == "MFImage") fValue = getMFImage(fname, sNode);
		else if(ftype == "MFInt32") fValue = getMFInt32(fname, sNode);
		else if(ftype == "MFRotation") fValue = getMFRotation(fname, sNode);
		else if(ftype == "MFString") fValue = getMFString(fname, sNode);
		else if(ftype == "MFTime") fValue = getMFTime(fname, sNode);
		else if(ftype == "MFVec2f") fValue = getMFVec2f(fname, sNode);
		else if(ftype == "MFVec2d") fValue = getMFVec2d(fname, sNode);
		else if(ftype == "MFVec3f") fValue = getMFVec3f(fname, sNode);
		else if(ftype == "MFVec3d") fValue = getMFVec3d(fname, sNode);
	}
	return fValue;
}

MObjectArray	web3dExportMethods::getScriptNodeObjects(MFnDagNode &sNode, unsigned int index)
{
	MObjectArray nObj;
	MStringArray tsa = getScriptCustomFieldTypes(sNode);
	MStringArray fsa = getScriptCustomFieldNames(sNode);
	if(tsa.operator [](index).operator ==("MFNode"))
	{
		MString attName("x3d_");
		attName.operator +=(fsa.operator [](index));
		MPlug strPlug = sNode.findPlug(attName);

		MPlug kvPlug = sNode.findPlug(attName);
		MString cString = attName;
		cString.operator +=("_cc");
		MPlug ccPlug = sNode.findPlug(cString);

		int cc;
		ccPlug.getValue(cc);
		unsigned int vLength = cc;

		unsigned int i;
		for(i=0;i<vLength;i++)
		{
			MPlug dPlug = kvPlug.child(i);
			MString sVal;
			dPlug.getValue(sVal);
//			MFnDependencyNode depFn = getMyDepNode(sVal);
			MFnDependencyNode depFn(getMyDepNodeObj(sVal));
			if(depFn.name().operator !=("")) nObj.append(depFn.object());
		}
	}
	else if(tsa.operator [](index).operator ==("SFNode"))
	{
		MString attName("x3d_");
		attName.operator +=(fsa.operator [](index));
		MPlug strPlug = sNode.findPlug(attName);
		MString nodeName;
		strPlug.getValue(nodeName);

//		MFnDependencyNode depFn = getMyDepNode(nodeName);
		MFnDependencyNode depFn(getMyDepNodeObj(nodeName));
		if(depFn.name().operator !=("")) nObj.append(depFn.object());
	}
	return nObj;
}
