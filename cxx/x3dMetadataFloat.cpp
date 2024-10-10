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

// File: x3dMetadataFloat.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dMetadataFloat
//-----------------------------------------------
	const MTypeId x3dMetadataFloat::typeId( 0x00108F41 );
	const MString x3dMetadataFloat::typeName( "x3dMetadataFloat" );

	MObject x3dMetadataFloat::name;
	MObject x3dMetadataFloat::reference;
	MObject x3dMetadataFloat::valueButton;
	MObject x3dMetadataFloat::value;

	void *x3dMetadataFloat::creator()
	{
		return new x3dMetadataFloat();
	}

	MStatus x3dMetadataFloat::initialize()
	{
		MFnTypedAttribute typFn;
		MFnNumericAttribute numFn;
		MFnStringData sd;
		MObject defString = sd.create("");

		name = typFn.create("name", "nam", MFnData::kString, defString);
		addAttribute( name );

		reference = typFn.create("reference", "ref", MFnData::kString, defString);
		addAttribute( reference );

		valueButton = numFn.create("value_cc", "vcc", MFnNumericData::kInt, 0);
		addAttribute( valueButton );

		value = numFn.create("value", "val", MFnNumericData::kFloat);
		MFnNumericAttribute arrayVal(value);
		arrayVal.setArray(true);
//		arrayVal.setHidden(true);
		addAttribute(value);
		
		return MS::kSuccess;
	}
