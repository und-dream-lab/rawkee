//
// Copyright (C) 2004-2005 North Dakota State University (http://atl.ndsu.edu/resources/maya_x3d.php) 
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

// File: x3dStringSensor.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dStringSensor
//-----------------------------------------------
	const MTypeId x3dStringSensor::typeId( 0x00108F6B );
	const MString x3dStringSensor::typeName( "x3dStringSensor" );

	MObject x3dStringSensor::enabled;
	MObject x3dStringSensor::deletionAllowed;

//	const double M_2PI = M_PI * 2.0;

	MStatus x3dStringSensor::initialize()
	{
		MFnNumericAttribute numFn;
		deletionAllowed = numFn.create("deletionAllowed", "delAllow", MFnNumericData::kBoolean, true);
		addAttribute( enabled );

		enabled = numFn.create("enabled", "enab", MFnNumericData::kBoolean, true);
		addAttribute( enabled );

		return MS::kSuccess;
	}

	void *x3dStringSensor::creator()
	{
		return new x3dStringSensor();
	}
