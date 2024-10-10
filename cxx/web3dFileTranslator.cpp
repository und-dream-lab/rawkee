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

// File: web3dFileTranslator.cpp
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

//x3dExportOrganizer x3dEO;
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
MString web3dFileTranslator::defaultExtension() const
{
	//returns the default file extension
	MString fileExtension("");
	return fileExtension;
}

MString web3dFileTranslator::filter() const
{
	MString fileFilter("*.*");
	return fileFilter;
}
//**********************************************
//**********************************************

///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//Constructors and destructors used to 
//create/destroy the web3dFileTranslator object
//-----------------------------------------
web3dFileTranslator::web3dFileTranslator()
{
}

web3dFileTranslator::~web3dFileTranslator()
{
	//destructor method
}

//*************************************************
//*************************************************

///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//Required File Transaltor methods
//---------------------------------------
//All File Interpreter plug-ins must implement this method
//This method tells Maya whether or not it can write out files
//for this file format.
//---------------------------------------
bool web3dFileTranslator::haveWriteMethod() const 
{
	return true;
}

//---------------------------------------
//All File Interpreter plug-ins must implement this method
//This method tells Maya whether or not it can read in files
//for this file format.
//---------------------------------------
bool web3dFileTranslator::haveReadMethod() const 
{
	return false;
}

//---------------------------------------
//All File Interpreter plug-ins must implement this method.
//This method tells Maya whether or not it can read open
//and import files, or just open files.
//It is currently set to true, meaning the plugin is allowed
//to do both. Future version of RawKee will have this capability,
//but for now the value is ignored.
//---------------------------------------
bool web3dFileTranslator::canBeOpened() const 
{
	return true; //true means open and import - false means import only.
}
//***************************************
//***************************************

void * web3dFileTranslator::creator()
{
	return new web3dFileTranslator;
}

MStatus web3dFileTranslator::writer(const MFileObject& file, const MString& optionsString, FileAccessMode mode) 
{
	MGlobal::executeCommand("setX3DProcTreeTrue");
	MGlobal::executeCommand("processNonFileTextures");

	x3dExportOrganizer newX3dEO;
	this->x3dEO = newX3dEO;
	
	x3dEO.isDone = false;
	x3dEO.isTreeBuilding = false;
	x3dEO.hasPassed = false;

	//In the next two lines we are getting the file
	//path to the directory in which we are writing
	//the X3D file. Since we are using the
	//MFileObject of the Maya API to get this
	//information, the path name is returned
	//in a format that is appropriate to the
	//operating system that is being used.
	x3dEO.fileName = file.fullName();
	

	x3dEO.localPath = file.path();

	//Opens an output stream to a new file.
	ofstream tempFile(x3dEO.fileName.asChar(), ios::out);

	//points the newFile object to tempFile so that
	//we can use newFile as the file object for writing
	//later on.
	x3dEO.setFileSax3dWriter(tempFile);
	x3dEO.setExportStyle(filter());

	x3dEO.optionsString.operator =(optionsString);
	
	x3dEO.organizeExport();

	x3dEO.sax3dw.profileType.set("Immersive");	
	x3dEO.sax3dw.version.set("3.1");
	x3dEO.setAdditionalComps();

	//Adds a comment that we are using version 0.1 of the RawKee Maya exporter.
	MString commentValue("RawKee (version ");
	commentValue += RAWKEE_versionMajor;
	commentValue += ".";
	commentValue += RAWKEE_versionMinor;
	commentValue += ".";
	commentValue += RAWKEE_versionPoint;
	commentValue += "): an open source X3D plug-in for Maya";
	MString commentName("created_with");
	x3dEO.sax3dw.comments.clear();
	x3dEO.sax3dw.commentNames.clear();
	x3dEO.sax3dw.comments.append(commentValue);
	x3dEO.sax3dw.commentNames.append(commentName);

	//Checks to make sure that newFile actually exists before 
	//deciding whether or not to continue the export process.
	if (!x3dEO.sax3dw.newFile)
	{
		//Obviously the export has failed because we can't open
		//an output stream to the file, and we are now notifying
		//the user as to the problem.
		x3dEO.sax3dw.msg.set("");
		x3dEO.sax3dw.msg.operator +=(x3dEO.fileName);
		x3dEO.sax3dw.msg.operator +=(": an output stream could be openned to the file. We cannot tell you why, sorry.");
		cerr << x3dEO.sax3dw.msg.asChar() << endl;

		//We return a failure MStatus to Maya, the export process ends here.
		return MS::kFailure;
	}
	else
	{
		

		//Opening an output stream to our file has been 
		//successful, we will now continue with the export
		//process.
		tempFile.setf(ios::unitbuf);	//Tells the stream to flush after

		//Writes out the header for the X3D file.
		x3dEO.sax3dw.startDocument();
			
			//This method puts media files at the front of the X3D file
			//in a hiddens X3D Switch Node so that image, movie, and 
			//sound nodes load as soon as possible.
//			x3dEO.writeHiddenNodes();

			//This method traverses the Directed Acyclic Graph
			//calls the appropriate methods to export Maya
			//nodes it comes across.
			if(mode == kExportActiveAccessMode) {
			  	// export selected objects only
				x3dEO.exportSelected();
			} else {
			  	// export all objects
				x3dEO.exportAll();
			}

			x3dEO.writeRoutes();

		//Writes out the footer for the X3D file.
		x3dEO.sax3dw.endDocument();
		//Closing the output stream to our exprorted file.

		tempFile.flush();
		tempFile.close();

		//Notifying the content author that the export process has completed
		//and where the file is located on the author's computer.
		x3dEO.sax3dw.msg.set("Export Complete! Please refer to the following file:\n");
		x3dEO.sax3dw.msg.operator +=(x3dEO.fileName);		
		cout << x3dEO.sax3dw.msg.asChar() << endl;

		bool isComplete = false;
		bool isClosed = false;
		while(!isComplete || !isClosed)
		{
			MGlobal::displayInfo("Waiting to delete.\n");
			if(x3dEO.isDone && !isComplete)
			{
				MGlobal::executeCommand("delete_rawkee_export_files");
				MGlobal::executeCommand("setX3DProcTreeFalse");
				MGlobal::executeCommand("clearAllRawKeeKVs");
				isComplete = true;
			}
			if(!tempFile.is_open() && !isClosed)
			{
				if(x3dEO.exEncoding == X3DBENC) MGlobal::executeCommand("convertToX3DB(\""+x3dEO.fileName+"\")");
				isClosed = true;
			}
		}

		//This method must return a MStatus value.
		//Tells maya that the file translation process has completed.

		
		return MS::kSuccess;
	}
}
