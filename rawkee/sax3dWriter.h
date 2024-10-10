#ifndef __SAX3DWRITER_H
#define __SAX3DWRITER_H

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

// File: sax3dWriter.h
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//


#include <sys/stat.h>
#include <sys/types.h>

#if MAYA_API_VERSION >= 600 //For versions of Maya 6.0 and higher
#include <iostream>
#include <fstream>
#include "stdio.h"
//#include "string.h"
//#include "direct.h"

using namespace std;
#else //For versions of Maya below 6.0
#include "stdio.h"
#include "iostream.h"
#include "fstream.h"
#endif
///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//MStrings used to check against nodeType 
//names in order to the get the type of 
//node being exported - probably should be 
//implemented in a more efficient manner.
//-----------------------------------------
#define msEmpty ""

#define msBox "Box"
#define msCone "Cone"
#define msCylinder "Cylinder"
#define msSphere "Sphere"

#define msIndexedFaceSet "IndexedFaceSet"

#define msColor "Color"
#define msColorRGBA "ColorRGBA"
#define msCoordinate "Coordinate"
#define msMultiTextureCoordinate "MultiTextureCoordinate"
#define msNormal "Normal"
#define msTextureCoordinate "TextureCoordinate"

#define msAnchor "Anchor"
#define msInline "Inline"
#define msCollision "Collision"
#define msGroup "Group"
#define msLOD "LOD"
#define msSwitch "Switch"
#define msTransform "Transform"
#define msBillboard "Billboard"

#define msShape "Shape"
#define msAppearance "Appearance"
#define msMaterial "Material"

#define msNavigationInfo "NavigationInfo"
#define msWorldInfo "WorldInfo"
#define msViewpoint "Viewpoint"

#define msDirectionalLight "DirectionalLight"
#define msSpotLight "SpotLight"
#define msPointLight "PointLight"

#define msColorInterpolator "ColorInterpolator"
#define msOrientationInterpolator "OrientationInterpolator"
#define msPositionInterpolator "PositionInterpolator"
#define msScalarInterpolator "ScalarInterpolator"

#define msCoordinateInterpolator "CoordinateInterpolator"
#define msNormalInterpolator "NormalInterpolator"

#define msBooleanSequencer "BooleanSequencer"
#define msIntegerSequencer "IntegerSequencer"

#define msBooleanTrigger "BooleanTrigger"
#define msBooleanToggle "BooleanToggle"
#define msBooleanFilter "BooleanFilter"
#define msIntegerTrigger "IntegerTrigger"
#define msTimeTrigger "TimeTrigger"

#define msCylinderSensor "CylinderSensor"
#define msKeySensor "KeySensor"
#define msLoadSensor "LoadSensor"
#define msPlaneSensor "PlaneSensor"
#define msProximitySensor "ProximitySensor"
#define msSphereSensor "SphereSensor"
#define msStringSensor "StringSensor"
#define msTimeSensor "TimeSensor"
#define msTouchSensor "TouchSensor"
#define msVisibilitySensor "VisibilitySensor"

#define msImageTexture "ImageTexture"
#define msPixelTexture "PixelTexture"
#define msMovieTexture "MovieTexture"
#define msMultiTexture "MultiTexture"
#define msTextureTransform "TextureTransform"
#define msMultiTextureTransform "MultiTextureTransform"

#define msAudioClip "AudioClip"
#define msSound "Sound"

#define msScript "Script"

#define msMetaD "MetadataDouble"
#define msMetaF "MetadataFloat"
#define msMetaI "MetadataInteger"
#define msMetaSe "MetadataSet"
#define msMetaSt "MetadataString"

//Xj3D RigidBody Phyisics Component: 2
#define msColShape "CollidableShape"
#define msRigidBodyCollection "RigidBodyCollection"
#define msRigidBody "RigidBody"
#define msCollisionCollection "CollisionCollection"
#define msCollisionSpace "CollisionSpace"
#define msCollisionSensor "CollisionSensor"

//H-Anim Component: 1
#define msHAnimJoint "HAnimJoint"
#define msHAnimHumanoid "HAnimHumanoid"
#define msHAnimSite "HAnimSite"

//Xj3D IODevice Component: 2
#define msGamepadSensor "GamepadSensor"

#define msRoute "ROUTE"

#define msfield "field"

#define ftSFNode "SFNode"
#define ftMFNode "MFNode"

#define defValue "------"

#define X3DENC 0
#define X3DVENC 1
#define VRML97ENC 2
#define X3DBENC 3

class sax3dWriter
{
public:
			sax3dWriter();
	virtual	~sax3dWriter();

	ostream*		newFile;

	void	writeScriptFile(MString fName, MString contents, MString localPath);
	void	startDocument();
	void	endDocument();
	void	startNode(MString x3dType, MString x3dName, MStringArray fields, MStringArray fieldValues, bool hasMore);
	void	writeRoute(MString fromNode, MString fromField, MString toNode, MString toField);
	void	addScriptNonNodeField(MString accessType, MString fieldType, MString fieldName, MString fieldValue);
	void	addScriptNodeField(MString accessType, MString fieldType, MString fieldName);
	void	addScriptNodeFieldValue(MString value);
	void	endScriptNodeField();
	void	endNode(MString x3dType, MString x3dName);
	void	startField(MString x3dFName, MString x3dFValue);
	void	fieldValue(MString x3dFValue);
	void	endField();
	void	useDecl(MString x3dType, MString x3dName, MString cField, MString cValue);
	void	writeTabs();
	void	profileDecl();//MString type);
	void	writeComponents();
	void	outputCData(MStringArray rawdata);
	void	writeSBracket();
	void	writeScriptSBracket();
	void	preWriteField(MString fieldName);
	void	writeScriptEBracket();
	void	writeEBracket();
	void	writeRawCode(MString rawCode);

	static			MString			version;

	static			MString			profileType;
	static			MStringArray	additionalComps;
	static			MStringArray	additionalCompsLevels;

	static			MStringArray	commentNames;
	static			MStringArray	comments;

	static			unsigned int				tabNumber;

	static			MString			msg;

	static			int				exEncoding;

	static			bool			hasMultiple;
	static			bool			firstNotWritten;

					bool			checkIfIgnored(MString nodeName);
					void			setIgnored(MString nodeName);

					bool			checkIfHasBeen(MString nodeName);
					void			setAsHasBeen(MString nodeName);
					void			clearMemberLists();
					void			setHasMultiple(bool value);
					MString			processForLineReturns(MString sData);
					MString			processForTabs(MString sData);

protected:

					MStringArray	tabRawData(MStringArray rawdata);
/*
	static			MString			documentUrl;
	static			MString			versionEncoding;
	static			MString			writeEncoding;
	static			MString			x3dProfile;
	static			MStringArray	x3dComponents;
	static			MStringArray	x3dComments;
	static			MString			nodeType;
	static			MString			nodeName;
	static			MStringArray	nodeFields;
	static			MStringArray	nodeValues;
	static			MString			fieldName;
	static			MString			fieldValue1;
	static			MString			fieldValue2;
	static			MString			cField;
	static			MString			cValue;
	static			MStringArray	cData;
*/
	static			MStringArray	ignoredNodes;
	static			MStringArray	haveBeenNodes;

};

#endif
