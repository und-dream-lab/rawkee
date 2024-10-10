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

// File: x3dCylinderSensor.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dCylinderSensor
//-----------------------------------------------
	const MTypeId x3dCylinderSensor::typeId( 0x00108F19 );
	const MString x3dCylinderSensor::typeName( "x3dCylinderSensor" );

	MObject x3dCylinderSensor::description;
	MObject x3dCylinderSensor::autoOffset;
	MObject x3dCylinderSensor::diskAngle;
	MObject x3dCylinderSensor::enabled;
	MObject x3dCylinderSensor::maxAngle;
	MObject x3dCylinderSensor::minAngle;
	MObject x3dCylinderSensor::offset;

//	const double M_2PI = M_PI * 2.0;

	MStatus x3dCylinderSensor::initialize()
	{
		MFnNumericAttribute numFn;
		MFnTypedAttribute typFn;
		MFnUnitAttribute unitFn;

		autoOffset = numFn.create("autoOffset", "aOffset", MFnNumericData::kBoolean, true);
		addAttribute( autoOffset );

		double diskVal = M_PI/12;
		diskAngle= unitFn.create("diskAngle", "dkAngle", MFnUnitAttribute::kAngle, diskVal);
		addAttribute( diskAngle );

		enabled = numFn.create("enabled", "enab", MFnNumericData::kBoolean, true);
		addAttribute( enabled );

		description = typFn.create( "description", "desc", MFnData::kString);
		addAttribute( description );
		
//		double degVal = -57.296;
		double max = M_PI * 2;//360;
		double min = M_PI * -2;//-360;
		maxAngle = unitFn.create("maxAngle", "maxAng", MFnUnitAttribute::kAngle, -1);
		unitFn.setObject(maxAngle);
		unitFn.setMax(max);
		unitFn.setMin(min);
		addAttribute( maxAngle );

		minAngle= unitFn.create("minAngle", "minAng", MFnUnitAttribute::kAngle, 0);
		unitFn.setObject(minAngle);
		unitFn.setMax(max);
		unitFn.setMin(min);
		addAttribute( minAngle );

		offset = numFn.create("offset", "oset", MFnNumericData::kFloat);
		addAttribute( offset );

		return MS::kSuccess;
	}

	void *x3dCylinderSensor::creator()
	{
		return new x3dCylinderSensor();
	}
