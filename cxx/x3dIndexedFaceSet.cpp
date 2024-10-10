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

// File: x3dIndexedFaceSet.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

	const MTypeId x3dIndexedFaceSet::typeId( 0x00108F32 );
	const MString x3dIndexedFaceSet::typeName( "x3dIndexedFaceSet" );
	MObject x3dIndexedFaceSet::ccw;

	MObject x3dIndexedFaceSet::colorIndex;
	MObject x3dIndexedFaceSet::colorPerVertex;

	MObject x3dIndexedFaceSet::convex;

	MObject x3dIndexedFaceSet::creaseAngle;

	MObject x3dIndexedFaceSet::normalIndex;
	MObject x3dIndexedFaceSet::normalPerVertex;

	MObject x3dIndexedFaceSet::solid;

	MObject x3dIndexedFaceSet::coordIndex;

	MObject x3dIndexedFaceSet::texCoordIndex;



	x3dIndexedFaceSet::x3dIndexedFaceSet():ParentClass()
	{
	}

	x3dIndexedFaceSet::x3dIndexedFaceSet(MPxTransformationMatrix *tm):ParentClass(tm)
	{
	}

	x3dIndexedFaceSet::~x3dIndexedFaceSet()
	{
	}

	MStatus x3dIndexedFaceSet::computeLocalTransformation(MPxTransformationMatrix *xform, MDataBlock &block)
	{
		return ParentClass::computeLocalTransformation(xform, block);
	}

	MPxTransformationMatrix *x3dIndexedFaceSet::createTransformationMatrix()
	{
		return new MPxTransformationMatrix();
	}

	void *x3dIndexedFaceSet::creator()
	{
		return new x3dIndexedFaceSet();
	}

	MStatus x3dIndexedFaceSet::initialize()
	{
		MStatus status;
		MFnNumericAttribute numFn;
		MFnTypedAttribute typFn;

		MFnStringData sd;
		MObject defString = sd.create("");

		ccw = numFn.create("ccw", "cc", MFnNumericData::kBoolean, true);
		addAttribute( ccw );

		colorPerVertex = numFn.create("colorPerVertex", "cpv", MFnNumericData::kBoolean, true);
		addAttribute( colorPerVertex );

		convex = numFn.create("convex", "conv", MFnNumericData::kBoolean, true);
		addAttribute( convex );

		normalPerVertex = numFn.create("normalPerVertex", "npv", MFnNumericData::kBoolean, true);
		addAttribute( normalPerVertex );

		creaseAngle = numFn.create("creaseAngle", "cAngle", MFnNumericData::kFloat, 0.0);
		MFnNumericAttribute numFn2( creaseAngle );
		numFn2.setMin(0.0);
		numFn2.setMax(3.141592);
		addAttribute( creaseAngle );

		solid = numFn.create("solid", "soli", MFnNumericData::kBoolean, true);
		addAttribute( solid );

		coordIndex = typFn.create("coordIndex", "coordInd", MFnData::kIntArray);
		addAttribute( coordIndex );

		texCoordIndex = typFn.create("texCoordIndex", "texCoordInd", MFnData::kIntArray);
		addAttribute( texCoordIndex );

		colorIndex = typFn.create("colorIndex", "colorInd", MFnData::kIntArray);
		addAttribute( colorIndex );

		normalIndex = typFn.create("normalIndex", "normalInd", MFnData::kIntArray);
		addAttribute( normalIndex );


		return status;
	}
