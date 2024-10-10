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

// File: x3dInline.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

	const MTypeId x3dInline::typeId( 0x00108F37 );
	const MString x3dInline::typeName( "x3dInline" );

	MObject x3dInline::load;
	MObject x3dInline::url;

	x3dInline::x3dInline():ParentClass()
	{
	}

	x3dInline::x3dInline(MPxTransformationMatrix *tm):ParentClass(tm)
	{
	}

	x3dInline::~x3dInline()
	{
	}

	MStatus x3dInline::computeLocalTransformation(MPxTransformationMatrix *xform, MDataBlock &block)
	{
		return ParentClass::computeLocalTransformation(xform, block);
	}

	MPxTransformationMatrix *x3dInline::createTransformationMatrix()
	{
		return new MPxTransformationMatrix();
	}

	void *x3dInline::creator()
	{
		return new x3dInline();
	}

	MStatus x3dInline::initialize()
	{
		MStatus stat;
		MFnNumericAttribute numFn;
		MFnTypedAttribute tAttr;

		load = numFn.create("load", "ld", MFnNumericData::kBoolean, true);
		addAttribute( load );

		url = tAttr.create("url", "u", MFnData::kString);
		addAttribute( url );

		return MS::kSuccess;
	}
