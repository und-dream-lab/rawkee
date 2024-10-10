#ifndef __WEBX3DEXPORTER_H
#define __WEBX3DEXPORTER_H

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

// File: webX3DExporter.h
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

class webX3DExporter:public MPxCommand
{
	public:
		virtual MStatus			doIt( const MArgList& args );

		static	void*			creator();
		static	void			constructWeb3DScenegraphTree(unsigned int exportType, MString optionsString, bool isFrom);

		static	void			afterFile( void* clientData );
		static	void			runFileSetup();

		static	void			setRawKeeNodeAdded(MObject & node, void* clientData);
		static	void			setRawKeeNodeRemoved(MObject & node, void* clientData);
		static	void			showSelectedRoute(void* clientData);
		static	void			rawKeeIsRenaming(MObject & node, void* clientData);
		static	void			trackSelfDelete(MNodeMessage::AttributeMessage msg, MPlug &plug, MPlug &otherPlug, void *clientData);
		static	void			changeSwitchVisibility(MNodeMessage::AttributeMessage msg, MPlug &plug, MPlug &otherPlug, void *clientData);
		static	void			rawKeeNodeSetups(MObject & node);
		static	void			x3dSceneUpdateMethod(void* clientData);
		static	void			runWeb3dSGFromAPI(int updateMethod);//, MString oldName);
		static	MFnDependencyNode	getMyDepNode(MString nodeName);
		static	MObject		getMyDepNodeObj(MString nodeName);

	private:
//		static void				addTextureAttributes(MFnDependencyNode depNode);
		static void				addTextureAttributes(MObject mObj);

};

#endif
