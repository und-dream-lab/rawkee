#ifndef __WEB3DFILETRANSLATOR_H
#define __WEB3DFILETRANSLATOR_H

//
// Copyright (C) 2005 North Dakota State University (http://atl.ndsu.edu/resources/maya_x3d.php) 
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

// File: web3dFileTranslator.h
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

class web3dFileTranslator:public MPxFileTranslator {

	public:
								web3dFileTranslator();
		virtual					~web3dFileTranslator();

		virtual MStatus			writer (const MFileObject& file, const MString& optionsString, MPxFileTranslator::FileAccessMode mode);

		virtual bool			haveWriteMethod () const;
		virtual bool			haveReadMethod () const;
		virtual	bool			canBeOpened () const;
		
		MString			defaultExtension () const;
		MString         filter() const;
		static void*			creator();

//		MStatus		processSceneGraph(MPxFileTranslator::FileAccessMode mode);
//		MStatus			exportAll();
//		MStatus			exportSelected();

		x3dExportOrganizer		x3dEO;
};

#endif
