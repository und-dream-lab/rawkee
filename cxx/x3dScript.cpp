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

// File: x3dScript.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dScript
//-----------------------------------------------
	const MTypeId x3dScript::typeId( 0x00108F63 );
	const MString x3dScript::typeName( "x3dScript" );

	MObject x3dScript::mustEvaluate;
	MObject x3dScript::directOutput;

	MObject x3dScript::fieldName;
	MObject x3dScript::fieldAccess;
	MObject x3dScript::fieldType;

	MObject x3dScript::x3dfc;
	MObject x3dScript::x3dlc;
	MObject x3dScript::x3drc;

	MObject x3dScript::x3dll;
	MObject x3dScript::x3drl;

	MObject x3dScript::fieldValue;

	MObject x3dScript::localScript;
	MObject x3dScript::remoteScript;

	MObject x3dScript::x3dbc;


	MStatus x3dScript::initialize()
	{
		MFnNumericAttribute numFn;
		MFnTypedAttribute typeFn;

		x3dfc = numFn.create("x3dFieldCount", "x3dfc", MFnNumericData::kInt, 0);
		MFnAttribute fcNum(x3dfc);
		fcNum.setHidden(true);
		addAttribute(x3dfc);

		x3dbc = numFn.create("x3dBackCount", "x3dbc", MFnNumericData::kInt, 0);
		MFnAttribute bcNum(x3dbc);
		bcNum.setHidden(true);
		addAttribute(x3dbc);

//		x3dlc = numFn.create("x3dLocalCount", "x3dlc", MFnNumericData::kInt, 0);
		x3dlc = numFn.create("localScript_cc", "lscc", MFnNumericData::kInt, 0);
		MFnAttribute lcNum(x3dlc);
		lcNum.setHidden(true);
		addAttribute(x3dlc);

		x3drc = numFn.create("remoteScript_cc", "rscc", MFnNumericData::kInt, 0);
		MFnAttribute rcNum(x3drc);
		rcNum.setHidden(true);
		addAttribute(x3drc);

		x3dll = numFn.create("x3dLocalLast", "x3dll", MFnNumericData::kInt, 1);
		MFnAttribute llNum(x3dll);
		llNum.setHidden(true);
		addAttribute(x3dll);

		x3drl = numFn.create("x3dRemoteLast", "x3drl", MFnNumericData::kInt, 1);
		MFnAttribute rlNum(x3drl);
		rlNum.setHidden(true);
		addAttribute(x3drl);

		mustEvaluate = numFn.create("mustEvaluate", "me", MFnNumericData::kBoolean, false);
		addAttribute(mustEvaluate);

		directOutput = numFn.create("directOutput", "dOut", MFnNumericData::kBoolean, false);
		addAttribute(directOutput);

		fieldName = typeFn.create("fieldName", "fieldN", MFnData::kString);

		MFnTypedAttribute arrayFn1(fieldName);
		arrayFn1.setArray(true);
		arrayFn1.setHidden(true);

		addAttribute(fieldName);

		fieldAccess = typeFn.create("fieldAccess", "fieldA", MFnData::kString);

		MFnTypedAttribute arrayFn2(fieldAccess);
		arrayFn2.setArray(true);
		arrayFn2.setHidden(true);

		addAttribute(fieldAccess);

		fieldType = typeFn.create("fieldType", "fieldT", MFnData::kString);

		MFnTypedAttribute arrayFn3(fieldType);
		arrayFn3.setArray(true);
		arrayFn3.setHidden(true);

		addAttribute(fieldType);

		localScript = typeFn.create("localScript", "lScript", MFnData::kString);
		MFnAttribute lsFn(localScript);
		lsFn.setHidden(true);
		lsFn.setArray(true);
		addAttribute(localScript);

		remoteScript = typeFn.create("remoteScript", "rScript", MFnData::kString);
		MFnAttribute rsFn(remoteScript);
		rsFn.setHidden(true);
		rsFn.setArray(true);
		addAttribute(remoteScript);

		return MS::kSuccess;
	}

	void *x3dScript::creator()
	{
		return new x3dScript;
	}
