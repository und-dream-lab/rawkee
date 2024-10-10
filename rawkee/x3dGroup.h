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

// File: x3dGroup.h
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#ifndef __x3dGroup_H
#define __x3dGroup_H

class x3dGroup : public MPxTransform
{
	public:
		typedef MPxTransform ParentClass;
		x3dGroup();
		x3dGroup(MPxTransformationMatrix *);
		virtual ~x3dGroup();
		virtual MPxTransformationMatrix *createTransformationMatrix();
		virtual MStatus computeLocalTransformation(MPxTransformationMatrix *, MDataBlock &);

		static void * creator();
		static MStatus initialize();
		static const MTypeId typeId;
		static const MString typeName;

};
#endif
