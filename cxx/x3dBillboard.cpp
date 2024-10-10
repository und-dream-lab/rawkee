//
// Copyright (C) 2004-2007 North Dakota State University (http://atl.ndsu.edu/resources/maya_x3d.php) 
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

// File: x3dBillboard.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

	const MTypeId x3dBillboard::typeId( 0x00108F06 );
	const MString x3dBillboard::typeName( "x3dBillboard" );

	MObject x3dBillboard::axisOfRotation;

	x3dBillboard::x3dBillboard():ParentClass()
	{
	}

	x3dBillboard::x3dBillboard(MPxTransformationMatrix *tm):ParentClass(tm)
	{
	}

	x3dBillboard::~x3dBillboard()
	{
	}

	MStatus x3dBillboard::computeLocalTransformation(MPxTransformationMatrix *xform, MDataBlock &block)
	{
		return ParentClass::computeLocalTransformation(xform, block);
	}

	MPxTransformationMatrix *x3dBillboard::createTransformationMatrix()
	{
		return new MPxTransformationMatrix();
	}

	void *x3dBillboard::creator()
	{
		return new x3dBillboard();
	}

	MStatus x3dBillboard::initialize()
	{
		MStatus stat;
		MFnNumericAttribute numFn;

		numFn.setMin(0.0);
		numFn.setMax(1.0);

		MObject axisX = numFn.create("axisX", "axx", MFnNumericData::kFloat);
		MObject axisY = numFn.create("axisY", "axy", MFnNumericData::kFloat);
		MObject axisZ = numFn.create("axisZ", "axz", MFnNumericData::kFloat);

		axisOfRotation = numFn.create("axisOfRotation", "aor", axisX, axisY, axisZ);
		addAttribute( axisOfRotation );
		addAttribute( axisX );
		addAttribute( axisY );
		addAttribute( axisZ );

		return MS::kSuccess;
	}
