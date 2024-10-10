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

// File: x3dAnchor.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

	const MTypeId x3dAnchor::typeId( 0x00108F00 );
	const MString x3dAnchor::typeName( "x3dAnchor" );

	MObject x3dAnchor::parameter;
	MObject x3dAnchor::url;
	MObject x3dAnchor::description;
	MObject x3dAnchor::url_cc;
	MObject x3dAnchor::parameter_cc;

	x3dAnchor::x3dAnchor():ParentClass()
	{
	}

	x3dAnchor::x3dAnchor(MPxTransformationMatrix *tm):ParentClass(tm)
	{
	}

	x3dAnchor::~x3dAnchor()
	{
	}

	MStatus x3dAnchor::computeLocalTransformation(MPxTransformationMatrix *xform, MDataBlock &block)
	{
		return ParentClass::computeLocalTransformation(xform, block);
	}

	MPxTransformationMatrix *x3dAnchor::createTransformationMatrix()
	{
		return new MPxTransformationMatrix();
	}

	void *x3dAnchor::creator()
	{
		return new x3dAnchor();
	}

	MStatus x3dAnchor::initialize()
	{
		MStatus stat;
		MFnNumericAttribute numFn;
		MFnTypedAttribute tAttr;

		description = tAttr.create( "description", "desc", MFnData::kString);
		addAttribute( description );
	
		parameter_cc = numFn.create("parameter_cc", "pcc", MFnNumericData::kInt, 0);
		numFn.setObject(parameter_cc);
		numFn.setHidden(true);
		addAttribute( parameter_cc );

		url_cc = numFn.create("url_cc", "ucc", MFnNumericData::kInt, 0);
		numFn.setObject(url_cc);
		numFn.setHidden(true);
		addAttribute( url_cc );

		parameter = tAttr.create("parameter", "pmeter", MFnData::kString);
		tAttr.setObject(parameter);
		tAttr.setArray(true);
		addAttribute( parameter);

		url = tAttr.create("url", "u", MFnData::kString);
		tAttr.setObject(url);
		tAttr.setArray(true);
		addAttribute( url );

		return MS::kSuccess;
	}
