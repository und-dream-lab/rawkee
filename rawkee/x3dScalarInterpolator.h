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

// File: x3dScalarInterpolator.h
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#ifndef __x3dScalarInterpolator_H
#define __x3dScalarInterpolator_H

//-----------------------------------------------
//x3dScalarInterpolator Node Functions and NodeID#
//
	class x3dScalarInterpolator : public MPxLocatorNode
	{
	public:

		typedef MPxLocatorNode ParentClass;
		virtual MStatus compute( const MPlug& plug, MDataBlock& data );
		
		static void *creator();
		static MStatus initialize();
		static const MTypeId typeId;
		static const MString typeName;

		static MObject key;
		static MObject key_cc;
		static MObject keyValue;
		static MObject keyValue_cc;
		static MObject everyFrame;
		static MObject startFrame;
		static MObject stopFrame;
		static MObject secondLength;
		static MObject fps;

	};

//
//
//-----------------------------------------------
#endif
