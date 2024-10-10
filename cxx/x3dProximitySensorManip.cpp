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

// File: x3dProximitySensorManip.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

	const MTypeId x3dProximitySensorManip::typeId( 0x00108F7E );
	const MString x3dProximitySensorManip::typeName("x3dProximitySensorManip");

	MDagPath x3dProximitySensorManip::fFreePointManip;

	x3dProximitySensorManip::x3dProximitySensorManip()
	{
	}
	x3dProximitySensorManip::~x3dProximitySensorManip()
	{
	}

	void *x3dProximitySensorManip::creator()
	{
		return new x3dProximitySensorManip();
	}

	MStatus x3dProximitySensorManip::initialize()
	{ 
		MStatus stat;
		stat = MPxManipContainer::initialize();
		return stat;
	}

	MStatus x3dProximitySensorManip::createChildren()
	{
		MStatus stat = MStatus::kSuccess;
		fFreePointManip = addFreePointTriadManip("pointManip", "freePoint");
		return stat;
	}

	MStatus x3dProximitySensorManip::connectToDependNode(const MObject & node)
	{
		MStatus stat;

		MFnDependencyNode nodeFn(node);
		MPlug tPlug = nodeFn.findPlug("proxCenter", &stat);

		MFnFreePointTriadManip freePointManipFn(fFreePointManip);
		freePointManipFn.connectToPointPlug(tPlug);

		// 
		// Manipulator transformations can be set by using methods on the base 
		// class MFnTransform.  To display the manipulator at a constant offset 
		// from its natural position, change the value of the offset vector below.
		//

		MVector offset(0.0, 0.0, 0.0);
		freePointManipFn.setTranslation(offset, MSpace::kTransform);

		finishAddingManips();
		MPxManipContainer::connectToDependNode(node);		

		return stat;
	}

	void x3dProximitySensorManip::draw(M3dView & view, 
					 const MDagPath & path, 
					 M3dView::DisplayStyle style,
					 M3dView::DisplayStatus status)
	{
	//
	// Demonstrate how drawing can be overriden for manip containers - draw the
	// string "Stretch Me!" at the origin.
	//

	MPxManipContainer::draw(view, path, style, status);
	view.beginGL(); 

	MPoint textPos(0, 0, 0);
	char str[100];
	sprintf(str, "Stretch Me!"); 
	MString distanceText(str);
	view.drawText(distanceText, textPos, M3dView::kLeft);

	view.endGL();
}
