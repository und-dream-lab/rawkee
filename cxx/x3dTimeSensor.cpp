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

// File: x3dTimeSensor.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dTimeSensor
//-----------------------------------------------
	const MTypeId x3dTimeSensor::typeId( 0x00108F72 );
	const MString x3dTimeSensor::typeName( "x3dTimeSensor" );

	MObject x3dTimeSensor::cycleInterval;
	MObject x3dTimeSensor::enabled;
	MObject x3dTimeSensor::loop;
	MObject x3dTimeSensor::pauseTime;
	MObject x3dTimeSensor::resumeTime;
	MObject x3dTimeSensor::startTime;
	MObject x3dTimeSensor::stopTime;

	MObject x3dTimeSensor::everyFrame;
	MObject x3dTimeSensor::startFrame;
	MObject x3dTimeSensor::stopFrame;
	MObject x3dTimeSensor::fps;

	MStatus x3dTimeSensor::compute(const MPlug &plug, MDataBlock &data){
		MStatus stat;
		if(plug == cycleInterval)
		{
			MDataHandle slHnd = data.outputValue(cycleInterval);
			MDataHandle sttfHnd = data.inputValue(startFrame);
			MDataHandle stpfHnd = data.inputValue(stopFrame);
			MDataHandle fpsHnd = data.inputValue(fps);

			int fpsVal = fpsHnd.asInt();

			double startFloat = sttfHnd.asDouble();
			double stopFloat = stpfHnd.asDouble();
			double seconds = (stopFloat - startFloat) / static_cast<double>(fpsVal);

			if(seconds < 0) seconds = 0;

			slHnd.set(seconds);

			data.setClean(plug);
			stat = MS::kSuccess;
		}
		else
		{
			stat = MS::kUnknownParameter;
		}
		return stat;
	}

	MStatus x3dTimeSensor::initialize()
	{
		MFnNumericAttribute numFn;
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

		fps = numFn.create("framesPerSecond", "fps", MFnNumericData::kInt);
		numFn.setObject(fps);
		numFn.setDefault(30);
		numFn.setMin(1);
		numFn.setMax(60);

		addAttribute(everyFrame);
		addAttribute(startFrame);
		addAttribute(stopFrame);
		addAttribute(fps);

		MFnNumericData nData;

		MFnNumericAttribute tAtt01a;
		cycleInterval = tAtt01a.create("cycleInterval", "ci", MFnNumericData::kDouble, 1.0);
		tAtt01a.setMin(0.0);
		addAttribute( cycleInterval );

		attributeAffects(fps, cycleInterval);
		attributeAffects(startFrame, cycleInterval);
		attributeAffects(stopFrame, cycleInterval);

		MFnNumericAttribute tAtt02a;
		enabled = tAtt02a.create("enabled", "enab", MFnNumericData::kBoolean, true);
		addAttribute( enabled );

		MFnNumericAttribute tAtt03a;
		loop = tAtt03a.create("loop", "loo", MFnNumericData::kBoolean, false);
		addAttribute( loop );

		MFnNumericAttribute tAtt05a;
		pauseTime = tAtt05a.create("pauseTime", "pt", MFnNumericData::kDouble, 0.0);
		addAttribute( pauseTime );

		resumeTime = tAtt05a.create("resumeTime", "rtx3d", MFnNumericData::kDouble, 0.0);
		//The short name for this attribute cannot be "rt" because it conflicts with
		//some Maya internal variable.
		addAttribute( resumeTime );

		MFnNumericAttribute tAtt07a;
		startTime = tAtt07a.create("startTime", "stat", MFnNumericData::kDouble, 0.0);
		addAttribute( startTime );

		MFnNumericAttribute tAtt08a;
		stopTime = tAtt08a.create("stopTime", "stot", MFnNumericData::kDouble, 0.0);
		addAttribute( stopTime );

		return MS::kSuccess;
	}

	void *x3dTimeSensor::creator()
	{
		return new x3dTimeSensor();
	}
