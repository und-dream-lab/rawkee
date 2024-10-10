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

// File: x3dColor.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

	const MTypeId x3dColor::typeId( 0x00108F0E );
	const MString x3dColor::typeName( "x3dColor" );
	MObject x3dColor::color;


	x3dColor::x3dColor():ParentClass()
	{
	}

	x3dColor::x3dColor(MPxTransformationMatrix *tm):ParentClass(tm)
	{
	}

	x3dColor::~x3dColor()
	{
	}

	MStatus x3dColor::computeLocalTransformation(MPxTransformationMatrix *xform, MDataBlock &block)
	{
		return ParentClass::computeLocalTransformation(xform, block);
	}

	MPxTransformationMatrix *x3dColor::createTransformationMatrix()
	{
		return new MPxTransformationMatrix();
	}

	void *x3dColor::creator()
	{
		return new x3dColor();
	}

	MStatus x3dColor::initialize()
	{
		MFnTypedAttribute typFn;

		color = typFn.create("color", "colo", MFnData::kVectorArray);
		addAttribute( color );

		return MS::kSuccess;
	}
