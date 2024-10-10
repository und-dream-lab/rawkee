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

// File: x3dVisibilitySensor.h
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#ifndef __x3dVisibilitySensor_H
#define __x3dVisibilitySensor_H

//-----------------------------------------------
//x3dVisibilityhSensor Node Functions and NodeID#
//
	class x3dVisibilitySensor : public MPxLocatorNode
	{
	public:

		typedef MPxLocatorNode ParentClass;
		virtual void draw(M3dView &view, const MDagPath &path, M3dView::DisplayStyle style, M3dView::DisplayStatus status);
		virtual bool isBounded() const;
		virtual MBoundingBox boundingBox() const;

		static void *creator();
		static MStatus initialize();
		static const MTypeId typeId;
		static const MString typeName;

		static MObject enabled;
		static MObject visCenter;
		static MObject visSize;

	private:
		bool getBoxPoints(MPointArray &pts )const;
	};
//-----------------------------------------------
#endif
