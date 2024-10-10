//
// Copyright (C) 2004 North Dakota State University (http://atl.ndsu.edu/resources/maya_x3d.php) 
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

// File: x3dNavigationInfo.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dNavigationInfo
//-----------------------------------------------
	const MTypeId x3dNavigationInfo::typeId( 0x00108F48 );
	const MString x3dNavigationInfo::typeName( "x3dNavigationInfo" );

	MObject x3dNavigationInfo::avatarSize;
	MObject x3dNavigationInfo::avatarWidth;
	MObject x3dNavigationInfo::avatarHeight;
	MObject x3dNavigationInfo::avatarStep;
	MObject x3dNavigationInfo::headlight;
	MObject x3dNavigationInfo::speed;
	MObject x3dNavigationInfo::visibilityLimit;
	MObject x3dNavigationInfo::transitionType;
	MObject x3dNavigationInfo::transitionType_cc;	
	MObject x3dNavigationInfo::type;
	MObject x3dNavigationInfo::type_cc;

	MStatus x3dNavigationInfo::initialize()
	{
		MFnNumericAttribute numFn;
		MFnTypedAttribute typFn;

		avatarWidth = numFn.create("avatarWidth", "aw", MFnNumericData::kFloat, 0.25);
		numFn.setMin(0.0);

		avatarHeight = numFn.create("avatarHeight", "ah", MFnNumericData::kFloat, 1.6);
		numFn.setMin(0.0);

		avatarStep = numFn.create("avatarStep", "aStep", MFnNumericData::kFloat, 0.75);
		numFn.setMin(0.0);

		avatarSize = numFn.create("avatarSize", "as", avatarWidth, avatarHeight, avatarStep);
		numFn.setDefault(0.25, 1.6, 0.75);
		addAttribute(avatarSize);

		headlight = numFn.create("headlight", "hl", MFnNumericData::kBoolean, true);
		addAttribute(headlight);

		MObject defMeta;
		MFnStringData sd;
		defMeta = sd.create("");

		speed = numFn.create("speed", "sd", MFnNumericData::kFloat, 1.0);
		numFn.setMin(0.0);

		addAttribute(speed);

		transitionType = typFn.create("transitionType", "tt", MFnData::kString);
		MFnAttribute ttAttr(transitionType);
		ttAttr.setHidden(true);
		ttAttr.setArray(true);
		addAttribute(transitionType);

		transitionType_cc =  numFn.create("transitionType_cc", "ttcc", MFnNumericData::kInt, 0);
		numFn.setObject(transitionType_cc);
		numFn.setHidden(true);
		addAttribute(transitionType_cc);

		type = typFn.create("type", "typ", MFnData::kString);
		MFnAttribute moveAttr(type);
		moveAttr.setHidden(true);
		moveAttr.setArray(true);
		addAttribute(type);

		type_cc = numFn.create("type_cc", "typcc", MFnNumericData::kInt, 0);
		numFn.setObject(type_cc);
		numFn.setHidden(true);
		addAttribute(type_cc);

		visibilityLimit = numFn.create("visibilityLimit", "visLimit", MFnNumericData::kFloat, 0.0);
		numFn.setMin(0.0);

		addAttribute(visibilityLimit);

		return MS::kSuccess;
	}

	void *x3dNavigationInfo::creator()
	{
		return new x3dNavigationInfo();
	}

	void x3dNavigationInfo::postConstructor()
	{
		MFnDependencyNode nodeFn(thisMObject());
		nodeFn.setName("NavigationInfo");

	}
