//
// Copyright (C) 2004, 2005 North Dakota State University (http://atl.ndsu.edu/resources/maya_x3d.php) 
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

// File: x3dbFileTranslator.cpp
//
// Author: Maya SDK Wizard
//
//         Aaron Bergstrom
//         Computer Visualization Manger
//         NDSU Archaeology Technologies Laboratory
//         http://atl.ndsu.edu/
//
//*M* - means: As stated by the Maya API documentation
// LastUpdated: Thursday, Dec 30 - 2004
// 

#include <rawkee/impl.h>

///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//Method for Maya's plug-in interface to get
//the default file extension for the file
//type to be exported.
//
//It is possible to add more than one extension
//to a particular file type for plug-in export
//purposes. Not entirely sure how this is done
//But must add x3dv and x3db extensions as well.
//-----------------------------------------
MString x3dbFileTranslator::defaultExtension() const
{
	//returns the default file extension
	MString fileExtension("x3d");
	return fileExtension;
}

MString x3dbFileTranslator::filter() const
{
	MString fileFilter("*.x3db");
	return fileFilter;
}

void * x3dbFileTranslator::creator()
{
	return new x3dbFileTranslator;
}
