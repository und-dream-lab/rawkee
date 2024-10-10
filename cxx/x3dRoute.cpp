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

// File: x3dRoute.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dRoute
//-----------------------------------------------
	const MTypeId x3dRoute::typeId( 0x00108FFE );
	const MString x3dRoute::typeName( "x3dRoute" );

	MObject x3dRoute::fromNode;
	MObject x3dRoute::fromValue;
	MObject x3dRoute::selfDel;
	MObject x3dRoute::sdDoIt;
	MObject x3dRoute::checkString;
	MObject x3dRoute::toNode;
	MObject x3dRoute::toValue;
	MObject x3dRoute::x3dTypeFrom;
	MObject x3dRoute::x3dTypeTo;
	MObject x3dRoute::nameFrom1;
	MObject x3dRoute::nameFrom2;
	MObject x3dRoute::nameTo1;
	MObject x3dRoute::nameTo2;
	MObject x3dRoute::chopFrom;
	MObject x3dRoute::chopTo;
	
	void *x3dRoute::creator()
	{
		return new x3dRoute();
	}

	MStatus x3dRoute::compute(const MPlug &plug, MDataBlock &data){
		MStatus stat;
		if(plug == selfDel)
		{
			bool newBool = false;
			MDataHandle sdHnd = data.outputValue(selfDel);
			MDataHandle csHnd = data.inputValue(checkString);
			MDataHandle fromHnd = data.inputValue(fromNode);
			MDataHandle toHnd = data.inputValue(toNode);
			MString csString = csHnd.asString();
			MString fnString = fromHnd.asString();
			MString tnString = toHnd.asString();

			if(csString != "" && fnString != "" && tnString != "")
			{
				MStringArray nodeNames;
				bool fromVal = false;
				bool toVal = false;
				csString.split('*',nodeNames);

				unsigned int nnLen = nodeNames.length();
				unsigned int i;
				for(i=0;i<nnLen;i++)
				{
					if(nodeNames.operator [](i).operator ==(fnString)) fromVal = true;
					if(nodeNames.operator [](i).operator ==(tnString)) toVal = true;
				}
				if(fromVal != true || toVal != true) newBool = true;
			}
			sdHnd.set(newBool);
			data.setClean(plug);
			stat = MS::kSuccess;
		}
		if(plug == fromNode)
		{
			MDataHandle fromHnd = data.outputValue(fromNode);
			MDataHandle nfrom1Hnd = data.inputValue(nameFrom1);
			MDataHandle nfrom2Hnd = data.inputValue(nameFrom2);
			MString n1 = nfrom1Hnd.asString();
			MString n2 = nfrom2Hnd.asString();

			MString combined("");

			MStringArray endSplit;
			n2.split('*', endSplit);
			if(endSplit.length() > 1)
			{
				if(endSplit.operator [](1).operator ==("_x_"))
				{
					MString resName;
					resName.operator =(endSplit.operator [](0));
					resName.operator +=("_x_");
					combined.operator +=(resName);
					combined.operator +=(n1);
				}
			}else
			{
				combined.operator +=(n1);
				combined.operator +=(n2);
			}
			fromHnd.set(combined);
			data.setClean(plug);
			stat = MS::kSuccess;
		}
		if(plug == toNode)
		{
			MDataHandle toHnd = data.outputValue(toNode);
			MDataHandle nto1Hnd = data.inputValue(nameTo1);
			MDataHandle nto2Hnd = data.inputValue(nameTo2);
			MString n1 = nto1Hnd.asString();
			MString n2 = nto2Hnd.asString();
			MString combined("");

			MStringArray endSplit;
			n2.split('*', endSplit);
			if(endSplit.length() > 1)
			{
				if(endSplit.operator [](1).operator ==("_x_"))
				{
					MString resName;
					resName.operator =(endSplit.operator [](0));
					resName.operator +=("_x_");
					combined.operator +=(resName);
					combined.operator +=(n1);
				}
			}else
			{
				combined.operator +=(n1);
				combined.operator +=(n2);
			}
			toHnd.set(combined);
			data.setClean(plug);
			stat = MS::kSuccess;
		}
		if(plug == nameFrom1)
		{
			MDataHandle nHnd = data.outputValue(nameFrom1);
			MDataHandle chopHnd = data.inputValue(chopFrom);
			MDataHandle typeHnd = data.inputValue(x3dTypeFrom);
			MString chop = chopHnd.asString();
			MString type = typeHnd.asString();
			MStringArray theSplit = x3dSplitValue(chop, type);

			nHnd.set(theSplit.operator [](0));
			data.setClean(plug);
			stat = MS::kSuccess;
		}
		if(plug == nameFrom2)
		{
			MDataHandle nHnd = data.outputValue(nameFrom2);
			MDataHandle chopHnd = data.inputValue(chopFrom);
			MDataHandle typeHnd = data.inputValue(x3dTypeFrom);
			MString chop = chopHnd.asString();
			MString type = typeHnd.asString();
			MStringArray theSplit = x3dSplitValue(chop, type);

			nHnd.set(theSplit.operator [](1));
			data.setClean(plug);
			stat = MS::kSuccess;
		}
		if(plug == nameTo1)
		{
			MDataHandle nHnd = data.outputValue(nameTo1);
			MDataHandle chopHnd = data.inputValue(chopTo);
			MDataHandle typeHnd = data.inputValue(x3dTypeTo);
			MString chop = chopHnd.asString();
			MString type = typeHnd.asString();
			MStringArray theSplit = x3dSplitValue(chop, type);

			nHnd.set(theSplit.operator [](0));
			data.setClean(plug);
			stat = MS::kSuccess;
		}
		if(plug == nameTo2)
		{
			MDataHandle nHnd = data.outputValue(nameTo2);
			MDataHandle chopHnd = data.inputValue(chopTo);
			MDataHandle typeHnd = data.inputValue(x3dTypeTo);
			MString chop = chopHnd.asString();
			MString type = typeHnd.asString();
			MStringArray theSplit = x3dSplitValue(chop, type);

			nHnd.set(theSplit.operator [](1));
			data.setClean(plug);
			stat = MS::kSuccess;
		}
		else stat = MS::kUnknownParameter;
		return stat;
	}

	MStringArray x3dRoute::x3dSplitValue(MString chopMe, MString x3dType)
	{
		MStringArray newArray;
		int theChoice = -1;

		if(x3dType.operator ==("TextureTransform")) theChoice = 0;
		if(x3dType.operator ==("MultiTextureTransform")) theChoice = 1;
		if(x3dType.operator ==("MultiTexture")) theChoice = 2;
		if(x3dType.operator ==("ImageTexture") || x3dType.operator ==("PixelTexture")) theChoice = 3;
		if(x3dType.operator ==("MultiTextureCoordinate")) theChoice = 4;
		if(x3dType.operator ==("IndexedFaceSet")) theChoice = 5;
		if(x3dType.operator ==("Shape")) theChoice = 6;
		if(x3dType.operator ==("Coordinate")) theChoice = 7;
		if(x3dType.operator ==("Normal")) theChoice = 8;
		if(x3dType.operator ==("TextureCoordinate")) theChoice = 9;
		if(x3dType.operator ==("Color")) theChoice = 10;
		if(x3dType.operator ==("HAnimJoint")) theChoice = 11;

		unsigned int strlen = chopMe.length();
		MString endVal("");
		MString nodeName(chopMe);
		MStringArray chopArray;
		chopMe.split('_', chopArray);
		unsigned int cslen = chopArray.length();
		unsigned int evlen = 0;
		MStringArray jnArray;
		MString processor;

		switch(theChoice){
			case 0:
				if(strlen > 3)
				{
					endVal = chopMe.substring(strlen-3, strlen-1);
					if(endVal.operator ==("_tt")) nodeName = chopMe.substring(0,strlen-4);
					else endVal.operator =("");
				}
				break;
			case 1:
				if(strlen > 9)
				{
					endVal = chopMe.substring(strlen-9, strlen-1);
					if(endVal.operator ==("_multi_tt")) nodeName = chopMe.substring(0,strlen-10);
					else endVal.operator =("");
				}
				break;
			case 2:
				if(strlen > 8)
				{
					endVal = chopMe.substring(strlen-8, strlen-1);
					if(endVal.operator ==("_multi_t")) nodeName = chopMe.substring(0,strlen-9);
					else endVal.operator =("");
				}
				break;
			case 3:
				if(strlen > 14)
				{
					endVal = chopMe.substring(strlen-14, strlen-1);
					if(endVal.operator ==("_rawkee_export")) nodeName = chopMe.substring(0,strlen-15);
					else endVal.operator =("");
				}
				break;
			case 4:
				if(cslen > 2)
				{
					if(chopArray.operator [](cslen-1).operator ==("mtc"))
					{
						endVal.operator +=("_");
						endVal.operator +=(chopArray.operator [](cslen-2));
						endVal.operator +=("_");
						endVal.operator +=(chopArray.operator [](cslen-1));
						evlen = endVal.length()+1;
						nodeName = chopMe.substring(0,strlen-evlen);
					}
				}
				break;
			case 5:
				if(cslen > 1)
				{
					if(chopArray.operator [](cslen-1).operator ==("ifs"))
					{
						endVal.operator +=("_ifs");
						nodeName = chopMe.substring(0,strlen-5);
					}
					else if(chopArray.operator [](cslen-2).operator ==("ifs"))
					{
						endVal.operator +=("_");
						endVal.operator +=(chopArray.operator [](cslen-2));
						endVal.operator +=("_");
						endVal.operator +=(chopArray.operator [](cslen-1));
						evlen = endVal.length()+1;
						nodeName = chopMe.substring(0,strlen-evlen);
					}
				}
				break;
			case 6:
				if(cslen > 2)
				{
					if(chopArray.operator [](cslen-2).operator ==("rks"))
					{
						endVal.operator +=("_");
						endVal.operator +=(chopArray.operator [](cslen-2));
						endVal.operator +=("_");
						endVal.operator +=(chopArray.operator [](cslen-1));
						evlen = endVal.length()+1;
						nodeName = chopMe.substring(0,strlen-evlen);
					}
				}
				break;
			case 7:
				if(strlen > 6)
				{
					endVal = chopMe.substring(strlen-6, strlen-1);
					if(endVal.operator ==("_coord")) nodeName = chopMe.substring(0,strlen-7);
					else endVal.operator =("");
				}
				break;
			case 8:
				if(strlen > 7)
				{
					endVal = chopMe.substring(strlen-7, strlen-1);
					if(endVal.operator ==("_normal")) nodeName = chopMe.substring(0,strlen-8);
					else endVal.operator =("");
				}
				break;
			case 9:
				endVal.operator +=("_");
				endVal.operator +=(chopArray.operator [](cslen-2));
				endVal.operator +=("_");
				endVal.operator +=(chopArray.operator [](cslen-1));
				evlen = endVal.length()+1;
				nodeName = chopMe.substring(0,strlen-evlen);
				break;
			case 10:
				if(strlen > 6)
				{
					endVal = chopMe.substring(strlen-6, strlen-1);
					if(endVal.operator ==("_color")) nodeName = chopMe.substring(0,strlen-7);
					else endVal.operator =("");
				}
				break;
			case 11:
				if(strlen > 3)
				{
					unsigned int bj = 0;
					unsigned int ej = 2;
					bool fj = false;
					while (ej<strlen && fj == false)
					{
						processor = chopMe.substring(bj,ej);
						if(processor.operator ==("_x_"))
						{
							endVal.operator =(chopMe.substring(0,bj-1));
							endVal.operator +=("*");
							endVal.operator +=("_x_");
							nodeName = chopMe.substring(ej+1,strlen-1);
							fj = true;
						}else{
							bj = bj+1;
							ej = ej+1;
						}
					}
				}
				break;

			default:
				break;
		}
		newArray.append(nodeName);
		newArray.append(endVal);
		return newArray;
	}

	MStatus x3dRoute::initialize()
	{

		MFnTypedAttribute typeFn;
		fromNode = typeFn.create( "fromNode", "fn", MFnData::kString);
		typeFn.setObject(fromNode);
		typeFn.setHidden( true );

		toNode = typeFn.create( "toNode", "tn", MFnData::kString);
		typeFn.setObject(toNode);
		typeFn.setHidden( true );

		nameFrom1 = typeFn.create( "nameFrom1", "nf1", MFnData::kString);
		typeFn.setObject(nameFrom1);
		typeFn.setHidden(true);

		nameFrom2 = typeFn.create( "nameFrom2", "nf2", MFnData::kString);
		typeFn.setObject(nameFrom2);
		typeFn.setHidden(true);

		fromValue = typeFn.create("fromValue", "fv", MFnData::kString);
		typeFn.setObject(fromValue);
		typeFn.setHidden( true );

		toValue = typeFn.create("toValue", "tv", MFnData::kString);
		typeFn.setObject(toValue);
		typeFn.setHidden( true );

		nameTo1 = typeFn.create("nameTo1", "nt1", MFnData::kString);
		typeFn.setObject(nameTo1);
		typeFn.setHidden(true);

		nameTo2 = typeFn.create("nameTo2", "nt2", MFnData::kString);
		typeFn.setObject(nameTo2);
		typeFn.setHidden(true);

		x3dTypeFrom = typeFn.create("x3dTypeFrom", "x3dtf", MFnData::kString);
		typeFn.setObject(x3dTypeFrom);
		typeFn.setHidden(true);

		x3dTypeTo = typeFn.create("x3dTypeTo", "x3dtt", MFnData::kString);
		typeFn.setObject(x3dTypeTo);
		typeFn.setHidden(true);

		chopFrom = typeFn.create("chopFrom", "cfrom", MFnData::kString);
		typeFn.setObject(chopFrom);
		typeFn.setHidden(true);

		chopTo = typeFn.create("chopTo", "cto", MFnData::kString);
		typeFn.setObject(chopTo);
		typeFn.setHidden(true);

		MFnNumericAttribute numFn;
		selfDel = numFn.create("selfDelete", "seldel", MFnNumericData::kBoolean, false);
		numFn.setObject(selfDel);
		numFn.setHidden(true);

		sdDoIt = numFn.create("sdDoIt", "sddi", MFnNumericData::kBoolean, false);
		numFn.setObject(sdDoIt);
		numFn.setHidden(true);

		checkString = typeFn.create("checkString", "cStr", MFnData::kString);
		typeFn.setObject(checkString);
		typeFn.setHidden( true );

		addAttribute(checkString);
		addAttribute( selfDel);
		addAttribute( sdDoIt);

		addAttribute(x3dTypeFrom);
		addAttribute(x3dTypeTo);
		addAttribute(chopFrom);
		addAttribute(chopTo);
		addAttribute(nameFrom1);
		addAttribute(nameFrom2);
		addAttribute(nameTo1);
		addAttribute(nameTo2);

		addAttribute( fromNode );
		addAttribute( fromValue );
		addAttribute( toNode );
		addAttribute( toValue );

		attributeAffects(checkString, selfDel);
		attributeAffects(fromNode, selfDel);
		attributeAffects(toNode, selfDel);

		attributeAffects(chopFrom, nameFrom1);
		attributeAffects(x3dTypeFrom, nameFrom1);
		attributeAffects(chopFrom, nameFrom2);
		attributeAffects(x3dTypeFrom, nameFrom2);
		attributeAffects(chopTo, nameTo1);
		attributeAffects(x3dTypeTo, nameTo1);
		attributeAffects(chopTo, nameTo2);
		attributeAffects(x3dTypeTo, nameTo2);
		attributeAffects(nameFrom1, fromNode);
		attributeAffects(nameTo1, toNode);
		attributeAffects(nameFrom2, fromNode);
		attributeAffects(nameTo2, toNode);

		return MS::kSuccess;
	}
