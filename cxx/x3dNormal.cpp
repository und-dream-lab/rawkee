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

// File: x3dNormal.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

	const MTypeId x3dNormal::typeId( 0x00108F49 );
	const MString x3dNormal::typeName( "x3dNormal" );
	MObject x3dNormal::vector;


	x3dNormal::x3dNormal():ParentClass()
	{
	}

	x3dNormal::x3dNormal(MPxTransformationMatrix *tm):ParentClass(tm)
	{
	}

	x3dNormal::~x3dNormal()
	{
	}

	MStatus x3dNormal::computeLocalTransformation(MPxTransformationMatrix *xform, MDataBlock &block)
	{
		return ParentClass::computeLocalTransformation(xform, block);
	}

	MPxTransformationMatrix *x3dNormal::createTransformationMatrix()
	{
		return new MPxTransformationMatrix();
	}

	void *x3dNormal::creator()
	{
		return new x3dNormal();
	}

	MStatus x3dNormal::initialize()
	{
		MFnTypedAttribute typFn;
		MFnStringData sd;
		MObject defString = sd.create("");

		vector = typFn.create("vector", "vect", MFnData::kVectorArray);
		addAttribute( vector );

		return MS::kSuccess;
	}
