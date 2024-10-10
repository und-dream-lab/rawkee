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

// File: x3dWorldInfo.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dWorldInfo
//-----------------------------------------------
	const MTypeId x3dWorldInfo::typeId( 0x00108F7D );
	const MString x3dWorldInfo::typeName( "x3dWorldInfo" );

	MObject x3dWorldInfo::title;
	MObject x3dWorldInfo::info;
	MObject x3dWorldInfo::info_cc;


	MStatus x3dWorldInfo::initialize()
	{
		MStatus stat;
		MFnTypedAttribute typFn;
		MFnNumericAttribute numFn;
		
		title = typFn.create("title", "titl", MFnData::kString);
		info = typFn.create("info", "inf", MFnData::kString);
		typFn.setObject(info);
		typFn.setArray(true);

		info_cc = numFn.create("info_cc", "infcc", MFnNumericData::kInt, 0);
		numFn.setObject(info_cc);
		numFn.setHidden(true);

		addAttribute( title );
		addAttribute( info );
		addAttribute( info_cc);

		return MS::kSuccess;
	}

	void *x3dWorldInfo::creator()
	{
		return new x3dWorldInfo();
	}
