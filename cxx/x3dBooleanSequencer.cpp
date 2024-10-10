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

// File: x3dBooleanSequencer.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dBooleanSequencer
//-----------------------------------------------
	const MTypeId x3dBooleanSequencer::typeId( 0x00108F08 );
	const MString x3dBooleanSequencer::typeName( "x3dBooleanSequencer" );

	MObject x3dBooleanSequencer::key;
	MObject x3dBooleanSequencer::key_cc;
	MObject x3dBooleanSequencer::keyValue;
	MObject x3dBooleanSequencer::keyValue_cc;

	MObject x3dBooleanSequencer::everyFrame;
	MObject x3dBooleanSequencer::startFrame;
	MObject x3dBooleanSequencer::stopFrame;
	MObject x3dBooleanSequencer::secondLength;
	MObject x3dBooleanSequencer::fps;


	MStatus x3dBooleanSequencer::compute(const MPlug &plug, MDataBlock &data){
		MStatus stat;
		if(plug == secondLength)
		{
			MDataHandle slHnd = data.outputValue(secondLength);
			MDataHandle sttfHnd = data.inputValue(startFrame);
			MDataHandle stpfHnd = data.inputValue(stopFrame);
			MDataHandle fpsHnd = data.inputValue(fps);

			int fpsVal = fpsHnd.asInt();

			double startFloat = sttfHnd.asDouble();
			double stopFloat = stpfHnd.asDouble();
			double seconds = (stopFloat - startFloat) /  static_cast<double>(fpsVal);

			if(seconds < 0) seconds = 0;

			slHnd.set(seconds);

			data.setClean(plug);
			stat = MS::kSuccess;
		}
		else if (plug == key_cc)
		{
			MDataHandle kHnd = data.outputValue(key_cc);
			MDataHandle sttfHnd = data.inputValue(startFrame);
			MDataHandle stpfHnd = data.inputValue(stopFrame);
			MDataHandle efHnd = data.inputValue(everyFrame);

			double eFrame = efHnd.asDouble();
			double startFloat = sttfHnd.asDouble();
			double stopFloat = stpfHnd.asDouble();
			double denom = stopFloat - startFloat;

			double dKeyLen = denom/eFrame;
			if(dKeyLen<0) dKeyLen = dKeyLen * -1;
			unsigned int keyLen = static_cast<int>(dKeyLen);
			if(keyLen ==0) keyLen = 1;

			int kl = keyLen;
			kHnd.set(kl);
			data.setClean(plug);
		}
		else if (plug == keyValue_cc)
		{
			MDataHandle kHnd = data.outputValue(keyValue_cc);
			MDataHandle sttfHnd = data.inputValue(startFrame);
			MDataHandle stpfHnd = data.inputValue(stopFrame);
			MDataHandle efHnd = data.inputValue(everyFrame);

			double eFrame = efHnd.asDouble();
			double startFloat = sttfHnd.asDouble();
			double stopFloat = stpfHnd.asDouble();
			double denom = stopFloat - startFloat;

			double dKeyLen = denom/eFrame;
			if(dKeyLen<0) dKeyLen = dKeyLen * -1;
			unsigned int keyLen = static_cast<int>(dKeyLen);
			if(keyLen ==0) keyLen = 1;

			int kl = keyLen;
			kHnd.set(kl);
			data.setClean(plug);
		}
		else if (plug == key)
		{
			MString keyString("");
			MDataHandle kHnd = data.outputValue(key);
			MDataHandle sttfHnd = data.inputValue(startFrame);
			MDataHandle stpfHnd = data.inputValue(stopFrame);
			MDataHandle efHnd = data.inputValue(everyFrame);

			double eFrame = efHnd.asDouble();
			double startFloat = sttfHnd.asDouble();
			double stopFloat = stpfHnd.asDouble();
			double denom = stopFloat - startFloat;

			double dKeyLen = denom/eFrame;

			double keyPer = eFrame/denom;
			if(keyPer < 0) keyPer = keyPer * -1;

			if(dKeyLen<0) dKeyLen = dKeyLen * -1;
			unsigned int keyLen = static_cast<int>(dKeyLen);

			if(keyLen == 0) keyLen = 1;

			MObject obj = thisMObject();
			MFnDependencyNode depNode(obj);

			MPlug aPlug = depNode.findPlug("key");

			unsigned int i;
			for(i=0;i<=keyLen;i++)
			{
				MPlug bPlug = aPlug.elementByPhysicalIndex(i);
				double cKey = i * keyPer;
				if(i == 0) bPlug.setValue(0);
				else if(i==keyLen) bPlug.setValue(1);
				else bPlug.setValue(cKey);
			}
			data.setClean(plug);
			stat = MS::kSuccess;
		}
		else
		{
			stat = MS::kUnknownParameter;
		}
		return stat;
	}

	MStatus x3dBooleanSequencer::initialize()
	{
		MFnNumericAttribute numFn;
		MFnTypedAttribute typFn;
		MStatus stat;

		everyFrame = numFn.create("keysEverySoOften", "keso", MFnNumericData::kDouble);
		numFn.setObject(everyFrame);
		numFn.setDefault(1.0);
		numFn.setMin(1.0);
		numFn.setMax(100.0);

		startFrame = numFn.create("startFrame", "strf", MFnNumericData::kDouble);
		numFn.setObject(startFrame);
		numFn.setDefault(0.0);

		stopFrame = numFn.create("stopFrame", "stpf", MFnNumericData::kDouble);
		numFn.setObject(stopFrame);
		numFn.setDefault(0.0);

		secondLength = numFn.create("secondLength", "sl", MFnNumericData::kDouble);
		numFn.setObject(secondLength);
		numFn.setDefault(0.0);

		fps = numFn.create("framesPerSecond", "fps", MFnNumericData::kInt);
		numFn.setObject(fps);
		numFn.setDefault(30);
		numFn.setMin(1);
		numFn.setMax(60);

		addAttribute(everyFrame);
		addAttribute(startFrame);
		addAttribute(stopFrame);
		addAttribute(secondLength);
		addAttribute(fps);

		attributeAffects(fps, secondLength);
		attributeAffects(startFrame, secondLength);
		attributeAffects(stopFrame, secondLength);

		key = numFn.create("key", "ky", MFnNumericData::kFloat);
		numFn.setObject(key);
		numFn.setArray(true);
		numFn.setHidden(true);
		addAttribute( key );
		
		key_cc = numFn.create("key_cc", "kycc", MFnNumericData::kInt, 2);
		numFn.setObject(key_cc);
		numFn.setHidden(true);
		addAttribute( key_cc );
		
		keyValue = numFn.create("keyValue", "kv", MFnNumericData::kBoolean);//kVectorArray);
		numFn.setObject(keyValue);
		numFn.setArray(true);
		numFn.setHidden(true);
		addAttribute( keyValue );

		keyValue_cc = numFn.create("keyValue_cc", "kvcc", MFnNumericData::kInt, 2);//kVectorArray);
		numFn.setObject(keyValue_cc);
		numFn.setHidden(true);
		addAttribute( keyValue_cc );

		attributeAffects(everyFrame, key);
		attributeAffects(startFrame, key);
		attributeAffects(stopFrame, key);

		attributeAffects(everyFrame, key_cc);
		attributeAffects(startFrame, key_cc);
		attributeAffects(stopFrame, key_cc);

		attributeAffects(everyFrame, keyValue_cc);
		attributeAffects(startFrame, keyValue_cc);
		attributeAffects(stopFrame, keyValue_cc);

		return MS::kSuccess;
	}

	void *x3dBooleanSequencer::creator()
	{
		return new x3dBooleanSequencer();
	}
