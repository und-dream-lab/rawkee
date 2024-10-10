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

// File: x3dLoadSensor.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dLoadSensor
//-----------------------------------------------
	const MTypeId x3dLoadSensor::typeId( 0x00108F3D );
	const MString x3dLoadSensor::typeName( "x3dLoadSensor" );

	MObject x3dLoadSensor::watchList;
	MObject x3dLoadSensor::enabled;
	MObject x3dLoadSensor::timeOut;
	MObject x3dLoadSensor::images;
	MObject x3dLoadSensor::movies;
	MObject x3dLoadSensor::audios;
	MObject x3dLoadSensor::inlines;

//	const double M_2PI = M_PI * 2.0;

	MStatus x3dLoadSensor::initialize()
	{
		MFnNumericAttribute numFn;
		MFnTypedAttribute typFn;
		MFnStringData sd;
		MObject defString = sd.create("");

		enabled = numFn.create("enabled", "enab", MFnNumericData::kBoolean, true);
		addAttribute( enabled );

		timeOut = numFn.create("timeOut", "tOut", MFnNumericData::kDouble, 0);
		addAttribute(timeOut);
		
		images = typFn.create("images", "imgs", MFnData::kString, defString);
		movies = typFn.create("movies", "moves", MFnData::kString, defString);
		audios = typFn.create("audios", "ads", MFnData::kString, defString);
		inlines = typFn.create("inlines", "ins", MFnData::kString, defString);
		
		typFn.setObject(images);
		typFn.setHidden(true);
		addAttribute(images);

		typFn.setObject(movies);
		typFn.setHidden(true);
		addAttribute(movies);

		typFn.setObject(audios);
		typFn.setHidden(true);
		addAttribute(audios);

		typFn.setObject(inlines);
		typFn.setHidden(true);
		addAttribute(inlines);
		
		return MS::kSuccess;
	}

	void *x3dLoadSensor::creator()
	{
		return new x3dLoadSensor();
	}
