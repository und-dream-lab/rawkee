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

// File: x3dBox.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

	const MTypeId x3dBox::typeId( 0x00108F0B );
	const MString x3dBox::typeName( "x3dBox" );
	MObject x3dBox::size;
	MObject x3dBox::solid;



	x3dBox::x3dBox():ParentClass()
	{
	}

	x3dBox::x3dBox(MPxTransformationMatrix *tm):ParentClass(tm)
	{
	}

	x3dBox::~x3dBox()
	{
	}

	MStatus x3dBox::computeLocalTransformation(MPxTransformationMatrix *xform, MDataBlock &block)
	{
		return ParentClass::computeLocalTransformation(xform, block);
	}

	MPxTransformationMatrix *x3dBox::createTransformationMatrix()
	{
		return new MPxTransformationMatrix();
	}

	void *x3dBox::creator()
	{
		return new x3dBox();
	}

	MStatus x3dBox::initialize()
	{
		MStatus status;
		MFnNumericAttribute numFn;

		size = numFn.create("size", "siz", MFnNumericData::k3Float, 2);

		addAttribute( size );

		solid = numFn.create("solid", "soli", MFnNumericData::kBoolean, true);

		addAttribute( solid );

		return status;
	}
