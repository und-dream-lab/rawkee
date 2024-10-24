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

// File: x3dExportOrganizer.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

///////////////////////////////
//NEW SECTION
///////////////////////////////
//---------------------------------------
//Variables used to hold optionVar values
//Names are generally the same as their
//MEL Counterparts
//---------------------------------------

#include <rawkee/impl.h>

bool x3dExportOrganizer::isTreeBuilding = false;;
bool x3dExportOrganizer::hasPassed = false;
bool x3dExportOrganizer::isDone = false;
bool x3dExportOrganizer::useRelURL = true;
bool x3dExportOrganizer::useRelURLW = true;
MString x3dExportOrganizer::x3dTreeStrings;
MString x3dExportOrganizer::x3dTreeDelStrings;
int x3dExportOrganizer::updateMethod = 0;
bool x3dExportOrganizer::fileOverwrite = false;
bool x3dExportOrganizer::exRigidBody = false;
bool x3dExportOrganizer::exHAnim = false;
bool x3dExportOrganizer::exIODevice = false;
bool x3dExportOrganizer::nonStandardHAnim = false;
unsigned int x3dExportOrganizer::exBCFlag = 1;
MStringArray x3dExportOrganizer::avatarMeshNames;
MDagPathArray x3dExportOrganizer::avatarDagPaths;

void x3dExportOrganizer::setFileSax3dWriter(ofstream &stream)
{
	sax3dw.newFile  = &stream;

}

void x3dExportOrganizer::setExportStyle(MString filter)
{
	if(!isTreeBuilding)
	{
		if(filter.operator ==("*.x3dv")) exEncoding = X3DVENC;
		else if(filter.operator ==("*.wrl")) exEncoding = VRML97ENC;
		else if(filter.operator ==("*.x3db")) exEncoding = X3DBENC;
		else exEncoding = X3DENC;
		sax3dw.exEncoding = exEncoding;
		web3dem.setExportEncoding(exEncoding);
	}
}

void x3dExportOrganizer::organizeExport()
{
cout << "Go 1" << endl;
		grabExporterOptions();	//This method extracts the export
								//options information for us from the 
								//optionVar variables.

cout << "Go 2" << endl;
		if(!isTreeBuilding) createResourceDir();	//This methods creates the local
								//directories in which we will
								//place any image, movie, or audio
								//files created or transferred
								//during the export process.
cout << "Go 3" << endl;

		if(!isTreeBuilding) textureSetup();			//This method evaluates the export
								//options for textures. If needed
								//the method changes the file format
								//of the image textures, the size of
								//textures, writes them or transfers
								//these files as necessary to the 
								//directory found in the images path 
								//designated by our export options.
								//Internal Maya textures are exported
								//at this time as well in the same
								//manner.

		if(!isTreeBuilding) soundSetup();			//This methods evaluates the export
								//options for audioClips in a manner
								//similar to the textureSetup method
								//above. Currently, no sound export
								//functionality has been implemented
								//so this method does nothing.
		if(!isTreeBuilding) inlineSetup();
//********************
//********************
		//REVIEW REVIEW REVIEW PREPAREUNDERWORLDNODES
		if(!isTreeBuilding) prepareUnderworldNodes();	//This method evaluates the 
									//RawKee underworld nodes such
									//as x3dIndexedFaceSet, x3dColor 
									//and x3dNormal in order to prepare
									//them for export. This includes any
									//required data collection.

//********************
//********************
		//REVIEW REVIEW REVIEW PREPAREINTERPOLATORNODES
		if(!isTreeBuilding) prepareInterpolatorNodes(); //This method evalutes the RawKee
									//interpolator nodes such as 
									//x3dPositionInterpolator and 
									//x3dOrientationInterpolator nodes
									//in order to prepare them for export.
									//This includes any required data
									//collection.

		sax3dw.clearMemberLists();
		setIgnoreStatusForDefaults();
		
}

x3dExportOrganizer::x3dExportOrganizer()
{
}

x3dExportOrganizer::~x3dExportOrganizer()
{
}


MString x3dExportOrganizer::optionsString;

//Tells us which encoding choice to use:
//0 Traditional, 1 XML, 2 Binary
int x3dExportOrganizer::exEncoding;

//Tells whether or not location-defined leaf nodes
//should be exported as syblings to their parents
bool x3dExportOrganizer::asSyblings;

bool x3dExportOrganizer::useEmpties = false;

//Tells whether or not to export Metadata
//0 No, 1 Yes
int x3dExportOrganizer::exMetadata;

//Tells us whether or not to export textures
//0 No, 1 Yes
int x3dExportOrganizer::exTextures;

//Tells us whether or not to export Audio files
//0 No, 1 Yes
int x3dExportOrganizer::exAudio;
int x3dExportOrganizer::exInline;

//Tells us whether or not the external X3D viewer should 
//be launched at the completion of the export. - Not yet implemented
int x3dExportOrganizer::launchExtern;

//Tells us the switch value for Texture Export.
//0 is current, 1 is gif, 2 is jpg, 3 is png
//Not to be confused with "exTextureFormat",
//which actually holds the string that 
//is the file extension.
//int x3dExportOrganizer::x3dTextureForInt;

//Tells us whether or not to consolidate external
//media into sub folders of the directory in 
//which the X3D file is written.
//0 No, 1 Yes
int x3dExportOrganizer::conMedia;

//Tells us whether or not to adjust the texture
//size of the textures we are using. If equal to
//1, the textures will be exported to the folder
//designated by the localImagePath variable.
//0 No, 1 Yes
//int x3dExportOrganizer::adjTexture;

//Tells us whether or not to save internal Maya
//Textures as external files. If equal to 1, the
//texture files will be exported to the folder
//designated by the localImagePath variable.
//0 No, 1 Yes
//int x3dExportOrganizer::saveMayaTex;
MString x3dExportOrganizer::tempTexturePath;

//Tells us whether or not ColorPerVertex data
//should be exported for those mesh nodes that
//have no geometry node defining this 
//parameter in these mesh's underworld.
//0 No, 1 Yes
//int x3dExportOrganizer::cpvNonD;

//Tells us whether or not NormalPerVertex data
//should be exported for those mesh nodes that
//have no geometry node defining this 
//parameter in these meshes' underworld.
//0 No, 1 Yes
int x3dExportOrganizer::npvNonD;

//Tells us whether or not the geometry of those
//mesh nodes that have no geometry node defining
//"solid" this parameter in these meshes' underworld
//is solid or not.
//0 No, 1 Yes
//int x3dExportOrganizer::solidGlobalValue;

//bool x3dExportOrganizer::internalPixel;
//bool x3dExportOrganizer::externalPixel;

//Tells us the size of what exported textures
//should be if they are created by Maya
//int x3dExportOrganizer::x3dTextureWidth;
//int x3dExportOrganizer::x3dTextureHeight;

//Tells us the creaseAngle of mesh nodes that
//do not have this parameter designated by
//an underworld geometry node.
float x3dExportOrganizer::caGlobalValue;

//Holds Export Type for external image files
//MString	x3dExportOrganizer::exTextureFormat;

//Holds the path to where the X3D File will be written
MString	x3dExportOrganizer::localPath;

//Holds the file name to where the X3D file will be written
MString x3dExportOrganizer::fileName;

//Holds the path starting below the localPath where image/movie
//files are stored
MString	x3dExportOrganizer::localImagePath;

//Holds the path starting below the localPath where audio files
//are stored
MString	x3dExportOrganizer::localAudioPath;
MString x3dExportOrganizer::localInlinePath;

//Holds the base url used in all URL fields - not yet implemented
MString	x3dExportOrganizer::exBaseURL;

//Holds the url used in URL fields of all textures
MString	x3dExportOrganizer::exTextureURL;

//Holds the url used in URL fields of AudioClip nodes
MString	x3dExportOrganizer::exAudioURL;
MString x3dExportOrganizer::exInlineURL;

MString x3dExportOrganizer::getTextureDir;

MString x3dExportOrganizer::getAudioDir;
MString x3dExportOrganizer::getInlineDir;

unsigned int x3dExportOrganizer::treeTabs;
unsigned int x3dExportOrganizer::ttabsMax = 0;
MStringArray x3dExportOrganizer::mayaArray;
MStringArray x3dExportOrganizer::x3dArray;

//const unsigned int x3dExportOrganizer::curUVSetLL;

//Specifies the command to load the exported X3D file into
//an external X3D viewer once export has been completed - not yet implemented
MString	x3dExportOrganizer::externLaunchCMD;
//*****************************************
//*****************************************

///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//Variables for checking that the mesh node
//has underworld nodes attached to it. For
//instance, if an x3dColor node was a 
//child of a mesh node, then hasColor would
// be true.
//-----------------------------------------
bool x3dExportOrganizer::hasColor;
bool x3dExportOrganizer::hasCoord;
bool x3dExportOrganizer::hasNormal;
bool x3dExportOrganizer::hasTexCoord;
bool x3dExportOrganizer::hasGeometry;
bool x3dExportOrganizer::hasTexture;	
//*****************************************
//*****************************************

///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//Arrays of Array Strings used to store the 
//names of nodes which have already been
//exported
//-----------------------------------------
MStringArray x3dExportOrganizer::textureNames;	//Not currently used
//*****************************************
//*****************************************

///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//Object used to get the Root of the
//DAG for export.
//-----------------------------------------
MObject x3dExportOrganizer::worldRoot;		
//*****************************************
//*****************************************

///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//This method extracts the export options information for us from the 
//optionVar variables
//-----------------------------------------
void x3dExportOrganizer::grabExporterOptions()
{

	//--------------------------------------------
	//User feedback letting the content author know
	//that the plugin is retrieving the export options.
	//--------------------------------------------
	if(!isTreeBuilding)
	{

		sax3dw.msg.set("Analyzing export options.");		
		cout << sax3dw.msg.asChar() << endl;
		sax3dw.msg.set(" ");
		cout << sax3dw.msg.asChar() << endl;
	}

	MStringArray inlineNodeArray = getInlineNodeNames();
	exInline = 0;
	if(inlineNodeArray.length() > 0) exInline = 1;

	MStringArray optionsArray;
	optionsString.split('*', optionsArray);
	unsigned int oaSize = optionsArray.length();
	unsigned int i;


	for(i=0; i<oaSize; i++)
	{
		if(optionsArray.operator [](i) == "x3dUseEmpties")
		{
			if(optionsArray.operator [](++i) == "0") useEmpties = false;
			else useEmpties = true;
		}
		else
		if(optionsArray.operator [](i) == "x3dExportMetadata")
		{
			if(optionsArray.operator [](++i) == "0") exMetadata = false;
			else exMetadata = true;
		}
		else
		if(optionsArray.operator [](i) == "x3dConsolidateMedia")
		{
			if(optionsArray.operator [](++i) == "0")
			{
				conMedia = false;
				web3dem.setConsolidate(false);
			}
			else
			{
				conMedia = true;
				web3dem.setConsolidate(true);
			}
		}
		else
		if(optionsArray.operator [](i) == "x3dFileOverwrite")
		{
			if(optionsArray.operator [](++i) == "0")
			{
				fileOverwrite = false;
			}
			else
			{
				fileOverwrite = true;
			}
		}
		else
		if(optionsArray.operator [](i) == "x3dExportTextures")
		{
			if(optionsArray.operator [](++i) == "0" ) exTextures = 0;
			else exTextures = 1;
		}
		else
		if(optionsArray.operator [](i) == "x3dTextureDirectory")
		{
			getTextureDir = optionsArray.operator [](++i);
			if(getTextureDir.operator ==(" ")) getTextureDir.set("");
		}
		else
		if(optionsArray.operator [](i) == "x3dNPV")
		{
			npvNonD = optionsArray.operator [](++i).asInt();
			if(npvNonD == 1) web3dem.setGlobalNPV(true);
			else web3dem.setGlobalNPV(false);
		}
		else
		if(optionsArray.operator [](i) == "x3dCreaseAngle")
		{
			caGlobalValue = optionsArray.operator [](++i).asFloat();
			web3dem.setGlobalCA(caGlobalValue);
		}
		else//999000
		if(optionsArray.operator [](i) == "x3dExportAudio")
		{
			if(optionsArray.operator [](++i) == "0") exAudio = false;
			else exAudio = true;
		}
		else//start of additional components
		if(optionsArray.operator [](i) == "x3dRigidBodyExport")
		{
			if(optionsArray.operator [](++i) == "0") exRigidBody = false;
			else exRigidBody = true;
		}
		else
		if(optionsArray.operator [](i) == "x3dHAnimExport")
		{
			if(optionsArray.operator [](++i) == "0") exHAnim = false;
			else exHAnim = true;
		}
		else//Binary Encoding issues
		if(optionsArray.operator [](i) == "x3dIODeviceExport")
		{
			if(optionsArray.operator [](++i) == "0") exIODevice = false;
			else exIODevice = true;
		}
		else if(optionsArray.operator [](i) == "x3dNSHAnim")
		{
			if(optionsArray.operator [](++i) == "0") nonStandardHAnim = false;
			else nonStandardHAnim = true;
		}
		else//Binary Encoding issues
		if(optionsArray.operator [](i) == "x3dBCFlag")
		{
			MString bcString;
			bcString.operator =(optionsArray.operator [](++i));
			if(bcString.operator ==("0")) exBCFlag = 0;
			else if(bcString.operator ==("2")) exBCFlag = 2;
			else exBCFlag = 1;
		}
		else//end of additional componenets
		if(optionsArray.operator [](i) == "x3dAudioDirectory")
		{
			getAudioDir = optionsArray.operator [](++i);
			if(getAudioDir.operator ==(" ")) getAudioDir.set("");
		}
		else
		if(optionsArray.operator [](i) == "x3dUseRelURL")
		{
			MString zero("0");
			if(optionsArray.operator [](++i) == zero)
			{
				useRelURL = false;
				web3dem.setUseRelURL(useRelURL);
			}
			else
			{
				useRelURL = true;
				web3dem.setUseRelURL(useRelURL);
			}
		}
		else
		if(optionsArray.operator [](i) == "x3dUseRelURLW")
		{
			MString zero("0");
			if(optionsArray.operator [](++i) == zero)
			{
				useRelURLW = false;
				web3dem.setUseRelURLW(useRelURLW);
			}
			else
			{
				useRelURLW = true;
				web3dem.setUseRelURLW(useRelURLW);
			}
		}
		else
		if(optionsArray.operator [](i) == "x3dInlineDirectory")
		{
			getInlineDir = optionsArray.operator [](++i);
			if(getInlineDir.operator ==(" ")) getInlineDir.set("");
		}
		else
		if(optionsArray.operator [](i) == "x3dBaseUrl")
		{
			exBaseURL = optionsArray.operator [](++i);
			if(exBaseURL.operator ==(" ")) exBaseURL.set("");
		}
		else
		if(optionsArray.operator [](i) == "x3dTextTempStore")
		{
			tempTexturePath = optionsArray.operator [](++i);
		}
		else if(optionsArray.operator [](i) == "updateMethod")
		{
			MString updateString = optionsArray.operator [](++i);
			if(updateString == "1") updateMethod = 1;
			else if(updateString == "2") updateMethod = 2;
			else updateMethod = 0;
		}

	}

	if(!isTreeBuilding)
	{
		MString imagePath(getTextureDir);
		if(getTextureDir.operator !=(""))
		{
			MStringArray ipArray;
			imagePath.split('/', ipArray);
			unsigned int ipl = ipArray.length();
			unsigned int l;
			MString newIP("");
			for(l=0;l<ipl;l++)
			{
				newIP.operator +=(ipArray.operator [](l));
				newIP.operator +=("/");
			}
			imagePath.operator ==(newIP);
			web3dem.setImageDir(imagePath);
		}

		MString audioPath(getAudioDir);
		if(getAudioDir.operator !=(""))
		{
			MStringArray apArray;
			audioPath.split('/', apArray);
			unsigned int apl = apArray.length();
			unsigned int l;
			MString newAP("");
			for(l=0;l<apl;l++)
			{
				newAP.operator +=(apArray.operator [](l));
				newAP.operator +=("/");
			}
			audioPath.operator ==(newAP);
			web3dem.setAudioDir(audioPath);
		}

		MString inlinePath(getInlineDir);
		if(getInlineDir.operator !=(""))
		{
			MStringArray inArray;
			inlinePath.split('/', inArray);
			unsigned int inl = inArray.length();
			unsigned int l;
			MString newIN("");
			for(l=0;l<inl;l++)
			{
				newIN.operator +=(inArray.operator [](l));
				newIN.operator +=("/");
			}
			inlinePath.operator ==(newIN);
			web3dem.setInlineDir(inlinePath);
		}

		MString basePath("");
		if(exBaseURL.operator !=(""))
		{
			basePath.operator =(exBaseURL);
			int urlend = basePath.rindex('/');
			if(urlend != basePath.length()-1 && basePath.length() > 0) basePath.operator +=("/");
			web3dem.setBaseUrl(basePath);
		}

		localImagePath = localPath;
		localImagePath.operator +=(imagePath);

		localAudioPath = localPath;
		localAudioPath.operator +=(audioPath);

		localInlinePath = localPath;
		localInlinePath.operator +=(inlinePath);
	}

	//
	//---------------------------------------------------------------------------
}
//****************************************************************
//****************************************************************

void x3dExportOrganizer::createResourceDir()
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
//-------------------------------------------------------------------------------
//Code for checking if the directory exits. Probably only works on windows. As 
//far as I can tell this is the only code used as of (7/20/04) that is OS 
//dependent.
//
//to get mkdir work I put included sys.stat.h, sys.types.h, and direct.h
//sys.stat.h is necessary for other code as well.
//
//There maybe some Maya API substitute for this, but I do not know what it is.
//-------------------------------------------------------------------------------
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////
{
	#ifdef _WIN32
	if(exTextures) mkdir(localImagePath.asChar());
	if(exAudio) mkdir(localAudioPath.asChar());
	if(exInline) mkdir(localInlinePath.asChar());
	#else
	if(exTextures) mkdir(localImagePath.asChar(),0777);
	if(exAudio) mkdir(localAudioPath.asChar(),0777);
	if(exInline) mkdir(localInlinePath.asChar(),0777);
	#endif
}

///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//This method evaluates the export texture options
//and calles the appropriate methods for processing
//the texture data.  We do not write any data to the 
//x3d file at this time. Instead, we resize, move, or 
//save in a new format the textures we wish to use.
//-----------------------------------------
void x3dExportOrganizer::textureSetup()
{
	//User feedback to the output window telling the 
	//content author that we are in the middle of the
	//texture setup process for external image and movie
	//files used as textures
	if(!isTreeBuilding)
	{
		sax3dw.msg.set("Evaluating External Media");		
		cout << sax3dw.msg.asChar() << endl;
		sax3dw.msg.set(" ");		
		cout << sax3dw.msg.asChar() << endl;
	}

	processFileTextures();
	if(conMedia)
	//------------------------------------------------------
	//Relocating movie files and unaltered texture files to images directory
	//------------------------------------------------------
	{
		//User feedback telling the content author that we
		//are cosolidating the movie files.
		if(!isTreeBuilding)
		{
			sax3dw.msg.set("Consolidating External Movie Textures");		
			cout << sax3dw.msg.asChar() << endl;
			sax3dw.msg.set(" ");		
			cout << sax3dw.msg.asChar() << endl;
			//Call the moveFiles method and pass it a Maya node type
			//and the 1 int value. A value of 1 tells the method to
			//consolidate only movie files
			moveFiles(0);
			moveFiles(1);
		}
	}
}

//*********************************************************
//*********************************************************


void x3dExportOrganizer::processFileTextures()
//---------------------------------------------
//
//---------------------------------------------
{
	//Providing user feedback that we are now actually
	//creating new image files
	if(!isTreeBuilding)
	{
		sax3dw.msg.set("Creating New External Textures");		
		cout << sax3dw.msg.asChar() << endl;
		sax3dw.msg.set(" ");		
		cout << sax3dw.msg.asChar() << endl;
	}
	//Use API to grab an interation list of all external image media
	//including both single image files and movies
	MItDependencyNodes ftIt(MFn::kFileTexture);
	while(!ftIt.isDone())
	{

		MObject obj = ftIt.item();
		MFnDependencyNode depNode(obj);
		if(depNode.typeName() == "file")
		//As kFileTexture refers to both Maya file nodes and 
		//movie nodes, we much check to make sure that we don't
		//process anything but a file node.
		{

			//This give us access to the Maya attribute in
			//the file node that tells use the entire path 
			//and file name for the image file we wish to change
			MString oldFile("fileTextureName");
			MPlug ftnPlug = depNode.findPlug(oldFile);

			//This actually retrieves the path/name data from
			//the file node's attribute
			MString imageFileLoc;
			ftnPlug.getValue(imageFileLoc);
			
			//The following code extracts the name of the file
			//from the path and then adds the appropriate 
			//file extension to the end of it.
			//
			//Once this is done, it builds a path to where the
			//new file will be place on the hard drive
			MStringArray pathCuts;
			MStringArray fileParts;
			char splitter1 = '/';
			char splitter2 = '.';

			imageFileLoc.split(splitter1, pathCuts);
			unsigned int pcLen = pathCuts.length();

			pathCuts.operator [](pcLen-1).split(splitter2, fileParts);

			int ltf = 0;
			bool cFormat = true;
			MPlug aPlug;
			aPlug = depNode.findPlug("fChoice");
			aPlug.getValue(ltf);
			
			switch(ltf)
			{
				case 0:
					cFormat = false;
					break;
				case 1:
					fileParts.operator [](1).set("gif");
					break;
				case 2:
					fileParts.operator [](1).set("jpg");
					break;
				case 3:
					fileParts.operator [](1).set("png"); 
					break;
				default:
					fileParts.operator [](1).set("gif");
					break;
			}

			bool adjSize;
			aPlug = depNode.findPlug("adjsize");
			aPlug.getValue(adjSize);

			if(cFormat == true || adjSize == true)
			{
				//This reads the image data from the file node
				//and stores it in an object with MImage functionality
				MImage fImage;
				fImage.readFromTextureNode(obj);

				//This next bit of code scales the image to the new dimensions
				//expressed in the export options panel.

				if(adjSize)
				{
					int width = 256;
					int height = 256;
					aPlug = depNode.findPlug("imgdimw");
					aPlug.getValue(width);
					aPlug = depNode.findPlug("imgdimh");
					aPlug.getValue(height);
					MStatus iStat = fImage.resize(width, height, false);
				}

				//Constructiong file output path
				MString writeOutPath(localImagePath);
				writeOutPath.operator +=(fileParts.operator [](0));
				writeOutPath.operator +=(".");
				writeOutPath.operator +=(fileParts.operator [](1));

				//Maya API method that write the file to disk. Should 
				//be valid for all operating systems that support Maya.
				if(conMedia) fImage.writeToFile(writeOutPath, fileParts.operator [](1));
			}
		}
		ftIt.next();//tells the iterator to procede to the next object
	}
}


void x3dExportOrganizer::moveFiles(int mediaType)//MStringArray moveFile, int mediaType)
{
	//This method should be pretty straight forward for most C++ programmers.
	//We are traversing through a Maya API dependency node iterator object. We
	//check to make sure we are transfering the correct nodes - and if so,
	//we open input and output streams to new files and transfer the data

	MItDependencyNodes depIt(MFn::kFileTexture);
	if(mediaType==2)
	{
		MItDependencyNodes audioDeps(MFn::kAudio);
		depIt = audioDeps;
	}

	while(!depIt.isDone())
	{

		bool processIt = false;
		MObject obj = depIt.item();
		MFnDependencyNode depNode(obj);
		MString oldFile("fileTextureName");

		MStringArray nodeNameParts;
		char splitter1 = '_';
		bool isExternal = true;
		MPlug aPlug;
		int ltf = 0;
		bool adjSize;

		switch(mediaType){
			case 0:
				depNode.name().split(splitter1, nodeNameParts);
				if(nodeNameParts.length() > 1)
				{
					if(nodeNameParts.operator [](nodeNameParts.length()-2) == "rawkee" && nodeNameParts.operator [](nodeNameParts.length()-1) == "export")
					{
						isExternal = false;
					}
				}

				aPlug = depNode.findPlug("fChoice");
				aPlug.getValue(ltf);
				
				aPlug = depNode.findPlug("adjsize");
				aPlug.getValue(adjSize);

				if(depNode.typeName() == "file" && ((isExternal == true && fileOverwrite == true && adjSize == false && ltf == 0) || isExternal == false)) processIt = true;
				break;
			case 1:
				if(depNode.typeName() == "movie" && fileOverwrite == true) processIt = true;
				break;
			case 2:
				oldFile.set("filename");
				if(depNode.typeName() == "audio" && fileOverwrite == true) processIt = true;
				break;
			default:
				break;
		}
		if(processIt)
		{
			ifstream fin;
			ofstream fout;
			MPlug ftnPlug = depNode.findPlug(oldFile);
			MString fileLoc;
			ftnPlug.getValue(fileLoc);

			MStringArray pathCuts;
			char splitter = '/';

			fileLoc.split(splitter, pathCuts);
			unsigned int pcLen = pathCuts.length();

			fin.open(fileLoc.asChar(), ios::in | ios::binary);
				if (fin.bad()) {
					sax3dw.msg.set("Cannot input open file -- error error -- sorry no further info.");
					cerr << sax3dw.msg.asChar() << endl;
				}

			MString relocate("");
			if(mediaType < 2) relocate.operator +=(localImagePath);
			else relocate.operator +=(localAudioPath);
			relocate.operator +=(pathCuts.operator [](pcLen-1));


			fout.open(relocate.asChar(), ios::out | ios::binary);
			if (fout.bad()) {
				sax3dw.msg.set("Cannot open output file -- error error -- sorry no further info.");
				cerr << sax3dw.msg.asChar() << endl;
			}

			if(!fout.bad() && !fin.bad())
			{

				unsigned long length;
				unsigned long value = 0;
				double perc = 0;
				int rPerc = 0;
				int addDot = 10;

				if(!isTreeBuilding)
				{
					sax3dw.msg.set("Moving file: ");
					sax3dw.msg.operator +=(pathCuts.operator [](pcLen-1));
					cout << sax3dw.msg.asChar() << endl;
				}

				fin.seekg (0, ios::end);
				length = fin.tellg();
				fin.seekg (0, ios::beg);

				fin.seekg(0);
				fout.seekp(0);
		
				char buffer[100];

				while(!(!fin))
				{
					fin.read(buffer, 100);
					if(!(!fin)){
						fout.write(buffer, 100);
						value = value + 100;
						perc = (double)value/(double)length;
						perc = perc * 100;
						rPerc = (int)perc;
						if(rPerc >= addDot){
							if(!isTreeBuilding)
							{
								sax3dw.msg.set("Precentage Complete: ");
								sax3dw.msg.operator +=(addDot);
								sax3dw.msg.operator +=("%");
								cout << sax3dw.msg.asChar() << endl;
							}
							addDot = addDot + 10;
						}
					}
				}

				unsigned long cBuf = fin.gcount();
				if(cBuf > 0) fout.write(buffer, cBuf);
					
				if(!isTreeBuilding)
				{
					sax3dw.msg.set("File Move Complete");
					cout << sax3dw.msg.asChar() << endl;
				}
				fin.close();

				fout.flush();
				fout.close();
			}
		}

		depIt.next();
	}
}

void x3dExportOrganizer::inlineSetup()
{
//	MStringArray inlineNames;
//	MGlobal::executeCommand("ls -type x3dInline", inlineNames);
//	unsigned int inLen = inlineNames.length();
//	unsigned int i;
//	for(i=0;i<inLen;i++){
//		MFnDependencyNode inNode = web3dem.getMyDepNode(inlineNames.operator [](i));
//		MString refFile = inNode.findPlug("url");
//		
//	}	
}

void x3dExportOrganizer::soundSetup()
{
	//Currently, this really only transfers external audio files
	//used by Maya audio nodes. It does this by calling the 
	//moveFiles method and passing it a kAudio node type and a 2 int.
	//Works if you have a Maya audio file actually in your Maya file 
	//at the time of export. However, no other audio support is 
	//currently implemented in RawKee. So all you'll be doing is 
	//transfering an audio file for no reason.
	if(conMedia)
	{
		if(!isTreeBuilding)
		{
			sax3dw.msg.set("Relocating Audio Files");
			cout << sax3dw.msg.asChar() << endl;
			moveFiles(2);
			sax3dw.msg.set("Finished Audio Files");
			cout << sax3dw.msg.asChar() << endl;
		}
	}
}

///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//This method evaluates the RawKee underworld nodes (such
//as x3dIndexedFaceSet, x3dColor and x3dNormal) by calling
//a MEL procedure from the x3d_exporter_procedures.mel
//script in order to prepare the RawKee underworld nodes for 
//export. This includes any required data collection.
//
//As this can be quite a bit of data, this should really be
//done completely in C++ code because the MEL implementation
//is so slow.
//-----------------------------------------
void x3dExportOrganizer::prepareUnderworldNodes()
{
//	int slowIt;
//	MGlobal::executeCommand(MString("makeUNodesExportReady"), slowIt);
}
//********************************************************
//********************************************************


///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//This method evalutes the RawKee interpolator nodes (such as 
//x3dPositionInterpolator and x3dOrientationInterpolator nodes)
//by calling a MEL procedure found in the x3d_exporter_procedures.mel
//file, in order to prepare them for export. This includes any 
//required data collection.
//
//As this can be quite a bit of data, this should really be
//done completely in C++ code because the MEL implementation
//is so slow.
//-----------------------------------------
void x3dExportOrganizer::prepareInterpolatorNodes()
{
	posInterCollect();
	oriInterCollect();
	coordInterCollect();
	normalInterCollect();
	colorInterCollect();
	scalarInterCollect();
	boolSeqCollect();
	intSeqCollect();

	MAnimControl aControl;
	MTime nTime = aControl.currentTime();
	nTime.setValue(0);
	nTime.setUIUnit(MTime::uiUnit());
	aControl.setCurrentTime(nTime);
}
//******************************************************************
//******************************************************************
MSelectionList x3dExportOrganizer::getNodeList(MString cString)
{
	MSelectionList tempList;
	tempList.clear();
	MItDependencyNodes interpIt(MFn::kInvalid);
	while(!interpIt.isDone())
	{
		MObject obj = interpIt.item();
		MFnDependencyNode depNode(obj);
		if(depNode.typeName() == cString) tempList.add(depNode.name());
		interpIt.next();//tells the iterator to procede to the next object
	}

	return tempList;
}

//void x3dExportOrganizer::gatherKey(MFnDependencyNode depNode)
void x3dExportOrganizer::gatherKey(MObject mObj)
{
	MFnDependencyNode depNode(mObj);
	MPlug theKey = depNode.findPlug("key");
	MPlug startFrame = depNode.findPlug("startFrame");
	MPlug stopFrame = depNode.findPlug("stopFrame");
	MPlug everyFrame = depNode.findPlug("keso");

	double eFrame = 0;
	double startFloat = 0;
	double stopFloat = 0;
	startFrame.getValue(startFloat);
	stopFrame.getValue(stopFloat);
	everyFrame.getValue(eFrame);
	double denom = stopFloat - startFloat;

	double dKeyLen = denom/eFrame;

	double keyPer = eFrame/denom;
	if(keyPer < 0) keyPer = keyPer * -1;

	if(dKeyLen<0) dKeyLen = dKeyLen * -1;
	unsigned int keyLen = static_cast<int>(dKeyLen);

	if(keyLen == 0) keyLen = 1;

	unsigned int i;
	for(i=0;i<=keyLen;i++)
	{
//		MPlug bPlug = theKey.elementByPhysicalIndex(i);
		MPlug bPlug = theKey.elementByLogicalIndex(i);
		double cKey = i * keyPer;
		if(i == 0) bPlug.setValue(0);
		else if(i==keyLen) bPlug.setValue(1);
		else bPlug.setValue(cKey);
	}
}

void x3dExportOrganizer::posInterCollect()
{
	MSelectionList sList = getNodeList(X3D_POSINTER);

	unsigned int ss = sList.length();
    unsigned int i;
	for(i=0;i<ss;i++)
	{
		MObject obj;
		sList.getDependNode(i, obj);
		MFnDependencyNode depFn(obj);
		MPlug startp = depFn.findPlug("startFrame");
		MPlug stopp = depFn.findPlug("stopFrame");

		double sf = 0;
		double stf = 0;

		double sminuss = 0;
		double skip = 0;

		startp.getValue(sf);
		stopp.getValue(stf);

		sminuss = stf-sf;

		int keyLenInt = 0;
		unsigned int keyLen = 0;
		MPlug keyPlug = depFn.findPlug("key_cc");
		keyPlug.getValue(keyLenInt);
		keyLen = keyLenInt;

		skip = sminuss/keyLen;

		if(keyLen == 0)
		{
			keyLen = 1;
		}
		MAnimControl aControl;
		MTime nTime = aControl.currentTime();
		nTime.setValue(sf);
		aControl.setCurrentTime(nTime);

		MPlug kvPlug = depFn.findPlug("keyValue");

		unsigned int j;
		for(j=0;j<=keyLen;j++)
		{
			double offset = sf + (skip*j);
			nTime.setValue(offset);
			aControl.setCurrentTime(nTime);

			MPlug posPlug = depFn.findPlug("position");
			MPlug xPlug = posPlug.child(0);
			MPlug yPlug = posPlug.child(1);
			MPlug zPlug = posPlug.child(2);
			float pFloat[3];
			xPlug.getValue(pFloat[0]);
			yPlug.getValue(pFloat[1]);
			zPlug.getValue(pFloat[2]);

			MPlug tPlug = kvPlug.elementByLogicalIndex(j);
			MPlug xtPlug = tPlug.child(0);
			MPlug ytPlug = tPlug.child(1);
			MPlug ztPlug = tPlug.child(2);

			xtPlug.setValue(1);
			ytPlug.setValue(1);
			ztPlug.setValue(1);

			tPlug = kvPlug.elementByPhysicalIndex(j);
			xtPlug = tPlug.child(0);
			ytPlug = tPlug.child(1);
			ztPlug = tPlug.child(2);

			xtPlug.setValue(pFloat[0]);
			ytPlug.setValue(pFloat[1]);
			ztPlug.setValue(pFloat[2]);

		}
		gatherKey(depFn.object());
	}
}

void x3dExportOrganizer::oriInterCollect()
{
	MSelectionList sList = getNodeList(X3D_ORIINTER);

	unsigned int ss = sList.length();
    unsigned int i;
	for(i=0;i<ss;i++)
	{
		MObject obj;
		sList.getDependNode(i, obj);
		MFnDependencyNode depFn(obj);
		MPlug startp = depFn.findPlug("startFrame");
		MPlug stopp = depFn.findPlug("stopFrame");

		double sf = 0;
		double stf = 0;

		double sminuss = 0;
		double skip = 0;

		startp.getValue(sf);
		stopp.getValue(stf);

		sminuss = stf-sf;

		int keyLenInt = 0;
		unsigned int keyLen = 0;
		MPlug keyPlug = depFn.findPlug("key_cc");
		keyPlug.getValue(keyLenInt);
		keyLen = keyLenInt;

		skip = sminuss/keyLen;

		if(keyLen == 0)
		{
			keyLen = 1;
		}
		MAnimControl aControl;
		MTime nTime = aControl.currentTime();
		nTime.setValue(sf);
		aControl.setCurrentTime(nTime);

		MPlug kvPlug = depFn.findPlug("keyValue");

		unsigned int j;
		for(j=0;j<=keyLen;j++)
		{
			double offset = sf + (skip*j);
			nTime.setValue(offset);
			aControl.setCurrentTime(nTime);

			MPlug posPlug = depFn.findPlug("orientation");
			MPlug xPlug = posPlug.child(0);
			MPlug yPlug = posPlug.child(1);
			MPlug zPlug = posPlug.child(2);
			float pFloat[3];
			xPlug.getValue(pFloat[0]);
			yPlug.getValue(pFloat[1]);
			zPlug.getValue(pFloat[2]);

			MEulerRotation aRot(pFloat[0], pFloat[1], pFloat[2], MEulerRotation::kXYZ);
			MMatrix mmatrix;
			aRot.decompose(mmatrix, MEulerRotation::kXYZ);
			pFloat[0] = aRot.x;
			pFloat[1] = aRot.y;
			pFloat[2] = aRot.z;

			MPlug tPlug = kvPlug.elementByLogicalIndex(j);
			MPlug xtPlug = tPlug.child(0);
			MPlug ytPlug = tPlug.child(1);
			MPlug ztPlug = tPlug.child(2);

			xtPlug.setValue(1);
			ytPlug.setValue(1);
			ztPlug.setValue(1);

			tPlug = kvPlug.elementByPhysicalIndex(j);
			xtPlug = tPlug.child(0);
			ytPlug = tPlug.child(1);
			ztPlug = tPlug.child(2);

			xtPlug.setValue(pFloat[0]);
			ytPlug.setValue(pFloat[1]);
			ztPlug.setValue(pFloat[2]);

		}
		
		gatherKey(depFn.object());
	}
}

void x3dExportOrganizer::colorInterCollect()
{
	MSelectionList sList = getNodeList(X3D_COLORINTER);

	unsigned int ss = sList.length();
    unsigned int i;
	for(i=0;i<ss;i++)
	{
		MObject obj;
		sList.getDependNode(i, obj);
		MFnDependencyNode depFn(obj);
		MPlug startp = depFn.findPlug("startFrame");
		MPlug stopp = depFn.findPlug("stopFrame");

		double sf = 0;
		double stf = 0;

		double sminuss = 0;
		double skip = 0;

		startp.getValue(sf);
		stopp.getValue(stf);

		sminuss = stf-sf;

		int keyLenInt = 0;
		unsigned int keyLen = 0;
		MPlug keyPlug = depFn.findPlug("key_cc");
		keyPlug.getValue(keyLenInt);
		keyLen = keyLenInt;

		skip = sminuss/keyLen;

		if(keyLen == 0)
		{
			keyLen = 1;
		}
		MAnimControl aControl;
		MTime nTime = aControl.currentTime();
		nTime.setValue(sf);
		aControl.setCurrentTime(nTime);

		MPlug kvPlug = depFn.findPlug("keyValue");

		MPlug temp = depFn.findPlug("color");
		MItDependencyGraph depIt(temp, MFn::kInvalid, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kPlugLevel);

		bool searching = true;

		MFnDependencyNode depNode;
		while(!depIt.isDone() && searching == true)
		{
			MObject tObj = depIt.thisNode();
			depNode.setObject(tObj);
			if(depNode.name() != depFn.name())
			{
				searching = false;
			}
			depIt.next();
		}

		unsigned int j;
		for(j=0;j<=keyLen;j++)
		{
			double offset = sf + (skip*j);
			nTime.setValue(offset);
			aControl.setCurrentTime(nTime);

			MPlug colorPlug;
			if(searching) colorPlug = depFn.findPlug("color");
			else colorPlug = depNode.findPlug("color");
			MPlug rPlug = colorPlug.child(0);
			MPlug gPlug = colorPlug.child(1);
			MPlug bPlug = colorPlug.child(2);

			float pFloat[3];

			rPlug.getValue(pFloat[0]);
			gPlug.getValue(pFloat[1]);
			bPlug.getValue(pFloat[2]);

			if(pFloat[0] < 0) pFloat[0] = 0;
			if(pFloat[0] > 1) pFloat[0] = 1;
			if(pFloat[1] < 0) pFloat[1] = 0;
			if(pFloat[1] > 1) pFloat[1] = 1;
			if(pFloat[2] < 0) pFloat[2] = 0;
			if(pFloat[2] > 1) pFloat[2] = 1;

			MPlug tPlug = kvPlug.elementByLogicalIndex(j);
			MPlug rtPlug = tPlug.child(0);
			MPlug gtPlug = tPlug.child(1);
			MPlug btPlug = tPlug.child(2);

			rtPlug.setValue(1);
			gtPlug.setValue(1);
			btPlug.setValue(1);

			tPlug = kvPlug.elementByPhysicalIndex(j);
			rtPlug = tPlug.child(0);
			gtPlug = tPlug.child(1);
			btPlug = tPlug.child(2);

			rtPlug.setValue(pFloat[0]);
			gtPlug.setValue(pFloat[1]);
			btPlug.setValue(pFloat[2]);

		}
		
		gatherKey(depFn.object());
	}
}

void x3dExportOrganizer::coordInterCollect()
{
	MSelectionList sList = getNodeList(X3D_COORDINTER);

	unsigned int ss = sList.length();
    unsigned int i;
	for(i=0;i<ss;i++)
	{
		MObject obj;
		sList.getDependNode(i, obj);
		MFnDependencyNode depFn(obj);
		MPlug startp = depFn.findPlug("startFrame");
		MPlug stopp = depFn.findPlug("stopFrame");

		double sf = 0;
		double stf = 0;

		double sminuss = 0;
		double skip = 0;

		startp.getValue(sf);
		stopp.getValue(stf);

		sminuss = stf-sf;

		int keyLenInt = 0;
		unsigned int keyLen = 0;
		MPlug keyPlug = depFn.findPlug("key_cc");
		keyPlug.getValue(keyLenInt);
		keyLen = keyLenInt;

		skip = sminuss/keyLen;

		if(keyLen == 0)
		{
			keyLen = 1;
		}
		MAnimControl aControl;
		MTime nTime = aControl.currentTime();
		nTime.setValue(sf);
		aControl.setCurrentTime(nTime);

		MPlug kvPlug = depFn.findPlug("keyValue");

		MPlug temp = depFn.findPlug("x3dCoordsIn");
		MItDependencyGraph depIt(temp, MFn::kInvalid, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kPlugLevel);

		bool searching = true;
		MDagPath dagPath;
		MPlug conPlug;
		while(!depIt.isDone() && searching == true)
		{
			conPlug = depIt.thisPlug();
			MObject tObj = depIt.thisNode();
			MFnDagNode dagNode(tObj);
			if(dagNode.typeName() == X3D_MESH)
			{
				MString matchName = dagNode.name();
				MItDag itDag(MItDag::kDepthFirst, MFn::kInvalid);

				bool subSearch = true;
				while(!itDag.isDone() && subSearch == true)
				{
					MObject tItem = itDag.item();
					MFnDependencyNode nNode(tItem);
					if(nNode.name() == matchName)
					{
						itDag.getPath(dagPath);
						subSearch = false;
					}
					itDag.next();
				}
				searching = subSearch;
			}
			depIt.next();
		}

		int ccs = 0;
		if(!searching)
		{
			unsigned int l=0;
			MFnMesh mesh(dagPath);
			if(conPlug.partialName(false, false, false, false, false, true) == "x3dCoordsOut")
			{
				cout << depFn.name().asChar() << " - Extracting Coordinate Data from " << mesh.name().asChar() << endl;
				unsigned int j;
				for(j=0;j<=keyLen;j++)
				{
					double offset = sf + (skip*j);
					nTime.setValue(offset);
					aControl.setCurrentTime(nTime);

					MFloatPointArray coordValues;
					mesh.getPoints(coordValues, MSpace::kObject);

					unsigned int pl = coordValues.length();
					ccs = pl;
					unsigned int k;
					for(k=0;k<pl;k++)
					{
						MFloatPoint tPoint = coordValues.operator [](k);

						unsigned int arrVal = (pl*j)+k;
						MPlug tPlug = kvPlug.elementByLogicalIndex(arrVal);
						MPlug xPlug = tPlug.child(0);
						MPlug yPlug = tPlug.child(1);
						MPlug zPlug = tPlug.child(2);

						xPlug.setValue(1);
						yPlug.setValue(1);
						zPlug.setValue(1);

						tPlug = kvPlug.elementByPhysicalIndex(arrVal);
						xPlug = tPlug.child(0);
						yPlug = tPlug.child(1);
						zPlug = tPlug.child(2);

						xPlug.setValue(tPoint.x);
						yPlug.setValue(tPoint.y);
						zPlug.setValue(tPoint.z);
					}
				}
			}
			else if(conPlug.partialName(false, false, false, false, false, true) == "x3dCPVOut")
			{
				cout << depFn.name().asChar() << " - Extracting ColorPerVertex Data from " << mesh.name().asChar() << endl;

				unsigned int j;
				for(j=0;j<=keyLen;j++)
				{
					double offset = sf + (skip*j);
					nTime.setValue(offset);
					aControl.setCurrentTime(nTime);

					MColorArray colorValues;
					mesh.getVertexColors(colorValues);

					unsigned int pl = colorValues.length();
					ccs = pl;
					unsigned int k;
					for(k=0;k<pl;k++)
					{
						MColor tColor = colorValues.operator [](k);
						if(tColor.r < 0) tColor.r = 0;
						if(tColor.g < 0) tColor.g = 0;
						if(tColor.b < 0) tColor.b = 0;

						if(tColor.r > 0) tColor.r = 1;
						if(tColor.g > 0) tColor.g = 1;
						if(tColor.b > 0) tColor.b = 1;

						unsigned int arrVal = (pl*j)+k;
						MPlug tPlug = kvPlug.elementByLogicalIndex(arrVal);
						MPlug xPlug = tPlug.child(0);
						MPlug yPlug = tPlug.child(1);
						MPlug zPlug = tPlug.child(2);

						xPlug.setValue(1);
						yPlug.setValue(1);
						zPlug.setValue(1);

						tPlug = kvPlug.elementByPhysicalIndex(arrVal);
						xPlug = tPlug.child(0);
						yPlug = tPlug.child(1);
						zPlug = tPlug.child(2);

						xPlug.setValue(tColor.r);
						yPlug.setValue(tColor.g);
						zPlug.setValue(tColor.b);
					}
				}
			}
			else if(conPlug.partialName(false, false, false, false, false, true) == "x3dTexCoordsOut")
			{
				cout << depFn.name().asChar() << " - Extracting TexCoordinate Data from " << mesh.name().asChar() << endl;
				unsigned int j;
				for(j=0;j<=keyLen;j++)
				{
					double offset = sf + (skip*j);
					nTime.setValue(offset);
					aControl.setCurrentTime(nTime);

					MFloatArray tv1;
					MFloatArray tv2;
					mesh.getUVs(tv1, tv2);

					MPlug luv = mesh.findPlug("lostUV");
					MPlug luv1 = luv.child(0);
					MPlug luv2 = luv.child(1);
					float fluv[2] = { 0, 0};
					luv1.getValue(fluv[0]);
					luv2.getValue(fluv[1]);

					unsigned int pl = tv1.length();
					ccs = pl+1;

					MPlug tPlug = kvPlug.elementByLogicalIndex(pl*j);
					MPlug xPlug = tPlug.child(0);
					MPlug yPlug = tPlug.child(1);
					MPlug zPlug = tPlug.child(2);

					xPlug.setValue(1);
					yPlug.setValue(1);
					zPlug.setValue(1);

					tPlug = kvPlug.elementByPhysicalIndex(pl*j);
					xPlug = tPlug.child(0);
					yPlug = tPlug.child(1);
					zPlug = tPlug.child(2);

					xPlug.setValue(fluv[0]);
					yPlug.setValue(fluv[1]);
					zPlug.setValue(0);

					unsigned int k;
					for(k=1;k<=pl;k++)
					{
						unsigned int arrVal = (pl*j)+k;
						MPlug tPlug = kvPlug.elementByLogicalIndex(arrVal);
						MPlug xPlug = tPlug.child(0);
						MPlug yPlug = tPlug.child(1);
						MPlug zPlug = tPlug.child(2);

						xPlug.setValue(1);
						yPlug.setValue(1);
						zPlug.setValue(0);

						tPlug = kvPlug.elementByPhysicalIndex(arrVal);
						xPlug = tPlug.child(0);
						yPlug = tPlug.child(1);
						zPlug = tPlug.child(1);

						xPlug.setValue(tv1.operator [](k));
						yPlug.setValue(tv2.operator [](k));
						zPlug.setValue(0);
					}
				}
			}
		}
		MPlug ccsPlug = depFn.findPlug("keyValue_cc_s");
		ccs = (ccs * keyLen) + ccs;
		ccsPlug.setValue(ccs);
		gatherKey(depFn.object());
	}
}

void x3dExportOrganizer::normalInterCollect()
{
	MSelectionList sList = getNodeList(X3D_NORMINTER);

	unsigned int ss = sList.length();
    unsigned int i;
	for(i=0;i<ss;i++)
	{
		MObject obj;
		sList.getDependNode(i, obj);
		MFnDependencyNode depFn(obj);
		MPlug startp = depFn.findPlug("startFrame");
		MPlug stopp = depFn.findPlug("stopFrame");

		double sf = 0;
		double stf = 0;

		double sminuss = 0;
		double skip = 0;

		startp.getValue(sf);
		stopp.getValue(stf);

		sminuss = stf-sf;

		int keyLenInt = 0;
		unsigned int keyLen = 0;
		MPlug keyPlug = depFn.findPlug("key_cc");
		keyPlug.getValue(keyLenInt);
		keyLen = keyLenInt;

		skip = sminuss/keyLen;

		if(keyLen == 0)
		{
			keyLen = 1;
		}
		MAnimControl aControl;
		MTime nTime = aControl.currentTime();
		nTime.setValue(sf);
		aControl.setCurrentTime(nTime);

		MPlug kvPlug = depFn.findPlug("keyValue");

		MPlug temp = depFn.findPlug("x3dNormalsIn");
		MItDependencyGraph depIt(temp, MFn::kInvalid, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kPlugLevel);

		bool searching = true;
		MDagPath dagPath;
		MPlug conPlug;
		while(!depIt.isDone() && searching == true)
		{
			conPlug = depIt.thisPlug();
			MObject tObj = depIt.thisNode();
			MFnDagNode dagNode(tObj);
			if(dagNode.typeName() == X3D_MESH)
			{
				MString matchName = dagNode.name();
				MItDag itDag(MItDag::kDepthFirst, MFn::kInvalid);

				bool subSearch = true;
				while(!itDag.isDone() && subSearch == true)
				{
					MObject tItem = itDag.item();
					MFnDependencyNode nNode(tItem);
					if(nNode.name() == matchName)
					{
						itDag.getPath(dagPath);
						subSearch = false;
					}
					itDag.next();
				}
				searching = subSearch;
			}
			depIt.next();
		}

		int ccs = 0;
		if(!searching)
		{
			MFnMesh mesh(dagPath);
			if(conPlug.partialName(false, false, false, false, false, true) == "x3dNormalsOut")
			{
				cout << depFn.name().asChar() << " - Extracting Normal Data from " << mesh.name().asChar() << endl;
				unsigned int j;
				for(j=0;j<=keyLen;j++)
				{
					double offset = sf + (skip*j);
					nTime.setValue(offset);
					aControl.setCurrentTime(nTime);

					MFloatVectorArray normalValues;
					mesh.getNormals(normalValues, MSpace::kObject);//9990009991
					MFloatVectorArray compareValues = web3dem.getComparedFloatVectorArray(normalValues);

					unsigned int pl = compareValues.length();
					ccs = pl;
					unsigned int k;
					for(k=0;k<pl;k++)
					{
						MFloatVector tVector = compareValues.operator [](k);

						unsigned int arrVal = (pl*j)+k;
						MPlug tPlug = kvPlug.elementByLogicalIndex(arrVal);
						MPlug xPlug = tPlug.child(0);
						MPlug yPlug = tPlug.child(1);
						MPlug zPlug = tPlug.child(2);

						xPlug.setValue(1);
						yPlug.setValue(1);
						zPlug.setValue(1);

						tPlug = kvPlug.elementByPhysicalIndex(arrVal);
						xPlug = tPlug.child(0);
						yPlug = tPlug.child(1);
						zPlug = tPlug.child(2);

						xPlug.setValue(tVector.x);
						yPlug.setValue(tVector.y);
						zPlug.setValue(tVector.z);
					}
				}
			}
		}
		MPlug ccsPlug = depFn.findPlug("keyValue_cc_s");
		ccs = (ccs * keyLen) + ccs;
		ccsPlug.setValue(ccs);
		gatherKey(depFn.object());
	}
}

void x3dExportOrganizer::scalarInterCollect()
{
	MSelectionList sList = getNodeList(X3D_SCALINTER);

	unsigned int ss = sList.length();
    unsigned int i;
	for(i=0;i<ss;i++)
	{
		MObject obj;
		sList.getDependNode(i, obj);
		MFnDependencyNode depFn(obj);
		MPlug startp = depFn.findPlug("startFrame");
		MPlug stopp = depFn.findPlug("stopFrame");

		double sf = 0;
		double stf = 0;

		double sminuss = 0;
		double skip = 0;

		startp.getValue(sf);
		stopp.getValue(stf);

		sminuss = stf-sf;

		int keyLenInt = 0;
		unsigned int keyLen = 0;
		MPlug keyPlug = depFn.findPlug("key_cc");
		keyPlug.getValue(keyLenInt);
		keyLen = keyLenInt;

		skip = sminuss/keyLen;

		if(keyLen == 0)
		{
			keyLen = 1;
		}
		MAnimControl aControl;
		MTime nTime = aControl.currentTime();
		nTime.setValue(sf);
		aControl.setCurrentTime(nTime);

		MPlug kvPlug = depFn.findPlug("keyValue");

		unsigned int j;
		for(j=0;j<=keyLen;j++)
		{
			double offset = sf + (skip*j);
			nTime.setValue(offset);
			aControl.setCurrentTime(nTime);

			MPlug scalPlug = depFn.findPlug("scalar");
			float sFloat;
			scalPlug.getValue(sFloat);

			MPlug tPlug = kvPlug.elementByLogicalIndex(j);
			tPlug.setValue(1);

			tPlug = kvPlug.elementByPhysicalIndex(j);
			tPlug.setValue(sFloat);
		}
		gatherKey(depFn.object());
	}
}

void x3dExportOrganizer::boolSeqCollect()
{
	MSelectionList sList = getNodeList(X3D_BOOLSEQ);

	unsigned int ss = sList.length();
    unsigned int i;
	for(i=0;i<ss;i++)
	{
		MObject obj;
		sList.getDependNode(i, obj);
		MFnDependencyNode depFn(obj);
		MPlug startp = depFn.findPlug("startFrame");
		MPlug stopp = depFn.findPlug("stopFrame");

		double sf = 0;
		double stf = 0;

		double sminuss = 0;
		double skip = 0;

		startp.getValue(sf);
		stopp.getValue(stf);

		sminuss = stf-sf;

		int keyLenInt = 0;
		unsigned int keyLen = 0;
		MPlug keyPlug = depFn.findPlug("key_cc");
		keyPlug.getValue(keyLenInt);
		keyLen = keyLenInt;

		skip = sminuss/keyLen;

		if(keyLen == 0)
		{
			keyLen = 1;
		}
		MAnimControl aControl;
		MTime nTime = aControl.currentTime();
		nTime.setValue(sf);
		aControl.setCurrentTime(nTime);

		MPlug kvPlug = depFn.findPlug("keyValue");

		unsigned int j;
		for(j=0;j<=keyLen;j++)
		{
			double offset = sf + (skip*j);
			nTime.setValue(offset);
			aControl.setCurrentTime(nTime);

			MPlug bPlug = depFn.findPlug("boolean");
			bool bVal;
			bPlug.getValue(bVal);

			MPlug tPlug = kvPlug.elementByLogicalIndex(j);
			tPlug.setValue(bVal);

			tPlug = kvPlug.elementByPhysicalIndex(j);
			tPlug.setValue(bVal);
		}
		
		gatherKey(depFn.object());
	}
}

void x3dExportOrganizer::intSeqCollect()
{
	MSelectionList sList = getNodeList(X3D_INTSEQ);

	unsigned int ss = sList.length();
    unsigned int i;
	for(i=0;i<ss;i++)
	{
		MObject obj;
		sList.getDependNode(i, obj);
		MFnDependencyNode depFn(obj);
		MPlug startp = depFn.findPlug("startFrame");
		MPlug stopp = depFn.findPlug("stopFrame");

		double sf = 0;
		double stf = 0;

		double sminuss = 0;
		double skip = 0;

		startp.getValue(sf);
		stopp.getValue(stf);

		sminuss = stf-sf;

		int keyLenInt = 0;
		unsigned int keyLen = 0;
		MPlug keyPlug = depFn.findPlug("key_cc");
		keyPlug.getValue(keyLenInt);
		keyLen = keyLenInt;

		skip = sminuss/keyLen;

		if(keyLen == 0)
		{
			keyLen = 1;
		}
		MAnimControl aControl;
		MTime nTime = aControl.currentTime();
		nTime.setValue(sf);
		aControl.setCurrentTime(nTime);

		MPlug kvPlug = depFn.findPlug("keyValue");

		unsigned int j;
		for(j=0;j<=keyLen;j++)
		{
			double offset = sf + (skip*j);
			nTime.setValue(offset);
			aControl.setCurrentTime(nTime);

			MPlug iPlug = depFn.findPlug("integer");
			int iVal;
			iPlug.getValue(iVal);

			MPlug tPlug = kvPlug.elementByLogicalIndex(j);
			tPlug.setValue(iVal);

			tPlug = kvPlug.elementByPhysicalIndex(j);
			tPlug.setValue(iVal);
		}
		
		gatherKey(depFn.object());
	}
}


//methods that interact directly with the maya///
void x3dExportOrganizer::writeRoutes()
//This method is used to write X3D Routes to a file. It writes all the
//route nodes stored in your Maya file at export. It uses the sax3dw.startNode()
//method to do so.
{
	MStringArray routeList;
	MGlobal::executeCommand("ls -type x3dRoute", routeList);

	unsigned int rlLength = routeList.length();
	unsigned int i;

	for(i=0;i<rlLength;i++)
	{
//		bool isRef = isReferenceNode(routeList.operator [](i));
//		if(!isRef)
//		{
//			MFnDependencyNode depNode = web3dem.getMyDepNode(routeList.operator [](i));
			MFnDependencyNode depNode(web3dem.getMyDepNodeObj(routeList.operator [](i)));

			MPlug fnPlug = depNode.findPlug("fromNode");
			MString tString;
			fnPlug.getValue(tString);

			MPlug tnPlug = depNode.findPlug("toNode");
			MString tString2;
			tnPlug.getValue(tString2);

			if(sax3dw.checkIfHasBeen(tString) && sax3dw.checkIfHasBeen(tString2))
			{
				MPlug fvPlug = depNode.findPlug("fromValue");
				MString tString1;
				fvPlug.getValue(tString1);

				MPlug tvPlug = depNode.findPlug("toValue");
				MString tString3;
				tvPlug.getValue(tString3);

				sax3dw.writeRoute(tString, tString1, tString2, tString3);
			}

			//A node written this way will look like the following:
			//<ROUTE fromNode='proximitySensor1' fromField='position_changed' toNode='pSphere1' toField='set_translation'/>
			//or
			//ROUTE proximitySensor1.position_changed TO pSphere1.set_translation
			//--------------------------------------------------------------------
//		}
	}
}

void x3dExportOrganizer::setUpMetadataNodes()
{
	//Provide user feedback telling the content author
	//that all metadata nodes are being added
	//to the hidden switch node
	if(!isTreeBuilding)
	{
		sax3dw.msg.set("Exporting Metadata Nodes - Hidden Under \"HiddenNodeContainer\" Switch Node");
		cout << sax3dw.msg.asChar() << endl;
		sax3dw.msg.set(" ");
		cout << sax3dw.msg.asChar() << endl;
	}

	//Using several "for" loops, we will now write all metadata nodes
	unsigned int i;

	//MetadataDouble Nodes
	unsigned int metaInt = X3DMETAD;
	MStringArray mDoubles = x3dMetadataNames( metaInt );
	unsigned int cycleDoubles = mDoubles.length();

	for(i=0;i<cycleDoubles;i++)
	{	
		sax3dw.setHasMultiple(true);
		writeMetadataNode(mDoubles.operator [](i), msMetaD, "metadataStorage");
	}

	//MetadataFloat nodes
	metaInt = X3DMETAF;
	MStringArray mFloats = x3dMetadataNames(metaInt);
	unsigned int cycleFloats = mFloats.length();

	for(i=0;i<cycleFloats;i++)
	{
		sax3dw.setHasMultiple(true);
		writeMetadataNode(mFloats.operator [](i), msMetaF, "metadataStorage");
	}

	//MetadataInteger Nodes
	metaInt = X3DMETAI;
	MStringArray mIntegers = x3dMetadataNames(metaInt);
	unsigned int cycleIntegers = mIntegers.length();

	for(i=0;i<cycleIntegers;i++)
	{
		sax3dw.setHasMultiple(true);
		writeMetadataNode(mIntegers.operator [](i), msMetaI, "metadataStorage");
	}

	//MetadataString Nodes
	metaInt = X3DMETAST;
	MStringArray mStrings = x3dMetadataNames(metaInt);
	unsigned int cycleStrings = mStrings.length();

	for(i=0;i<cycleStrings;i++)
	{
		sax3dw.setHasMultiple(true);
		writeMetadataNode(mStrings.operator [](i), msMetaSt, "metadataStorage");
	}

	//MetadataSet Nodes
	metaInt = X3DMETASE;
	MStringArray mSets = x3dMetadataNames(metaInt);
	unsigned int cycleSets = mSets.length();

	for(i=0;i<cycleSets;i++)
	{
		sax3dw.setHasMultiple(true);
		writeMetadataNode(mSets.operator [](i), msMetaSe, "metadataStorage");
	}
}

void x3dExportOrganizer::writeHiddenNodes()
//This method puts media files at the front of the X3D file,
//hidden under an X3D Switch Node whose "whichChoice"
//field is set to -1. This is done so that image, movie,
//and sound nodes will load upfront possible.
{
	//User feedback telling the content author that
	//the X3D nodes for external media are being
	//written to the file
	if(!isTreeBuilding)
	{
		sax3dw.msg.set("Exporting Hidden Nodes");
		cout << sax3dw.msg.asChar() << endl;
		sax3dw.msg.set(" ");
		cout << sax3dw.msg.asChar() << endl;
	}

	if((exMetadata == 1 && exEncoding != VRML97ENC) || exTextures == 1 || exAudio == 1 || exInline == 1 || exRigidBody == true)
	{
		MStringArray se1;
		MStringArray se2;
//Binary Script issues
//		if(exEncoding == X3DBENC)
//		{
//			se1.append("url");
//			se2.append("\"HiddenNodes_0.js\"");
//		}
		// end issues
		if(!isTreeBuilding)
		{
			sax3dw.startNode(msScript, "HiddenNodes", se1, se2, true);
				se1.clear();
				se2.clear();
				se1.append(MString("name"));
				se1.append(MString("type"));
				se1.append(MString("accessType"));
				se2.append("metadataStorage");
				se2.append("MFNode");
				se2.append("initializeOnly");
		}
		else buildUITreeNode("","",msScript, "DEF", "HiddenNodes");

		if(!isTreeBuilding)
		{
			if(exMetadata == 1 && exEncoding != VRML97ENC)
			{
				sax3dw.addScriptNodeField("initializeOnly", "MFNode", "metadataStorage");
				sax3dw.writeSBracket();
				if(exEncoding == X3DENC || exEncoding == X3DBENC) sax3dw.startNode(msfield, msEmpty, se1, se2, true);
					 setUpMetadataNodes();
				sax3dw.writeEBracket();
				if(exEncoding == X3DENC || exEncoding == X3DBENC) sax3dw.endNode(msfield, msEmpty);
			}
		}
		else
		{
			treeTabs = treeTabs + 1;
			if(ttabsMax < treeTabs) ttabsMax = treeTabs;
			setUpMetadataNodes();
			treeTabs = treeTabs - 1;
		}

		if(!isTreeBuilding)
		{
			if(exTextures == 1)
			{
				se2.operator [](0).set("textureStorage");
				sax3dw.addScriptNodeField("initializeOnly", "MFNode", "textureStorage");
				sax3dw.writeSBracket();
				if(exEncoding == X3DENC || exEncoding == X3DBENC) sax3dw.startNode(msfield, msEmpty, se1, se2, true);
					outputFiles();
				sax3dw.writeEBracket();
				if(exEncoding == X3DENC || exEncoding == X3DBENC) sax3dw.endNode(msfield, msEmpty);
			}
		}
		else
		{
			treeTabs = treeTabs + 1;
			if(ttabsMax < treeTabs) ttabsMax = treeTabs;
			outputFiles();
			treeTabs = treeTabs - 1;
		}

		if(!isTreeBuilding)
		{
			if(exAudio == 1)
			{
				se2.operator [](0).set("audioStorage");
				sax3dw.addScriptNodeField("initializeOnly", "MFNode", "audioStorage");
				sax3dw.writeSBracket();
				if(exEncoding == X3DENC || exEncoding == X3DBENC) sax3dw.startNode(msfield, msEmpty, se1, se2, true);
					outputAudio();
				sax3dw.writeEBracket();
				if(exEncoding == X3DENC || exEncoding == X3DBENC) sax3dw.endNode(msfield, msEmpty);
			}
		}
		else
		{
			treeTabs = treeTabs + 1;
			if(ttabsMax < treeTabs) ttabsMax = treeTabs;
			outputAudio();
			treeTabs = treeTabs - 1;
		}

		if(!isTreeBuilding)
		{
			if(exRigidBody == true && exEncoding != VRML97ENC)
			{
				se2.operator [](0).set("colliders");
				sax3dw.addScriptNodeField("initializeOnly", "MFNode", "colliders");
				sax3dw.writeSBracket();
				if(exEncoding == X3DENC || exEncoding == X3DBENC) sax3dw.startNode(msfield, msEmpty, se1, se2, true);
					outputCollidableShapes();
				sax3dw.writeEBracket();
				if(exEncoding == X3DENC || exEncoding == X3DBENC) sax3dw.endNode(msfield, msEmpty);
			}
		}
		else
		{
			if(exEncoding != VRML97ENC)
			{
				treeTabs = treeTabs + 1;
				if(ttabsMax < treeTabs) ttabsMax = treeTabs;
				outputCollidableShapes();
				treeTabs = treeTabs - 1;
			}
		}

		if(!isTreeBuilding)
		{
			if(exInline == 1)
			{
				se2.operator [](0).set("inlineStorage");
				sax3dw.addScriptNodeField("initializeOnly", "MFNode", "inlineStorage");
				sax3dw.writeSBracket();
				if(exEncoding == X3DENC || exEncoding == X3DBENC) sax3dw.startNode(msfield, msEmpty, se1, se2, true);
					outputInlines();
				sax3dw.writeEBracket();
				if(exEncoding == X3DENC || exEncoding == X3DBENC) sax3dw.endNode(msfield, msEmpty);
			}
		}
		else
		{
			treeTabs = treeTabs + 1;
			if(ttabsMax < treeTabs) ttabsMax = treeTabs;
			outputInlines();
			treeTabs = treeTabs - 1;
		}
/*
		if(exEncoding == VRML97ENC && isTreeBuilding != true)
		{
			sax3dw.preWriteField("url");
			MString scriptString("\"javascript: \n\n");
			scriptString.operator +=("	function getResponse(value, timestamp)\n");
			scriptString.operator +=("	{\n");
			scriptString.operator +=("		if(value == true)\n");
			scriptString.operator +=("		{\n");
			scriptString.operator +=("			giveResponse = new SFString('Media Script Node Exists');\n");
			scriptString.operator +=("		}\n");
			scriptString.operator +=("	}\"\n");
			scriptString.operator +=("	eventIn SFBool getResponse\n");
			scriptString.operator +=("	eventOut SFString giveResponse\n"); 
			sax3dw.writeRawCode(scriptString);
		}

		if(exEncoding == X3DVENC && isTreeBuilding != true)
		{
			sax3dw.preWriteField("url");
			MString scriptString("\"ecmascript: \n\n");
			scriptString.operator +=("	function getResponse(value, timestamp)\n");
			scriptString.operator +=("	{\n");
			scriptString.operator +=("		if(value == true)\n");
			scriptString.operator +=("		{\n");
			scriptString.operator +=("			giveResponse = new SFString('Media Script Node Exists');\n");
			scriptString.operator +=("		}\n");
			scriptString.operator +=("	}\"\n");
			scriptString.operator +=("	inputOnly SFBool getResponse\n");
			scriptString.operator +=("	outputOnly SFString giveResponse\n"); 

			sax3dw.writeRawCode(scriptString);
		}
//Binary script issue
//		if((exEncoding == X3DENC || exEncoding == X3DBENC) && isTreeBuilding != true)
		if(exEncoding == X3DENC && isTreeBuilding != true)
		{
			MString rawField("			<field name='getResponse' type='SFBool' accessType='inputOnly'/>\n");
			rawField.operator +=("			<field name='giveResponse' type='SFString' accessType='outputOnly'/>\n");
			sax3dw.writeRawCode(rawField);

			MString scriptString("ecmascript: \n\n");
			scriptString.operator +=("function getResponse(value, timestamp)\n");
			scriptString.operator +=("{\n");
			scriptString.operator +=("	if(value == true)\n");
			scriptString.operator +=("	{\n");
			scriptString.operator +=("		giveResponse = new SFString('Media Script Node Exists');\n");
			scriptString.operator +=("	}\n");
			scriptString.operator +=("}\n");

			MStringArray ssArray;
			ssArray.append(scriptString);
			sax3dw.outputCData(ssArray);
		}
//Binary script issues begin here
		if(exEncoding == X3DBENC && isTreeBuilding != true)
		{
			MString rawField("			<field name='getResponse' type='SFBool' accessType='inputOnly'/>\n");
			rawField.operator +=("			<field name='giveResponse' type='SFString' accessType='outputOnly'/>\n");
			sax3dw.writeRawCode(rawField);

			MString scriptString("ecmascript: \n\n");
			scriptString.operator +=("function getResponse(value, timestamp)\n");
			scriptString.operator +=("{\n");
			scriptString.operator +=("	if(value == true)\n");
			scriptString.operator +=("	{\n");
			scriptString.operator +=("		giveResponse = new SFString('Media Script Node Exists');\n");
			scriptString.operator +=("	}\n");
			scriptString.operator +=("}\n");
			sax3dw.writeScriptFile("HiddenNodes_0.js", scriptString, localPath);
		}
		*/
		//
		if(!isTreeBuilding) sax3dw.endNode(msScript, "HiddenNodes");
	}
	isDone = true;
}



//-----------------------------------------------------------
//Procedure to export entire sceneGraph starting at the world root
//----------------------------------------------------------- 
MStatus x3dExportOrganizer::exportAll() 
{

	MStatus status;

	//Code necessary for grabbing the worldRoot of the DAG
	//The DAG is similar to a scenegraph.

	//Creates a DAG Interactor that can be used to 
	//traverse the DAG.
	MItDag itDag(MItDag::kDepthFirst, MFn::kTransform, &status);

	//itDag.root grabs the root node to the top level of the 
	//DAG Iterator. In this case, it is the worldRoot
	worldRoot = itDag.root();

	//Adds DagNode functionality to the worldRoot object
	MFnDagNode dagFn(worldRoot);

//	cout << "Contructing a Dag List for Mesh Nodes" << endl;
//	avatarMeshNames.clear();
//	avatarDagPaths.clear();
//	buildMeshDagList(dagFn);

//	MGlobal::displayInfo("Processing Branch Node");
	//Starts processing of the Directed Acyclic Graph's first object
	processBranchNode(dagFn.object(),0);
	if(exRigidBody) processDynamics();
	processScripts();
	isDone = true;

	return MStatus::kSuccess;
}

MStatus x3dExportOrganizer::exportSelected() 
{
	MStatus status;
	MSelectionList activeList;
	MGlobal::getActiveSelectionList(activeList);
    MItSelectionList iterGP( activeList );
	MItDag itDagGP(MItDag::kDepthFirst, MFn::kTransform, &status);

//	avatarMeshNames.clear();
//	avatarDagPaths.clear();
	while(!iterGP.isDone())
	{
        MDagPath dagPath;		
		MObject container;
        MStatus dStat = iterGP.getDagPath( dagPath, container );
		if(dStat.operator ==(MStatus::kSuccess))
		{
			itDagGP.reset(dagPath, MItDag::kDepthFirst, MFn::kTransform);
			MObject topNode;
			topNode = itDagGP.root();
			MFnDagNode dagFn( topNode );
//			buildMeshDagList(dagFn);
		}
		else
		{
//			iter.getDependNode(container);
//			MFnDependencyNode depNode(container);
//			MString nodeType = depNode.typeName();
		}
		iterGP.next();
	}

	MItSelectionList iter( activeList );
	MItDag itDag(MItDag::kDepthFirst, MFn::kTransform, &status);
	while(!iter.isDone())
	{
		MObject hidObj;
		iter.getDependNode(hidObj);
		MFnDependencyNode hidNodes(hidObj);

		if(!(showHiddenForTree(hidNodes.object()) && isTreeBuilding))
		{
		
			MDagPath dagPath;		
			MObject container;
			MStatus dStat = iter.getDagPath( dagPath, container );
			if(dStat.operator ==(MStatus::kSuccess))
			{
				itDag.reset(dagPath, MItDag::kDepthFirst, MFn::kTransform);
				MObject topNode;
				topNode = itDag.root();
				MFnDagNode dagFn( topNode );
				processChildNode(dagFn.object(), 0);
			}
			else
			{
	//			iter.getDependNode(container);
	//			MFnDependencyNode depNode(container);
	//			MString nodeType = depNode.typeName();
			}
		}
		iter.next();
	}

	isDone = true;
	return MStatus::kSuccess;
}

//bool x3dExportOrganizer::showHiddenForTree(MFnDependencyNode depNode)
bool x3dExportOrganizer::showHiddenForTree(MObject mObj)
{
	MFnDependencyNode depNode(mObj);
	bool isHidden = false;
	MString tn = depNode.typeName();
	if(tn.operator ==("mesh"))
	{
		MObject dObj = depNode.object();
		MFnDagNode mDag(dObj);
		MObject pObj = mDag.parent(0);
		MFnDagNode pDag(pObj);
		isHidden = getRigidBodyState(pDag.object()); 
		if(isHidden) outputCollidableShapes();
	}

//	if(tn.operator ==("x3dInline"))
//	{
//		outputInlines();
//		isHidden = true;
//	}
	if(tn.operator ==("x3dMetadataString") || tn.operator ==("x3dMetadataSet") || tn.operator ==("x3dMetadataInteger") || tn.operator ==("x3dMetadataFloat") || tn.operator ==("x3dMetadataDouble"))
	{
		setUpMetadataNodes();
		isHidden = true;
	}
	if(tn.operator ==("audio"))
	{
		outputAudio();
		isHidden = true;
	}
	if(tn.operator ==("file") || tn.operator ==("buldge") || tn.operator ==("checker") || tn.operator ==("cloth") || tn.operator ==("fractal") || tn.operator ==("grid") || tn.operator ==("mountain") || tn.operator ==("movie") || tn.operator ==("noise") || tn.operator ==("ocean") || tn.operator ==("ramp") || tn.operator ==("water") || tn.operator ==("layeredTexture"))
	{
		outputFiles();
		isHidden = true;
	}

	if(tn.operator ==("rigidSolver"))
	{
		processRigidBody(depNode.object());
		isHidden = true;
	}

   return isHidden;
}

void x3dExportOrganizer::buildUITreeNode(MString mayaType, MString mayaName, MString x3dType, MString x3dUse, MString x3dName)
{
	x3dTreeStrings.operator +=("*");
	unsigned int i;
	for(i=0; i < treeTabs; i++)
	{
		x3dTreeStrings.operator +=(" ");
	}
	x3dTreeStrings.operator +=(x3dType);
	x3dTreeStrings.operator +=(" ");
	x3dTreeStrings.operator +=(x3dUse);
	x3dTreeStrings.operator +=(" ");
	x3dTreeStrings.operator +=(x3dName);

//	switch(updateMethod)
//	{
//		case 1:
//			break;
//		case 2:
			if(x3dUse == "DEF")
			{
				x3dTreeDelStrings.operator +=("*");
				x3dTreeDelStrings.operator +=(x3dName);
			}
//			break;
//		default:
//			break;
//	}

}

//void x3dExportOrganizer::processGrouping(MFnDagNode dagFn, MString proxyNode, MStringArray fNames, MStringArray fValues, bool isOE, int remNum, bool hasMeta)
void x3dExportOrganizer::processGrouping(MObject mObj, MString proxyNode, MStringArray fNames, MStringArray fValues, bool isOE, int remNum, bool hasMeta)
{
	MFnDagNode dagFn(mObj);

	unsigned int fv = fValues.length();
	unsigned int childVal = 4;
	if(dagFn.typeName() == "x3dSwitch" && exEncoding == VRML97ENC) childVal = 101;
	if(dagFn.typeName() == "lodGroup" && exEncoding == VRML97ENC) childVal = 102;

	MString nString;
	nString.operator +=(dagFn.name());
	nString.operator +=("Parent");

	unsigned int hasRigidBody = getRigidBodyState(dagFn.object());

	if(!hasRigidBody)
	{
		if(isTreeBuilding)
		{
			if(dagFn.typeName() != "x3dGroup" && dagFn.typeName() != "transform")
			{
				buildUITreeNode("transform", nString, msTransform, "DEF", nString);
				treeTabs = treeTabs + 1;
				if(ttabsMax < treeTabs) ttabsMax = treeTabs;
			}
			if(dagFn.typeName() != "x3dInline")
			{
				buildUITreeNode(dagFn.typeName(), dagFn.name(), checkUseType(dagFn.name()), "DEF", dagFn.name());
				treeTabs = treeTabs + 1;
				if(ttabsMax < treeTabs) ttabsMax = treeTabs;

				if(hasMeta) addMetadataTag(dagFn.name());
				if(proxyNode != msEmpty) writeNodeField(dagFn.object(), proxyNode, "proxy");
			
				if(dagFn.typeName() != "x3dInline") processBranchNode(dagFn.object(), childVal);

				treeTabs = treeTabs - 1;
			}
			else writeInline(dagFn.object(), "children");//buildUITreeNode(dagFn.typeName(), dagFn.name(), checkUseType(dagFn.name()), "USE", dagFn.name());

			if(dagFn.typeName() != "x3dGroup" && dagFn.typeName() != "transform") treeTabs = treeTabs - 1;
		}
		else
		{
			if(dagFn.typeName() != "x3dGroup" && dagFn.typeName() != "transform")
			{

				MStringArray pArray1 = web3dem.getTransFields();

				MObject tObj = dagFn.object();
				MFnDependencyNode tDepFn(tObj);

				MStringArray pArray2 = web3dem.getTransFieldValues(tDepFn,0);
				pArray1.append("containerField");
				MString nContVal = fValues.operator [](fv-1);
				pArray2.append(nContVal);

				sax3dw.startNode(msTransform, nString, pArray1, pArray2, true);
			}//grouphanim
				if(proxyNode != msEmpty) isOE = true;
				if(dagFn.typeName() != "x3dGroup" && dagFn.typeName() != "transform") fValues.operator [](fv-1).set("children");
				if(hasMeta == false && dagFn.typeName()=="x3dInline") isOE = false;
				if(dagFn.typeName() != "x3dInline")
				{
					sax3dw.startNode(checkUseType(dagFn.name()), dagFn.name(), fNames, fValues, isOE);
						if(hasMeta) addMetadataTag(dagFn.name());
						if(dagFn.typeName() != "x3dInline")
						{
							if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
							{
								if(remNum > 1)
								{
									sax3dw.preWriteField(getCFValue(childVal));
									sax3dw.writeSBracket();
									processBranchNode(dagFn.object(), 0);
								}
								else processBranchNode(dagFn.object(), childVal);
								if(remNum > 1) sax3dw.writeEBracket();
							}
							else processBranchNode(dagFn.object(), childVal);
							if(proxyNode != msEmpty) writeNodeField(dagFn.object(), proxyNode, "proxy");
						}				
					if(isOE) sax3dw.endNode(checkUseType(dagFn.name()), dagFn.name());
				}
				else
				{
					sax3dw.preWriteField("children");
					writeInline(dagFn.object(), "children");
//					sax3dw.useDecl(msInline, dagFn.name(), "containerField", "children");
				}
			if(dagFn.typeName() != "x3dGroup" && dagFn.typeName() != "transform") sax3dw.endNode(msTransform, nString);
		}
	}
}

//void x3dExportOrganizer::evalForSyblings(MFnDagNode dagFn, MString contFieldName, unsigned int& remNum, unsigned int& remNum1)
void x3dExportOrganizer::evalForSyblings(MObject mObj, MString contFieldName, unsigned int& remNum, unsigned int& remNum1)
{
	MFnDagNode dagFn(mObj);

	unsigned int newNum = dagFn.childCount();
	unsigned int sybNum = 0;
	unsigned int i;
//	if(asSyblings){
		for(i=0;i<newNum;i++)
		{
			MObject obj = dagFn.child(i);
//			MFnDependencyNode ndep(obj);
			MFnDagNode ndep(obj);
			MString nType = ndep.typeName();
			MStringArray grArray1;
			MStringArray grArray2;
			if(!isTreeBuilding)
			{
				grArray1 = web3dem.getX3DFields(ndep, 0);
				grArray2 = web3dem.getX3DFieldValues(ndep, 0);
			}
			grArray1.append("containerField");
			grArray2.append(contFieldName);

			if(nType.operator ==(X3D_VIEW))
			{
				writeLeafNodes(ndep.name(), ndep.object(), ndep.name(), msViewpoint, grArray1, grArray2);
				sybNum++;
			}
			else if(nType.operator ==(X3D_DIRLIGHT))
			{
				writeLeafNodes(ndep.name(), ndep.object(), ndep.name(), msDirectionalLight, grArray1, grArray2);
				sybNum++;
			}
			else if(nType.operator ==(X3D_SPOTLIGHT))
			{
				writeLeafNodes(ndep.name(), ndep.object(), ndep.name(), msSpotLight, grArray1, grArray2);
				sybNum++;
			}
			else if(nType.operator ==(X3D_POINTLIGHT))
			{
				writeLeafNodes(ndep.name(), ndep.object(), ndep.name(), msPointLight, grArray1, grArray2);
				sybNum++;
			}
			else if(nType.operator ==(X3D_AMBLIGHT))
			{
				//writeLeafNodes(ndep.name(), ndep.object(), ndep.name(), msPointLight, grArray1, grArray2);
				sybNum++;
			}
			else if(nType.operator ==(X3D_AREALIGHT)) sybNum++;
			else if(nType.operator ==(X3D_VOLLIGHT)) sybNum++;
			else if(nType.operator ==(X3D_HANIMJOINT))
			{
//				cout << "Finds HAnimJoint" << endl;
				sybNum++;
				if(exEncoding != VRML97ENC && exHAnim == true)
				{
					MPlug ioPlug = ndep.findPlug("intermediateObject");
					bool ioBool = false;
					ioPlug.getValue(ioBool);
					if(!ioBool)
					{
						if(i == 0) writeHAnimHumanoid(ndep.object(), dagFn.object(), i, grArray1, grArray2);
					}
				}
			}
			else if(nType.operator ==(X3D_MESH))
			{
				if(getCharacterState(ndep.object())) sybNum++;
				bool isInter = evalIntermediacy(ndep.name());
				if(isInter == true) sybNum++;
			}
			else if(nType.operator ==(X3D_SCRIPT))
			{
				sybNum++;
			}
		}
//	}
	remNum = newNum - sybNum;
	remNum1 = 0;

//	if(remNum > 0) remNum1 = 1;
	if(sybNum > 0) remNum1 = 1;

}

bool x3dExportOrganizer::evalIntermediacy(MString nodeName)
{
//	MFnDependencyNode newDepFn = web3dem.getMyDepNode(nodeName);
	MFnDependencyNode newDepFn(web3dem.getMyDepNodeObj(nodeName));
	bool isInter = false;
	MStatus nStatus;
	MPlug aPlug = newDepFn.findPlug("intermediateObject", &nStatus);
	if(nStatus == MStatus::kSuccess)
	{
		aPlug.getValue(isInter);
	}
	return isInter;
}

void x3dExportOrganizer::setIgnoreStatusForDefaults()
{
		sax3dw.setIgnored("persp");
		sax3dw.setIgnored("top");
		sax3dw.setIgnored("front");
		sax3dw.setIgnored("side");
		sax3dw.setIgnored("groundPlane_transform");
		sax3dw.setIgnored("defaultUfeProxyCameraTransformParent");
}

//MStatus x3dExportOrganizer::processBranchNode(MFnDagNode dagFn, int cfChoice1)
//At this point, we are only interested in the children of dagFn.
MStatus x3dExportOrganizer::processBranchNode(MObject mObj, int cfChoice1)
{
	MFnDagNode dagFn(mObj);
	unsigned int cNumb = dagFn.childCount();
	unsigned int cCount;


	//Processes the "cCount" index of dagFn
	for ( cCount = 0; cCount < cNumb; cCount++)
	{

		//grabs the cCount child as an MObject
		MObject aChild = dagFn.child(cCount);

		//Adds DagNode functionality to that object
		MFnDagNode newDagFn(aChild);

		processChildNode(newDagFn.object(), cfChoice1);
	}

	return MStatus::kSuccess;
}

//void x3dExportOrganizer::processChildNode(MFnDagNode newDagFn, int cfChoice1)//999111999
void x3dExportOrganizer::processChildNode(MObject mObj, int cfChoice1)//999111999
{
	processChildNode(mObj, cfChoice1, "");
}

//void x3dExportOrganizer::processChildNode(MFnDagNode newDagFn, int cfChoice1, MString cfString)
void x3dExportOrganizer::processChildNode(MObject mObj, int cfChoice1, MString cfString)
{
	MFnDagNode newDagFn(mObj);
	if(hasPassed == false)
	{
		hasPassed = isTreeBuilding;
		int nVal = 0;
		MString tName = newDagFn.name();
		while(!newDagFn.hasUniqueName())
		{
			nVal = nVal-1;
			MString nValStr;
			nValStr.set(nVal);
			MString ntName(tName);
			ntName.operator +=(nValStr);
			newDagFn.setName(ntName);
		}

		//Retrieves the name of that node
		MString childName = newDagFn.name();


		MString contFieldName(cfString);
		if(contFieldName.operator ==("")) contFieldName = getCFValue(cfChoice1);

		//There are certain specific nodes that we don't
		//want exported. If okUse == 1, then the newDagFn
		//object is used for export. If okUse == 0, the 
		//newDagFn is not.
		bool okUse = true;

		//Two MStringArrays that are used for setting up node fields.
		//grArray1 is used for field names.
		MStringArray grArray1;

		//grArray2 is used for field values
		MStringArray grArray2;

		//This tells us what type of Maya node the newDagFn object is.
		MString childType = newDagFn.typeName();
		//Skip all nodes that have an okUse value of 0
		if(evalIntermediacy(childName)) okUse = false;
		if(sax3dw.checkIfIgnored(childName)) okUse = false;
//		if(isReferenceNode(childName)) okUse = false;
		if(isInHiddenLayer(childName)) okUse = false;
		if(okUse){
			
			//Retrieves the field names for a transform node
			//and stores them as MStrings in the MStringArray
			//named grArray1 using a MEL procedure found in the
			//x3d_exporter_procedures.mel file.
			if(!isTreeBuilding) grArray1 = web3dem.getX3DFields(newDagFn, 0);
			grArray1.append(MString("containerField"));

			//Retrieves the field values for this transform node
			//and stores them as MStrings in the MStringArray
			//named grArray2 using a MEL procedure found in the
			//x3d_exporter_procedures.mel file.
			//length of grArray2 is now equal to the length of
			//grArray1 - 1.
//			cout << "try it" << endl;
			if(!isTreeBuilding) grArray2 = web3dem.getX3DFieldValues(newDagFn, 0);
			grArray2.append(contFieldName);
//			cout << "try end" << endl;

			//We use the node name "childName" to find out whether or
			//not this node has already been written to the file.
			//This is done through the checkIfHasBeen method.
//			if(childType == MString(X3D_MESH)) writeMeshShape(newDagFn.object(), cfChoice1);
			if(childType == MString(X3D_MESH)){//999111

//				if(exRigidBody == true)
//				{
					if(!getCharacterState(newDagFn.object()))
					{
						MObject pObjectNode = newDagFn.parent(0);
						MFnDagNode parentDagFn(pObjectNode);

						if(!getRigidBodyState(parentDagFn.object())) writeMeshShape(newDagFn.object(), contFieldName);
					}
//				}
//				else writeMeshShape(newDagFn, contFieldName);

//				writeMeshShape(newDagFn, contFieldName);
			}
			else 
			{
				bool ciHasBeen = sax3dw.checkIfHasBeen(childName);
				bool isAvatar = checkForAvatar(newDagFn.object());
				if(ciHasBeen == false)
				{
					//User feedback telling the content author 
					//that a particular node is being exported.
					if(!isTreeBuilding)
					{
						sax3dw.msg.set("Exporting node: ");
						sax3dw.msg.operator +=(childName);
						cout << sax3dw.msg.asChar() << endl;
						sax3dw.msg.set(" ");
						cout << sax3dw.msg.asChar() << endl;
					}
	
					//used to change the containerField value in C++
					//without having to re-request all of a node's
					//field values through a MEL procedure call.
					unsigned int gra2 = grArray2.length();
					int cfInt = gra2-1;

					//Group node export similar in manner to export
					//of an actual transform node where children are
					//concerned.
//					if(childType == X3D_TRANS || childType == X3D_GROUP || childType == X3D_SWITCH || childType == X3D_INLINE || childType == X3D_LOD || childType == X3D_ANCHOR){
					if(childType == X3D_TRANS || childType == X3D_GROUP || childType == X3D_SWITCH || childType == X3D_LOD || childType == X3D_ANCHOR || childType == X3D_BILLBOARD){

						unsigned int remNum;
						unsigned int remNum1;
						evalForSyblings(newDagFn.object(), contFieldName, remNum, remNum1);

						bool isOE = false;
						if(remNum > 0) isOE = true;
						bool hasMeta = false;
						hasMeta = checkForMetadata(childName);
						if(hasMeta) isOE = true;

						if(isAvatar == true && exEncoding != VRML97ENC && exHAnim == true && childType == X3D_TRANS)
						{

						}
						else
						{
							if(remNum > 0)	processGrouping(newDagFn.object(), msEmpty, grArray1, grArray2, isOE, remNum, hasMeta);
							else if(remNum1 > 0)
							{
	//							cout << "Use Empties 1: " << newDagFn.name().asChar() << " - "<< useEmpties << endl;
								if(useEmpties)
								{
	//								cout << "Use Empties 2: " << newDagFn.name().asChar() << endl;
									processGrouping(newDagFn.object(), msEmpty, grArray1, grArray2, isOE, remNum, hasMeta);
								}
							}
							else processGrouping(newDagFn.object(), msEmpty, grArray1, grArray2, isOE, remNum, hasMeta);
						}
					}

					//Collision node export similar in manner to export
					//of an actual transform node where children are
					//concerned.
					//
					//Also checks for a proxy node. If it exists, RawKee
					//uses the writeNodeField method to follow a node
					//found in an SFNode field, such as the "proxy" 
					//field. If the proxy node has already been 
					//exported, RawKee writes out a USE version of the 
					//node. However, should RawKee need to write out the 
					//node and its children, any future writes of this node
					//will implement a USE version of it.
					if(childType == MString(X3D_COLLISION)){
						MStatus nStatus;
						MPlug aPlug = newDagFn.findPlug(MString("proxy"), &nStatus);
						MString proxyNode;
						aPlug.getValue(proxyNode);
//						cout << "Proxy Value: " << proxyNode << endl;

						unsigned int remNum;
						unsigned int remNum1;
						evalForSyblings(newDagFn.object(), contFieldName, remNum, remNum1);

						bool isOE = false;
						if(remNum > 0) isOE = true;
						bool hasMeta = false;
						hasMeta = checkForMetadata(childName);
						if(hasMeta) isOE = true;

						if(remNum > 0)	processGrouping(newDagFn.object(), proxyNode, grArray1, grArray2, isOE, remNum, hasMeta);
						else if(remNum1 > 0)
						{
							if(useEmpties) processGrouping(newDagFn.object(), proxyNode, grArray1, grArray2, isOE, remNum, hasMeta);
						}
						else processGrouping(newDagFn.object(), proxyNode, grArray1, grArray2, isOE, remNum, hasMeta);
					}

					//Shape is a complicated branch of the DAG to
					//traverse. It involves getting at underworld nodes
					//and appearnce/texture related Dependency Graph (DG)
					//nodes that are not part of the DAG. It has its
					//own export method.
	//				if(childType == MString(X3D_MESH)) writeMeshShape(newDagFn, cfChoice1);
				
					//Simple method for writing out leaf nodes 9999
					if(childType == X3D_INLINE)
					{
						cout << "Inline Found" << endl;
						writeLeafNodes(childName, newDagFn.object(), childName, msInline, grArray1, grArray2);
					}
					if(childType == X3D_HANIMJOINT && exEncoding != VRML97ENC && exHAnim == true && isTreeBuilding == true) writeHAnimJointForTree(newDagFn.object());
					if(childType == X3D_TIMESENSOR) writeLeafNodes(childName, newDagFn.object(), childName, msTimeSensor, grArray1, grArray2);
					if(childType == X3D_TOUCHSENSOR) writeLeafNodes(childName, newDagFn.object(), childName, msTouchSensor, grArray1, grArray2);
					if(childType == X3D_GAMEPADSENSOR && exEncoding !=VRML97ENC && exIODevice == true) writeLeafNodes(childName, newDagFn.object(), childName, msGamepadSensor, grArray1, grArray2);
					if(childType == X3D_LOADSENSOR && exEncoding != VRML97ENC) writeLeafNodes(childName, newDagFn.object(), childName, msLoadSensor, grArray1, grArray2);
					if(childType == X3D_CYLSENSOR) writeLeafNodes(childName, newDagFn.object(), childName, msCylinderSensor, grArray1, grArray2);
					if(childType == X3D_PLANESENSOR) writeLeafNodes(childName, newDagFn.object(), childName, msPlaneSensor, grArray1, grArray2);
					if(childType == X3D_SPHERESENSOR) writeLeafNodes(childName, newDagFn.object(), childName, msSphereSensor, grArray1, grArray2);
					if(childType == X3D_KEYSENSOR && exEncoding != VRML97ENC) writeLeafNodes(childName, newDagFn.object(), childName, msKeySensor, grArray1, grArray2);
					if(childType == X3D_STRINGSENSOR && exEncoding != VRML97ENC) writeLeafNodes(childName, newDagFn.object(), childName, msStringSensor, grArray1, grArray2);

					if(childType == X3D_PROXSENSOR) writeLeafNodes(childName, newDagFn.object(), childName, msProximitySensor, grArray1, grArray2);
					if(childType == X3D_VISSENSOR) writeLeafNodes(childName, newDagFn.object(), childName, msVisibilitySensor, grArray1, grArray2);

					if(childType == X3D_NAVIGATION) writeLeafNodes(childName, newDagFn.object(), childName, msNavigationInfo, grArray1, grArray2);
					if(childType == X3D_WORLDINFO) writeLeafNodes(childName, newDagFn.object(), childName, msWorldInfo, grArray1, grArray2);

					if(childType == X3D_SOUND) writeLeafNodes(childName, newDagFn.object(), childName, msSound, grArray1, grArray2);

					if(childType == X3D_POSINTER) writeLeafNodes(childName, newDagFn.object(), childName, msPositionInterpolator, grArray1, grArray2);
					if(childType == X3D_ORIINTER) writeLeafNodes(childName, newDagFn.object(), childName, msOrientationInterpolator, grArray1, grArray2);
					if(childType == X3D_COORDINTER) writeLeafNodes(childName, newDagFn.object(), childName, msCoordinateInterpolator, grArray1, grArray2);
					if(childType == X3D_NORMINTER) writeLeafNodes(childName, newDagFn.object(), childName, msNormalInterpolator, grArray1, grArray2);
					if(childType == X3D_SCALINTER) writeLeafNodes(childName, newDagFn.object(), childName, msScalarInterpolator, grArray1, grArray2);
					if(childType == X3D_COLORINTER) writeLeafNodes(childName, newDagFn.object(), childName, msColorInterpolator, grArray1, grArray2);

					if(childType == X3D_BOOLSEQ && exEncoding != VRML97ENC) writeLeafNodes(childName, newDagFn.object(), childName, msBooleanSequencer, grArray1, grArray2);
					if(childType == X3D_INTSEQ && exEncoding != VRML97ENC) writeLeafNodes(childName, newDagFn.object(), childName, msIntegerSequencer, grArray1, grArray2);

					if(childType == X3D_BOOLTRIGGER && exEncoding != VRML97ENC) writeLeafNodes(childName, newDagFn.object(), childName, msBooleanTrigger, grArray1, grArray2);
					if(childType == X3D_BOOLTOGGLE && exEncoding != VRML97ENC) writeLeafNodes(childName, newDagFn.object(), childName, msBooleanToggle, grArray1, grArray2);
					if(childType == X3D_BOOLFILTER && exEncoding != VRML97ENC) writeLeafNodes(childName, newDagFn.object(), childName, msBooleanFilter, grArray1, grArray2);
					if(childType == X3D_INTTRIGGER && exEncoding != VRML97ENC) writeLeafNodes(childName, newDagFn.object(), childName, msIntegerTrigger, grArray1, grArray2);
					if(childType == X3D_TIMETRIGGER && exEncoding != VRML97ENC) writeLeafNodes(childName, newDagFn.object(), childName, msTimeTrigger, grArray1, grArray2);

					//Script is a node to write in XML because it involves 
					//getting writing out URL strings within the tag, and
					//writing out CData for local url scripts. It has its
					//own export method.
//					if(childType == X3D_SCRIPT) writeScript(newDagFn, contFieldName);
					if(childType == X3D_SCRIPT && isTreeBuilding == true) writeScript(newDagFn.object(), contFieldName);
					//Adds the node name to the list of node names
					//that have already been written to the file.
					
					
					unsigned int hasRigidBody = 0;
					if(childType == X3D_TRANS) hasRigidBody = getRigidBodyState(newDagFn.object());
					if(!hasRigidBody) sax3dw.setAsHasBeen(childName);
				}
				else
				{
			
					//returns the type of X3D node as an MString
					//based upon the type of Maya node by using
					//the node's name to request the node type.
					MString tempString = checkUseType(childName);

					//sets the only field name to be used by sax3dw.useDecl
					//method
					MString contField("containerField");

					//gets the string value to be used for the containerField
					//value
					MString contVal(cfString);
					if(contVal.operator ==("")) contVal = getCFValue(cfChoice1);

//					if(childType == X3D_TRANS || childType == X3D_COLLISION || childType == X3D_GROUP || childType == X3D_SWITCH || childType == X3D_INLINE || childType == X3D_LOD || childType == X3D_ANCHOR)
					if(childType == X3D_TRANS || childType == X3D_COLLISION || childType == X3D_GROUP || childType == X3D_SWITCH || childType == X3D_LOD || childType == X3D_ANCHOR || childType == X3D_BILLBOARD)
					{

						unsigned int remNum;
						unsigned int remNum1;
						evalForSyblings(newDagFn.object(), contFieldName, remNum, remNum1);

//						bool isOE = false;

						if(isAvatar == true && exEncoding != VRML97ENC && exHAnim == true && childType == X3D_TRANS)
						{

						}
						else
						{
							if(remNum > 0)	processUsedGrouping(newDagFn.object(), childName, tempString, contVal, contField);
							else if(remNum1 > 0)
							{
	//							cout << "Use Empties 1: " << newDagFn.name().asChar() << " - "<< useEmpties << endl;
								if(useEmpties)
								{
	//								cout << "Use Empties 2: " << newDagFn.name().asChar() << endl;
									processUsedGrouping(newDagFn.object(), childName, tempString, contVal, contField);
								}
							}
							else processUsedGrouping(newDagFn.object(), childName, tempString, contVal, contField);
						}
					}
					else if(childType == X3D_INLINE)
					{
						if(isTreeBuilding)
						{
							buildUITreeNode("", "", msInline, "USE", childName);
						}
						else 
						{
							sax3dw.preWriteField(contVal);
							sax3dw.useDecl(msInline, childName, "containerField", contVal);
						}
					}
				}
			}
		}
	}
}

//void x3dExportOrganizer::processUsedGrouping(MFnDagNode newDagFn, MString childName, MString tempString, MString contVal, MString contField)
void x3dExportOrganizer::processUsedGrouping(MObject mObj, MString childName, MString tempString, MString contVal, MString contField)
{
	MFnDagNode newDagFn(mObj);

	if(isTreeBuilding)
	{
		if(newDagFn.typeName().operator ==("lodGroup") || newDagFn.typeName().operator ==("x3dSwitch")|| newDagFn.typeName().operator ==("x3dCollision") || newDagFn.typeName().operator ==("x3dAnchor") || newDagFn.typeName().operator ==("x3dInline"))
		{
			buildUITreeNode("transform", newDagFn.name(), msTransform, "USE", childName.operator +=("Parent"));
		}else buildUITreeNode(newDagFn.typeName(), newDagFn.name(), tempString, "USE", childName);
	}
	else
	{
		if(newDagFn.typeName().operator ==("lodGroup") || newDagFn.typeName().operator ==("x3dSwitch")|| newDagFn.typeName().operator ==("x3dCollision")|| newDagFn.typeName().operator ==("x3dAnchor") || newDagFn.typeName().operator ==("x3dInline"))
		{
			tempString.set(msTransform);
			childName.operator +=("Parent");
		}
		cout << "ContainerField Issues: " << contVal << endl;
		sax3dw.preWriteField(contVal);
		sax3dw.useDecl(tempString,childName,contField,contVal);
	}
}

void x3dExportOrganizer::writeHumanoidRootNode(bool open, MString humanName)// temporary solution
{
	MString jName(humanName);
	jName.operator +=("_HumanoidRoot");
	MString jaName("\"");
	jaName.operator +=(jName);
	jaName.operator +=("\"");
	if(isTreeBuilding == false)
	{
		if(open == true)
		{
			MStringArray fnames;
			MStringArray fvalues;
			fnames.append("name");
			fnames.append("center");
			fnames.append("containerField");
			fvalues.append(jaName);
			fvalues.append("0 -0.824 -0.277");
			fvalues.append("skeleton");
			sax3dw.startNode("HAnimJoint", jName, fnames, fvalues, true);
			sax3dw.preWriteField("children");
			sax3dw.writeSBracket();
		} else {
			sax3dw.writeEBracket();
			sax3dw.endNode("HAnimJoint", jName);
		}
	}
	else buildUITreeNode("transform", humanName, "HAnimJoint", "DEF", jName);
}

//MStatus x3dExportOrganizer::writeHeadlessHAnimHumanoid(MFnDagNode newDag)
MStatus x3dExportOrganizer::writeHeadlessHAnimHumanoid(MObject mObj)
{
	MFnDagNode newDag(mObj);

	/*
	double skLoc[3] = {0, 0, 0};
	MStringArray hnoid1;
	MStringArray hnoid2;

	hnoid1.append("containerField");
	hnoid2.append("");

	MString avatarName("humanoid_");
	avatarName.operator +=(newDag.name());

	MString aName(avatarName);
		bool getVal = true;
		getVal = sax3dw.checkIfHasBeen(aName);
		if(getVal == false)
		{
			sax3dw.setAsHasBeen(aName);
		}

	MStatus status;

	MObject rObj = newDag.parent(0);
	MFnDagNode rDag(rObj);
	MString pn = rDag.name();

	if(isTreeBuilding)
	{
		if(pn.operator ==("world"))
		{
			buildUITreeNode("joint", newDag.name(), msHAnimHumanoid, "DEF", aName);
			treeTabs = treeTabs+5;
				buildHAnimHumanoidBody(newDag, aName);//discontinued function
			treeTabs = treeTabs-5;
		}
		else
		{
			MStringArray skinCoordArray;
			MFnSkinCluster sc;
		}
	}
	else
	{
		if(pn.operator ==("world"))
		{
			sax3dw.startNode(msHAnimHumanoid, aName, hnoid1, hnoid2, true);
				buildHAnimHumanoidBody(newDag, aName);// discontinued function
			sax3dw.endNode(msHAnimHumanoid, aName);
		}
	}
	*/
	return MStatus::kSuccess;
}

//void x3dExportOrganizer::getSkinClusters(MFnDagNode jdag, MObjectArray &scObjs)
void x3dExportOrganizer::getSkinClusters(MObject mObj, MObjectArray &scObjs)
{
	MFnDagNode jdag(mObj);

	if(jdag.typeName().operator == ("joint"))
	{
//		cout << "---------" << endl;
//		cout << "New Joint" << endl;
//		cout << "---------" << endl;
		MPlug aPlug = jdag.findPlug("lockInfluenceWeights");

		MPlugArray plugSet;
		aPlug.connectedTo(plugSet, false, true);

		unsigned int i;
		for(i=0; i<plugSet.length(); i++)
		{
			bool isThere = false;
			unsigned int e;
			for(e=0;e<scObjs.length();e++)
			{
				MFnDependencyNode tNode(scObjs.operator [](e));
				MFnDependencyNode aNode(plugSet.operator [](i).node());
				if(tNode.name().operator ==(aNode.name()))
				{
//					cout << "We Equal - " << "SCNode: " << tNode.name().asChar() << ", " << "PLNode: " << aNode.name().asChar() << endl; 
					isThere = true;
				}else
				{
//					cout << "We Don't Equal - " << "SCNode: " << tNode.name().asChar() << ", " << "PLNode: " << aNode.name().asChar() << endl; 
				}
			}
			if(!isThere) scObjs.append(plugSet.operator [](i).node());
		}

		for(i=0; i<jdag.childCount(); i++)
		{
			MObject cobj = jdag.child(i);
			MFnDagNode newDag(cobj);
			getSkinClusters(newDag.object(), scObjs);
		}
	}
}

//void	x3dExportOrganizer::buildHAnimHumanoidBody(MFnDagNode newDag, MString pName)
//void	x3dExportOrganizer::buildHAnimHumanoidBody(MFnDagNode pDag)
void	x3dExportOrganizer::buildHAnimHumanoidBody(MObject mObj)
{
	MFnDagNode pDag(mObj);
	MObject obj = pDag.child(0);
	MFnDagNode newDag(obj);
	MString pName = pDag.name();

	double skLoc[3] = {0, 0, 0};
//	double pVal[] = {0, -0.824, -0.277};
	double pVal[] = {0, 0, 0};
	MString pNameCoord(pName);
	pNameCoord.operator +=("_Coords");

	MString pNameNorm(pName);
	pNameNorm.operator +=("_Norms");
/*
	MString grName("hanim_");
	grName.operator +=(newDag.name());
	MFnDependencyNode ghostDep = web3dem.getMyDepNode(grName);

	MFnDagNode skinDag = newDag;

	if(ghostDep.name().operator ==(grName))
	{
		MObject gObj = ghostDep.object();
		MDagPath gPath;
		MDagPath::getAPathTo(gObj, gPath);
		MObject gObj2 = gPath.node();
		MDagPath::getAPathTo(gObj2, gPath);
		MFnDagNode gNode(gPath);
//		skinDag.setObject(gNode.object());
	}
*/
	//----------------------
	MObjectArray scObjs;
	getSkinClusters(newDag.object(), scObjs);
	//----------------------
	cout << "MObjectArray Length: " << scObjs.length() << endl;

//	MPlug aPlug = newDag.findPlug("lockInfluenceWeights");

//	MPlugArray plugSet;
//	aPlug.connectedTo(plugSet, false, true);

//	MFnSkinCluster sc;

//	if(plugSet.length() > 0)
//	{
//		MObject pobj = plugSet.operator [](0).node();

//		sc.setObject(pobj);
//	}
	if(isTreeBuilding)
	{
		if(scObjs.length() > 0) buildUITreeNode("", "", msCoordinate, "DEF", pNameCoord);
		if(scObjs.length() > 0 && npvNonD == 1) buildUITreeNode("", "", msNormal, "DEF", pNameNorm);

		MStringArray skinCoordArray;
		MFloatVectorArray compNormArray;
		//traverseSkeleton(newDag, pName, sc, "", skLoc, pVal);
//		gatherMeshData(sc, skinCoordArray, compNormArray, pName);
		gatherMeshData(scObjs, skinCoordArray, compNormArray, pName);
	}
	else
	{
		MStringArray skinCoordArray;
		MStringArray skinNormArray;
		MFloatVectorArray compNormArray;

		MString coords;
		MString normals;
		if(scObjs.length()>0)
		{
			skinCoordArray = getSkinCoords(scObjs);
//			skinCoordArray = getSkinCoords(sc);
			coords = extractCoordinates(skinCoordArray);

			compNormArray = getTempSkinNormFloats(scObjs);
//			compNormArray = getTempSkinNormFloats(sc);
			skinNormArray = getSkinNorms(compNormArray);
			normals = extractNormals(skinNormArray);//cawNormalNode
//			normals  = web3dem.postProcessVectorArray(skinNormArray);
		}

		MStringArray pCoord1;
		MStringArray pCoord2;
		MStringArray pNorm1;
		MStringArray pNorm2;

		pCoord1.append("point");
		pCoord1.append("containerField");
		pCoord2.append(coords);
		pCoord2.append("skinCoord");

		pNorm1.append("vector");
		pNorm1.append("containerField");
		pNorm2.append(normals);
		pNorm2.append("skinNormal");

		if(scObjs.length() > 0)
		{
			sax3dw.startNode(msCoordinate, pNameCoord, pCoord1, pCoord2, false);

			if(npvNonD == 1)
			{
				sax3dw.startNode(msNormal, pNameNorm, pNorm1, pNorm2, false);
			}
		}
		MObjectArray crj = getCharacterRootJoints(pDag.object());
		writeHumanoidRootNode(true, pName);
			unsigned int i;
			for(i=0; i< crj.length();i++)
			{
				MFnDagNode jDag(crj.operator[](i));
				traverseSkeleton(jDag.object(), pName, scObjs, "children", skLoc, pVal);
			}
			//Commented out due to multi-root rig
			//traverseSkeleton(newDag, pName, scObjs, "children", skLoc, pVal);
		writeHumanoidRootNode(false, pName);
		MFloatVectorArray newNArray;
//		if(plugSet.length() > 0) gatherMeshData(sc, skinCoordArray, newNArray, pName);
		if(scObjs.length() > 0) gatherMeshData(scObjs, skinCoordArray, newNArray, pName);
	}
}

//MObjectArray x3dExportOrganizer::getCharacterRootJoints(MFnDagNode pDag)
MObjectArray x3dExportOrganizer::getCharacterRootJoints(MObject mObj)
{
	MFnDagNode pDag(mObj);
	unsigned int newNum = pDag.childCount();
	MObjectArray crj;
	unsigned int i;
	for(i=0;i<newNum;i++)
	{
		MObject obj = pDag.child(i);
		MFnDagNode tNode(obj);
		MString nType = tNode.typeName();
		MPlug ioPlug = tNode.findPlug("intermediateObject");
		bool ioBool = false;
		ioPlug.getValue(ioBool);
		if(nType.operator ==(X3D_HANIMJOINT) && ioBool == false) crj.append(obj);
	}
	return crj;
}

//void	x3dExportOrganizer::gatherMeshData(MFnSkinCluster sc, MStringArray sca, MFloatVectorArray cna, MString pName)
void	x3dExportOrganizer::gatherMeshData(MObjectArray scObjs, MStringArray sca, MFloatVectorArray cna, MString pName)
{//ericeric
	unsigned int ncon = 0;
	unsigned int d;
	for(d=0;d<scObjs.length();d++)
	{
		MFnSkinCluster aSkin(scObjs.operator [](d));
		unsigned int dnoc = aSkin.numOutputConnections();
		ncon = ncon+dnoc;
	}
//	unsigned int noc = sc.numOutputConnections();
//	unsigned int q;

//	if(noc > 0 && isTreeBuilding == false)
	if(ncon > 0 && isTreeBuilding == false)
	{
		sax3dw.preWriteField("skin");
		sax3dw.writeSBracket();
	}

	unsigned int e;
	for(e=0;e<scObjs.length();e++)
	{
		MFnSkinCluster sc(scObjs.operator [](e));
		unsigned int noc = sc.numOutputConnections();
		unsigned int q;
		for(q=0; q<noc; q++)
		{
			sax3dw.setHasMultiple(true);
			MDagPath skinPath;
			sc.getPathAtIndex(q,skinPath);
			//MFnMesh mesh(skinPath.node());
			MFnMesh mesh_a(skinPath.node());
			
			MPlug x3dSkinOut = mesh_a.findPlug("x3dSkinOut");
			MPlugArray xso;
			x3dSkinOut.connectedTo(xso, false, true);
			MDagPath xsoPath;
			MDagPath::getAPathTo(xso.operator[](0).node(), xsoPath);
			MFnMesh mesh(xsoPath);
/*
			MFnMesh mesh;
			MFnDagNode showMesh(skinPath.node());
			MFnDagNode pNode(showMesh.parent(0));

			unsigned int parch;
			for(parch=0; parch<pNode.childCount();parch++)
			{
				MString checkName("");
				checkName.operator +=(showMesh.name());
				checkName.operator +=("Orig");
				MFnDagNode acNode(pNode.child(parch));
				if(acNode.name().operator ==(checkName)) mesh.setObject(pNode.child(parch));
			}
			*/
			/*
			MFnMesh skinMesh(skinPath.node());

			MItDependencyGraph mdGraph(skinMesh.object(), MFn::kTweak, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kPlugLevel);
			MFnDependencyNode tkNode;
			bool isLooking = true;
			while(!mdGraph.isDone() && isLooking == true)
			{
				MObject cObj = mdGraph.thisNode();
				MFnDependencyNode cNode(cObj);
				if(cNode.typeName().operator ==("tweak"))
				{
					tkNode.setObject(cNode.object());
					isLooking = false;
				}
				mdGraph.next();
			}
		
			MFnMesh mesh;

			if(tkNode.name().operator !=(""))
			{
				MItDependencyGraph meshGraph(tkNode.object(), MFn::kMesh, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kPlugLevel);

				isLooking = true;
				while(!meshGraph.isDone() && isLooking == true)
				{
					MDagPath aPath = MDagPath::getAPathTo(meshGraph.thisNode());
					MFnDagNode aDagNode(aPath);
					MDagPath aPath2 = aDagNode.dagPath();
					MFnDagNode aDagNode2(aPath2);

					if(aDagNode2.typeName().operator ==("mesh"))
					{
						MPlug aPlug = aDagNode2.findPlug("intermediateObject");
						bool isIO = false;
						aPlug.getValue(isIO);
						if(isIO == true)
						{
							MFnMesh nMesh(aDagNode2.dagPath());
							mesh.setObject(nMesh.object());
							isLooking = false;
						}
					}
					meshGraph.next();
				}
			}
			else mesh.setObject(skinMesh.object());
	*/
			MString supMeshName = mesh.name();
			MStringArray shArray1;
			MStringArray shArray2;
			shArray1.clear();
			shArray2.clear();

		//Get sets
			MObjectArray shaders;
			MObjectArray groups;
			mesh.getConnectedSetsAndMembers(0, shaders, groups, true);

		//Check for Metadata
			bool hasMetadata = checkForMetadata(supMeshName);
			MString metadataName;
			MPlug aPlug;

			if(isTreeBuilding)//blarp
			{
					if(groups.length() == 1)
					{
						bool hasBeen = sax3dw.checkIfHasBeen(supMeshName);
						if(hasBeen == false)
						{
							sax3dw.setAsHasBeen(supMeshName);
							buildUITreeNode("mesh", supMeshName, msShape, "DEF", supMeshName);
							treeTabs = treeTabs + 1;
							if(ttabsMax < treeTabs) ttabsMax = treeTabs;
								if(hasMetadata) addMetadataTag(supMeshName);
								setUpAppearance(shaders.operator [](0), skinPath);
								setUpHAnimGeometry(skinPath, 0, sca, cna, pName);//(mesh, groups, nodeType, 0);
							treeTabs = treeTabs - 1;
						}
						else buildUITreeNode("mesh", supMeshName, msShape, "USE", supMeshName);
					}
					else
					{
						bool hasBeen = sax3dw.checkIfHasBeen(supMeshName);
						if(hasBeen == false)
						{
							sax3dw.setAsHasBeen(supMeshName);
							buildUITreeNode("mesh", supMeshName, msGroup, "DEF", supMeshName);
							treeTabs = treeTabs + 1;
							if(ttabsMax < treeTabs) ttabsMax = treeTabs;
							if(hasMetadata) addMetadataTag(supMeshName);

							unsigned int i;
							for(i=0; i<groups.length(); i++)
							{
								if(groups.operator [](i).apiType()!= MFn::kInvalid)
								{
									MString endVal;
									endVal.set(i);
									MString rawKeeShape(supMeshName);
									rawKeeShape.operator +=("_rks_");
									rawKeeShape.operator +=(endVal);

									buildUITreeNode("mesh", supMeshName, msShape, "DEF", rawKeeShape);
									treeTabs = treeTabs + 1;
									if(ttabsMax < treeTabs) ttabsMax = treeTabs;
										setUpAppearance(shaders.operator [](i), skinPath);
										setUpHAnimGeometry(skinPath, i, sca, cna, pName);//(mesh, groups, nodeType, i);
									treeTabs = treeTabs - 1;
								}
							}
							treeTabs = treeTabs - 1;
						}
						else buildUITreeNode("mesh", supMeshName, msGroup, "USE", supMeshName);
					}

			}
			else
			{
				shArray1.append(MString("containerField"));
				shArray2.append("skin");

				MString nodeType;

					if(groups.length() == 1)
					{
						bool hasBeen = sax3dw.checkIfHasBeen(supMeshName);
						if(hasBeen == false)
						{
							sax3dw.setAsHasBeen(supMeshName);
							sax3dw.startNode(msShape, supMeshName, shArray1, shArray2, true);
							if(hasMetadata) addMetadataTag(supMeshName);
							setUpAppearance(shaders.operator [](0), skinPath);
							setUpHAnimGeometry(skinPath, 0, sca, cna, pName);//(mesh, groups, nodeType, 0);
							sax3dw.endNode(msShape, supMeshName);
						}
						else
						{
							sax3dw.useDecl(msShape, supMeshName, "containerField", "skin");
						}
					}
					else
					{
						bool hasBeen = sax3dw.checkIfHasBeen(supMeshName);
						if(hasBeen == false)
						{
							sax3dw.setAsHasBeen(supMeshName);
							sax3dw.startNode(msGroup, supMeshName, shArray1, shArray2, true);
							shArray2.operator [](0) = getCFValue(4);
							if(hasMetadata) addMetadataTag(supMeshName);
							unsigned int i;
							for(i=0; i<groups.length(); i++)
							{
								if(groups.operator [](i).apiType()!= MFn::kInvalid)
								{
									MString endVal;
									endVal.set(i);
									MString rawKeeShape(supMeshName);
									rawKeeShape.operator +=("_rks_");
									rawKeeShape.operator +=(endVal);
										sax3dw.startNode(msShape, rawKeeShape, shArray1, shArray2, true);
										setUpAppearance(shaders.operator [](i), skinPath);
										setUpHAnimGeometry(skinPath, i, sca, cna, pName);//(mesh, groups, nodeType, i);
										sax3dw.endNode(msShape, rawKeeShape);
								}
							}
							sax3dw.endNode(msGroup, supMeshName);
						}
						else
						{
							sax3dw.preWriteField("skin");
							sax3dw.useDecl(msGroup, supMeshName, "containerField", "skin");
						}
					}

			}
		}
	}
//	if(noc > 0 && isTreeBuilding == false) sax3dw.writeEBracket();
	if(ncon > 0 && isTreeBuilding == false) sax3dw.writeEBracket();

}

MString x3dExportOrganizer::extractCoordinates(MStringArray coordArray)
{
	MString value;
	if(exEncoding == X3DVENC) value.operator +=("[ ");
	unsigned int i;
	for(i=0;i<coordArray.length();i++)
	{
        MStringArray chop;
		coordArray.operator [](i).split('*',chop);
		value.operator +=(chop.operator [](1));
		if(i<coordArray.length()-1) value.operator +=(",\n");
	}
	if(exEncoding == X3DVENC) value.operator +=(" ]");

	return value;
}

MString x3dExportOrganizer::extractNormals(MStringArray normArray)
{
	MString value;
	if(exEncoding == X3DVENC) value.operator +=("[ ");
	if(npvNonD == 1)
	{
		unsigned int i;
		for(i=0;i<normArray.length();i++)
		{
			value.operator +=(normArray.operator [](i));
			if(i<normArray.length()-1) value.operator +=(",\n");
		}
	}
	if(exEncoding == X3DVENC) value.operator +=(" ]");
	return value;
}

//MStringArray x3dExportOrganizer::getSkinCoords(MFnSkinCluster sc)
MStringArray x3dExportOrganizer::getSkinCoords(MObjectArray scObjs)
{
	MStringArray skinCoords;
	unsigned int d;
	for(d=0;d<scObjs.length();d++)
	{
		MFnSkinCluster sc(scObjs.operator [](d));
		MObjectArray moa;
		sc.getOutputGeometry(moa);

		unsigned int q;
		for(q=0;q<moa.length();q++)
		{
			MFnDagNode dNode(moa.operator [](q));
			MString mName = dNode.name();

//		cout << "Found a Geometry: " << mName << endl; 
			MDagPath dPath;
			dNode.getPath(dPath);

			MFnMesh mesh(dPath.node());

			MFloatPointArray coordValues;
			mesh.getPoints(coordValues, MSpace::kObject);

	//		cout << "Got Mesh Points" << endl;
			unsigned int i;
			for(i=0; i<coordValues.length(); i++)
			{
				MFloatPoint tp = coordValues.operator [](i);
				MString nci(mName);
				nci.operator +=("*");
				nci.operator +=(tp[0]);
				nci.operator +=(" ");
				nci.operator +=(tp[1]);
				nci.operator +=(" ");
				nci.operator +=(tp[2]);
				nci.operator +=("*");

				MString li;
				li.set(i);
				nci.operator +=(li);
				nci.operator +=("*");

				MString hai;
				hai.set(skinCoords.length());
				nci.operator +=(hai);

				skinCoords.append(nci);

			}
		}
	}
	return skinCoords;
}

//MFloatVectorArray x3dExportOrganizer::getTempSkinNormFloats(MFnSkinCluster sc)
MFloatVectorArray x3dExportOrganizer::getTempSkinNormFloats(MObjectArray scObjs)
{
	MFloatVectorArray finalArray;
	unsigned int d;
	for(d=0;d<scObjs.length();d++)
	{
		MFnSkinCluster sc(scObjs.operator [](d));
		MObjectArray moa;
		sc.getOutputGeometry(moa);

		unsigned int q;
		for(q=0;q<moa.length();q++)
		{

			MFnDagNode dNode(moa.operator [](q));
			MString mName = dNode.name();
			MDagPath dPath;
			dNode.getPath(dPath);

			MFnMesh mesh(dPath.node());

			MPointArray pta;
			mesh.getPoints(pta, MSpace::kObject);

			MFloatVectorArray normalValues;//9990009991
			mesh.getNormals(normalValues, MSpace::kObject);
			finalArray = web3dem.getComparedFloatVectorArray(normalValues);
	
//	MString catStr = postProcessVectorArray(compareVal);

//			unsigned int i;
//			for(i=0;i<normalValues.length();i++)
//			{
//				finalArray.append(normalValues.operator [](i));
//			}
		}
	}
	return finalArray;
}

MFloatVectorArray x3dExportOrganizer::addUniqueFloatVectors(MFloatVectorArray newArray, MFloatVectorArray finalArray)
{
	MFloatVectorArray tempArray;
	unsigned int i;
	for(i=0;i<newArray.length();i++)
	{
		bool isThere = false;
		unsigned int j;
		for(j=0;j<finalArray.length();j++)
		{
			if(newArray.operator [](i).operator ==(finalArray.operator [](j))) isThere = true;
		}
		if(isThere == false) finalArray.append(newArray.operator [](i));
	}
	return tempArray;
}

MStringArray x3dExportOrganizer::getSkinNorms(MFloatVectorArray finalArray)//101010
{
	MStringArray skinNorms;

	unsigned int i;
	for(i=0; i<finalArray.length(); i++)
	{
		MFloatVector vp = finalArray.operator [](i);
		MString nni;
		nni.operator +=(vp[0]);
		nni.operator +=(" ");
		nni.operator +=(vp[1]);
		nni.operator +=(" ");
		nni.operator +=(vp[2]);

		skinNorms.append(nni);
	}
	return skinNorms;
}

bool x3dExportOrganizer::getMeshDagPath(MString mName, MDagPath dPath)
{
	bool aValue = false;
	unsigned int i = 0;
	unsigned int j = avatarMeshNames.length();
	while(aValue == false && i < j)
	{
		if(mName.operator ==(avatarMeshNames.operator [](i)))
		{
			dPath = avatarDagPaths.operator [](i);

			MFnMesh mesh(dPath);
			bool isInter = mesh.isIntermediateObject();
			if(!isInter) aValue = true;
			else i = j;
		}
		i=i + 1;
	}
	return aValue;
}

bool x3dExportOrganizer::checkSArray(MStringArray against, MString check)
{
	bool aValue = false;
	unsigned int i = 0;
	unsigned int j = against.length();
	while(aValue == false && i < j)
	{
		if(check.operator ==(against.operator [](i)))
		{
			aValue = true;
		}
		i=i + 1;
	}
	return aValue;
}

//void	x3dExportOrganizer::writeHAnimJointForTree(MFnDagNode newDag)
void	x3dExportOrganizer::writeHAnimJointForTree(MObject mObj)
{
	MFnDagNode newDag(mObj);
	MDagPath cnDag = MDagPath::getAPathTo(newDag.object());
	MString pName("");
	bool jf = true;
	while(jf)
	{
		MFnDagNode tDag(cnDag);
		MObject po = tDag.parent(0);
		MFnDagNode pDag(po);
		if(pDag.typeName().operator !=("joint"))
		{
			pName.operator =(pDag.name());
			jf = false;
		}else cnDag = MDagPath::getAPathTo(pDag.object());
	}

	MString newDagName(pName);
	newDagName.operator +=("_x_");
	newDagName.operator +=(newDag.name());
	buildUITreeNode("joint", newDag.name(), msHAnimJoint, "DEF", newDagName);
}

//void	x3dExportOrganizer::traverseSkeleton(MFnDagNode newDag, MString pName, MFnSkinCluster sc, MString cfString, double pos[], double pVal[])
//void	x3dExportOrganizer::traverseSkeleton(MFnDagNode newDag, MString pName, MObjectArray scObjs, MString cfString, double pos[], double pVal[])
void	x3dExportOrganizer::traverseSkeleton(MObject mObj, MString pName, MObjectArray scObjs, MString cfString, double pos[], double pVal[])
{
	MFnDagNode newDag(mObj);

	double *newPVal = NULL;
	newPVal = new double[3];
	newPVal[0] = 0;
	newPVal[1] = 0;
	newPVal[2] = 0;

	MString pgString("hanim_");
	pgString.operator +=(newDag.name());

	MString newDagName(pName);
	if(nonStandardHAnim)
	{
		newDagName.operator +=("_x_");
		newDagName.operator +=(newDag.name());
	}
	else newDagName.operator =(newDag.name());


//	MFnDependencyNode pGNode = web3dem.getMyDepNode(pgString);
	MFnDependencyNode pGNode(web3dem.getMyDepNodeObj(pgString));
	if(pGNode.name().operator ==(pgString))
	{
		MPlug aPlug;
		aPlug = pGNode.findPlug("translate");
	/*
		aPlug = newDag.findPlug("translate");
	*/
		unsigned int i;
		float *cFloat = NULL;
		cFloat = new float[3];
		for(i=0;i<3;i++)
		{
			MPlug tPlug = aPlug.child(i);
			tPlug.getValue(cFloat[i]);
			newPVal[i] = pVal[i] + cFloat[i];
		}

		delete [] cFloat;
	}
//	newPVal[0] = 0;
//	newPVal[1] = 0;
//	newPVal[2] = 0;

	bool hasMetadata = checkForMetadata(newDag.name());

	if(newDag.typeName().operator ==("joint"))//888uuu888
	{
		if(isTreeBuilding)
		{
			buildUITreeNode(newDag.typeName(), newDag.name(), msHAnimJoint, "DEF", newDagName);
			if(hasMetadata)
			{
				treeTabs = treeTabs + 1;
				addMetadataTag(newDag.name());
				treeTabs = treeTabs - 1;
			}

			unsigned int k;
			for(k=0;k<newDag.childCount();k++)
			{
				MObject kobj = newDag.child(k);
				MFnDagNode aNode(kobj);
				treeTabs = treeTabs + 1;
//				traverseSkeleton(aNode, pName, sc, "children", pos, newPVal);
				traverseSkeleton(aNode.object(), pName, scObjs, "children", pos, newPVal);
				treeTabs = treeTabs - 1;
			}
		}
		else
		{
//			cout << " " << endl;
//			cout << " " << endl;

			MDagPath ndPath;
			newDag.getPath(ndPath);

			unsigned int ncon = 0;
			unsigned int d;
			for(d=0;d<scObjs.length();d++)
			{
				MFnSkinCluster aSkin(scObjs.operator [](d));
				unsigned int dnoc = aSkin.numOutputConnections();
				ncon = ncon+dnoc;
			}

//			MStatus status;
//			unsigned int noc = sc.numOutputConnections();
			MStringArray jArray1;
			MStringArray jArray2;

			MFnIkJoint thisJoint(newDag.object());

			jArray1 = web3dem.getJointFields();
//			jArray2 = web3dem.getJointFieldValues(newDag, 0, pName, pVal);
			jArray2 = web3dem.getJointFieldValues(thisJoint.object(), 0, pName, pVal);

//			TemporaryChange Dec 6, 2005
//			jArray2.operator [](0) = jArray2.operator [](4);
//			jArray2.operator [](4) = "";
			jArray2.operator [](1) = jArray2.operator [](5);
			jArray2.operator [](5) = "";

//			if(noc > 0)
			if(ncon > 0)//aaronaaron
			{
				MFloatArray wCollect;
				MFloatArray weights;
				unsigned int e;
				for(e=0;e<scObjs.length();e++)
				{
					MFnSkinCluster sc(scObjs.operator [](e));
					MStatus status;
					unsigned int noc = sc.numOutputConnections();//aaronaaron

					unsigned int jdp = sc.indexForInfluenceObject(ndPath, &status);

					MObjectArray moa;
					MDagPathArray infs;

					unsigned int ifo = sc.influenceObjects(infs, &status);
					unsigned int i;

//					MFloatArray wCollect;
//					MFloatArray weights;

					for(i=0; i<noc; ++i)
					{
						unsigned int index;
						index = sc.indexForOutputConnection(i);
						MDagPath skinPath;
						sc.getPathAtIndex(i,skinPath);
						MItGeometry gIter(skinPath);


						while(!gIter.isDone())
						{
							MObject comp = gIter.component();
							MFloatArray wts;
							unsigned int infCount;

							sc.getWeights(skinPath, comp, wts, infCount);
							
							wCollect.append(wts.operator [](jdp));

							gIter.next();
						}
					}
				}

				unsigned int l;
				unsigned int m = 0;

				MString indexList;
				MString weightList;

				for(l=0;l<wCollect.length();l++)
				{
					if(wCollect.operator [](l) > 0)
					{
						MString tw;
						tw.set(wCollect.operator [](l));

						MString ti;
						ti.set(l);

						if(m = 5)
						{
							tw.operator +=("\n");
							ti.operator +=("\n");
							m = 0;
						}
						else
						{
							tw.operator +=(" ");
							ti.operator +=(" ");
							m = m + 1;
						}
						weightList.operator +=(tw);
						indexList.operator +=(ti);
					}
				}

				MStringArray wlArray;
				MStringArray ilArray;

				weightList.split(' ', wlArray);
				indexList.split(' ', ilArray);

				weightList.set("");
				for(l=0;l<wlArray.length();l++)
				{
					weightList.operator +=(wlArray.operator [](l));
					if(l!= wlArray.length()-1) weightList.operator +=(" ");
				}

				indexList.set("");
				for(l=0;l<ilArray.length();l++)
				{
					indexList.operator +=(ilArray.operator [](l));
					if(l!= ilArray.length()-1) indexList.operator +=(" ");
				}

				MStringArray wlcArray;
				MStringArray ilcArray;

				MStringArray wlSplice;
				MStringArray ilSplice;

//				weightList.split('\n', wlArray);
//				indexList.split('\n', ilArray);
				weightList.split('\n', wlSplice);
				indexList.split('\n', ilSplice);
				for(l=0;l<wlSplice.length();l++)
				{
					float cFloat = wlSplice.operator [](l).asFloat();
					if( cFloat > 0 && cFloat <= 1)
					{
						wlcArray.append(wlSplice.operator [](l));
						ilcArray.append(ilSplice.operator [](l));
					}
				}

				MString wcList("");
//				weightList.set("");
				if(exEncoding == X3DVENC) wcList.operator +=(" [ ");
				for(l=0;l<wlcArray.length();l++)
				{
					wcList.operator +=(wlcArray.operator [](l));
					if(l!= wlcArray.length()-1) wcList.operator +=("\n");
				}
				if(exEncoding == X3DVENC) wcList.operator +=(" ]");
//				cout << endl;
//				cout << thisJoint.name().asChar() << endl;
//				cout << "WL - Array: " << wlArray.length() << endl;

				MString icList("");
//				indexList.set("");
				if(exEncoding == X3DVENC) icList.operator +=(" [ ");
				for(l=0;l<ilcArray.length();l++)
				{
					icList.operator +=(ilcArray.operator [](l));
					if(l!= ilcArray.length()-1) icList.operator +=("\n");
				}
				if(exEncoding == X3DVENC) icList.operator +=(" ]");

//				cout << "IL - Array: " << ilArray.length() << endl;

				jArray1.append("skinCoordIndex");
				jArray2.append(icList);

				jArray1.append("skinCoordWeight");
				jArray2.append(wcList);
			}
			jArray1.append("containerField");
			jArray2.append(cfString);

			if(cfString.operator !=("skeleton"))
			{
//				sax3dw.preWriteField(cfString);
				sax3dw.setHasMultiple(true);
			}

				sax3dw.startNode(msHAnimJoint, newDagName, jArray1, jArray2, true);
				if(hasMetadata) addMetadataTag(newDag.name());
				if(newDag.childCount() > 0)//888iii888
				{
					unsigned int k;
					sax3dw.preWriteField("children");
					sax3dw.writeSBracket();
					for(k=0;k<newDag.childCount();k++)
					{
						MObject kobj = newDag.child(k);
						MFnDagNode aNode(kobj);

						MString gName("hanim_");
						gName.operator +=(newDag.name());

						double px = 0;
						double py = 0;
						double pz = 0;

//						MFnDependencyNode ghostNode = web3dem.getMyDepNode(gName);
						MFnDependencyNode ghostNode(web3dem.getMyDepNodeObj(gName));
						if(ghostNode.name().operator ==(gName))
						{
//							MPlug posXPlug = newDag.findPlug("translateX");
//							MPlug posYPlug = newDag.findPlug("translateY");
//							MPlug posZPlug = newDag.findPlug("translateZ");
							MPlug posXPlug = ghostNode.findPlug("translateX");
							MPlug posYPlug = ghostNode.findPlug("translateY");
							MPlug posZPlug = ghostNode.findPlug("translateZ");

							posXPlug.getValue(px);
							posYPlug.getValue(py);
							posZPlug.getValue(pz);
						}

						pos[0] = pos[0] + px;
						pos[1] = pos[1] + py;
						pos[2] = pos[2] + pz;

//						traverseSkeleton(aNode, pName, sc, "children", pos, newPVal);
						traverseSkeleton(aNode.object(), pName, scObjs, "children", pos, newPVal);
					}
					sax3dw.writeEBracket();
				}
				sax3dw.endNode(msHAnimJoint, newDagName);

		}
	}
	else if(newDag.typeName().operator ==("transform"))//888ooo888
	{
		MStringArray sArray1 = web3dem.getSiteFields();
		MStringArray sArray2 = web3dem.getSiteFieldValues(newDag, 0, pName, pVal, nonStandardHAnim);
		sax3dw.setAsHasBeen(sArray2.operator [](0));
		if(isTreeBuilding)
		{
			buildUITreeNode("transform", newDag.name(), msHAnimSite, "DEF", sArray2.operator [](0));
			treeTabs = treeTabs + 1;
			if(hasMetadata) addMetadataTag(newDag.name());
			unsigned int i;
			for(i=0;i<newDag.childCount();i++)
			{
				MFnDagNode aDag(newDag.child(i));
				processChildNode(aDag.object(), 4);
			}
			treeTabs = treeTabs - 1;
		}
		else
		{

//			sArray2.operator [](1) = sArray2.operator [](5);
			sArray2.operator [](1) = "";
			sArray1.append("containerField");
			sArray2.append(cfString);
/*
						MPlug posXPlug = newDag.findPlug("translateX");
						MPlug posYPlug = newDag.findPlug("translateY");
						MPlug posZPlug = newDag.findPlug("translateZ");

						double px = 0;
						double py = 0;
						double pz = 0;

						posXPlug.getValue(px);
						posYPlug.getValue(py);
						posZPlug.getValue(pz);

						pos[0] = pos[0] + px;
						pos[1] = pos[1] + py;
						pos[2] = pos[2] + pz;

						MString newPos;
						newPos.set(pos[0]);
						newPos.operator +=(" ");
						newPos.operator +=(pos[1]);
						newPos.operator +=(" ");
						newPos.operator +=(pos[2]);
						sArray2.operator [](4) = newPos;
*/
			sax3dw.startNode(msHAnimSite, sArray2.operator [](0), sArray1, sArray2, true);
			if(hasMetadata) addMetadataTag(newDag.name());
			unsigned int i;
			for(i=0;i<newDag.childCount();i++)
			{
				MFnDagNode aDag(newDag.child(i));
				processChildNode(aDag.object(), 4);
			}
			sax3dw.endNode(msHAnimSite, newDag.name());
		}
	}

//	cout << " " << endl;
//	cout << " " << endl;
	delete [] newPVal;
}

//MStatus x3dExportOrganizer::writeHAnimHumanoid(MFnDagNode newDag, MFnDagNode pDag, unsigned int childNum, MStringArray grArray1, MStringArray grArray2)
MStatus x3dExportOrganizer::writeHAnimHumanoid(MObject mObj, MObject pObj, unsigned int childNum, MStringArray grArray1, MStringArray grArray2)
{
	MFnDagNode newDag(mObj);
	MFnDagNode pDag(pObj);

	cout << "HAnimHumanoid called" << endl;
	MStringArray hnoid1 = web3dem.getHAnimHumanoidFields();
	MStringArray hnoid2 = web3dem.getHAnimHumanoidFieldValues(pDag, 0);

	unsigned int i = grArray1.length();

	hnoid1.operator [](0).operator =(pDag.name());
	hnoid1.append("containerField");
	hnoid2.append(grArray2.operator [](i));

	bool hasBeen = sax3dw.checkIfHasBeen(pDag.name());
//	if(hasBeen == false) sax3dw.setAsHasBeen(pDag.name());

	if(isTreeBuilding)
	{
//		cout << "Finds HAnimHumanoid - isTreebuilding" << endl; 000000
		if(hasBeen == true)
		{
			buildUITreeNode(pDag.typeName(), pDag.name(), msHAnimHumanoid, "USE", pDag.name());
		}
		else
		{
			buildUITreeNode(pDag.typeName(), pDag.name(), msHAnimHumanoid, "DEF", pDag.name());
			treeTabs = treeTabs + 1;
				if(checkForMetadata(pDag.name())) addMetadataTag(pDag.name());
//				buildHAnimHumanoidBody(newDag, pDag.name());
				buildHAnimHumanoidBody(pDag.object());
			treeTabs = treeTabs - 1;
		}
	}
	else
	{
		if(exEncoding == X3DVENC)
		{
			MObject parentObj = pDag.parent(0);
			MFnDagNode parentDag(parentObj);
			unsigned int remNum = 0;
			unsigned int remNum1 = 0;
			if(parentDag.name().operator !=("")) evalForSyblings(parentDag.object(), "", remNum, remNum1);
			if(remNum == 1) sax3dw.preWriteField(grArray2.operator [](grArray2.length()-1));
		}
		if(hasBeen==true) sax3dw.useDecl(msHAnimHumanoid, pDag.name(),hnoid1.operator [](hnoid1.length()-1),hnoid2.operator [](hnoid2.length()-1));
		else
		{
//			if(exEncoding == X3DVENC) sax3dw.writeSBracket();
			sax3dw.startNode(msHAnimHumanoid, pDag.name(), hnoid1, hnoid2, true);
				if(checkForMetadata(pDag.name())) addMetadataTag(pDag.name());
//				buildHAnimHumanoidBody(newDag, pDag.name());
				buildHAnimHumanoidBody(pDag.object());
			sax3dw.endNode(msHAnimHumanoid, pDag.name());
		}
	}
	return MStatus::kSuccess;
}

//MStatus x3dExportOrganizer::writeCollidableShape(MFnDagNode newDag, MFnDagNode pDag, MFnDagNode rbDag, MString cfVal)
MStatus x3dExportOrganizer::writeCollidableShape(MObject mObj, MObject pObj, MObject rbObj, MString cfVal)
{
	MFnDagNode newDag(mObj);
	MFnDagNode pDag(pObj);
	MFnDagNode rbDag(rbObj);

	MString csName = pDag.name();
	bool hMeta = checkForMetadata(csName);
	bool hasBeen = sax3dw.checkIfHasBeen(csName);
	MStringArray colArr1;
	MStringArray colArr2;
	if(!isTreeBuilding)
	{
		if(hasBeen)
		{
			sax3dw.useDecl(msColShape, csName, "containerField", cfVal);
		}
		else
		{
			sax3dw.setAsHasBeen(csName);
			MStringArray tvalues = web3dem.getX3DCollidableShapeValues(pDag, 0);
			colArr1.append("center");
			colArr1.append("rotation");
			colArr1.append("translation");
			colArr1.append(MString("containerField"));
			colArr2.append(tvalues.operator [](0));
			colArr2.append(tvalues.operator [](1));
			colArr2.append(tvalues.operator [](2));
			colArr2.append(cfVal);
			
			sax3dw.startNode(msColShape, csName, colArr1, colArr2, true);
				addMetadataTag(csName);
				writeMeshShape(newDag.object(), "shape");
			sax3dw.endNode(msColShape, csName);
		}
	}
	else
	{
		if(hasBeen) buildUITreeNode("transform", csName, msColShape, "USE", csName);
		else
		{
			sax3dw.setAsHasBeen(csName);
			buildUITreeNode("transform", csName, msColShape, "DEF", csName);
			addMetadataTag(csName);
			writeMeshShape(newDag.object(), "shape");
		}
	}
	return MStatus::kSuccess;
}

//MStatus x3dExportOrganizer::writeMeshShape(MFnDagNode dagFn, MString cfVal)
MStatus x3dExportOrganizer::writeMeshShape(MObject mObj, MString cfVal)
{
	MFnDagNode dagFn(mObj);
	MDagPath dagpath;
	dagFn.getPath(dagpath);

	MFnMesh mesh(dagpath.node());
	MString supMeshName = mesh.name();
	MStringArray shArray1;
	MStringArray shArray2;
	shArray1.clear();
	shArray2.clear();

	//Get sets
	MObjectArray shaders;
	MObjectArray groups;
	mesh.getConnectedSetsAndMembers(0, shaders, groups, true);

	//Check for Metadata
	bool hasMetadata = checkForMetadata(supMeshName);
	MString metadataName;
	MPlug aPlug;

	if(isTreeBuilding)//blarp
	{
		MString nodeType;
		bool hasDefined = false;

		MString geoname;
		MString gur("getUnderworldRelatives ");
		gur.operator +=(dagFn.name());
		MGlobal::executeCommand(gur, geoname);

		MFnDagNode cDagFn;
		if(geoname != "")
		{
//			MFnDependencyNode aDep = web3dem.getMyDepNode(geoname);
			MFnDependencyNode aDep(web3dem.getMyDepNodeObj(geoname));
			cDagFn.setObject(aDep.object());
			if(cDagFn.typeName() == "x3dIndexedFaceSet" || cDagFn.typeName() == "x3dSphere" || cDagFn.typeName() == "x3dBox" || cDagFn.typeName() == "x3dCone" || cDagFn.typeName() == "x3dCylinder")
			{
				nodeType = cDagFn.typeName();
				hasDefined = true;
			}

		}
		if(!hasDefined) nodeType.set("x3dIndexedFaceSet");

		if(hasDefined == true && nodeType != "x3dIndexedFaceSet")
		{
			bool hasBeen = sax3dw.checkIfHasBeen(supMeshName);
			if(hasBeen == false)
			{
				sax3dw.setAsHasBeen(supMeshName);
				buildUITreeNode("mesh", supMeshName, msShape, "DEF", supMeshName);
				treeTabs = treeTabs + 1;
				if(ttabsMax < treeTabs) ttabsMax = treeTabs;
					if(hasMetadata) addMetadataTag(supMeshName);
					setUpAppearance(shaders.operator [](0), dagpath);
					if(nodeType != "x3dIndexedFaceSet")	writePrimative(cDagFn.object());
				treeTabs = treeTabs - 1;
			}
			else buildUITreeNode("mesh", supMeshName, msShape, "USE", supMeshName);
		}
		else
		{
			if(groups.length() == 1)
			{
				bool hasBeen = sax3dw.checkIfHasBeen(supMeshName);
				if(hasBeen == false)
				{
					sax3dw.setAsHasBeen(supMeshName);
					buildUITreeNode("mesh", supMeshName, msShape, "DEF", supMeshName);
					treeTabs = treeTabs + 1;
					if(ttabsMax < treeTabs) ttabsMax = treeTabs;
						if(hasMetadata) addMetadataTag(supMeshName);
						setUpAppearance(shaders.operator [](0), dagpath);
						setUpGeometry(dagpath, nodeType, 0);//(mesh, groups, nodeType, 0);
					treeTabs = treeTabs - 1;
				}
				else buildUITreeNode("mesh", supMeshName, msShape, "USE", supMeshName);
			}
			else
			{
				bool hasBeen = sax3dw.checkIfHasBeen(supMeshName);
				if(hasBeen == false)
				{
					sax3dw.setAsHasBeen(supMeshName);
					buildUITreeNode("mesh", supMeshName, msGroup, "DEF", supMeshName);
					treeTabs = treeTabs + 1;
					if(ttabsMax < treeTabs) ttabsMax = treeTabs;
						if(hasMetadata) addMetadataTag(supMeshName);

						unsigned int i;
						for(i=0; i<groups.length(); i++)
						{
							if(groups.operator [](i).apiType()!= MFn::kInvalid)
							{
								MString endVal;
								endVal.set(i);
								MString rawKeeShape(supMeshName);
								rawKeeShape.operator +=("_rks_");
								rawKeeShape.operator +=(endVal);

								buildUITreeNode("mesh", supMeshName, msShape, "DEF", rawKeeShape);
								treeTabs = treeTabs + 1;
								if(ttabsMax < treeTabs) ttabsMax = treeTabs;
									setUpAppearance(shaders.operator [](i), dagpath);
									setUpGeometry(dagpath, nodeType, i);//(mesh, groups, nodeType, i);
								treeTabs = treeTabs - 1;
							}
						}
					treeTabs = treeTabs - 1;
				}
				else buildUITreeNode("mesh", supMeshName, msGroup, "USE", supMeshName);
			}
		}
	}
	else
	{
		shArray1.append(MString("containerField"));
		shArray2.append(cfVal);

		MString nodeType;
		bool hasDefined = false;

		MString geoname;
		MString gur("getUnderworldRelatives ");
		gur.operator +=(dagFn.name());
		MGlobal::executeCommand(gur, geoname);

		MFnDagNode cDagFn;
		if(geoname != "")
		{
//			MFnDependencyNode aDep = web3dem.getMyDepNode(geoname);
			MFnDependencyNode aDep(web3dem.getMyDepNodeObj(geoname));
			cDagFn.setObject(aDep.object());
			if(cDagFn.typeName() == "x3dIndexedFaceSet" || cDagFn.typeName() == "x3dSphere" || cDagFn.typeName() == "x3dBox" || cDagFn.typeName() == "x3dCone" || cDagFn.typeName() == "x3dCylinder")
			{
				nodeType = cDagFn.typeName();
				hasDefined = true;
			}

		}
		if(!hasDefined) nodeType.set("x3dIndexedFaceSet");

		if(hasDefined == true && nodeType != "x3dIndexedFaceSet")
		{
			bool hasBeen = sax3dw.checkIfHasBeen(supMeshName);
			if(hasBeen == false)
			{
				sax3dw.setAsHasBeen(supMeshName);
				sax3dw.startNode(msShape, supMeshName, shArray1, shArray2, true);
					if(hasMetadata) addMetadataTag(supMeshName);
					setUpAppearance(shaders.operator [](0), dagpath);
					if(nodeType != "x3dIndexedFaceSet")	writePrimative(cDagFn.object());
				sax3dw.endNode(msShape, supMeshName);
			}
			else
			{
				sax3dw.preWriteField(cfVal);
				sax3dw.useDecl(msShape, supMeshName, "containerField", cfVal);
			}
		}
		else
		{
			if(groups.length() == 1)
			{
				bool hasBeen = sax3dw.checkIfHasBeen(supMeshName);
				if(hasBeen == false)
				{
					sax3dw.setAsHasBeen(supMeshName);
					sax3dw.startNode(msShape, supMeshName, shArray1, shArray2, true);
						if(hasMetadata) addMetadataTag(supMeshName);
						setUpAppearance(shaders.operator [](0), dagpath);
						setUpGeometry(dagpath, nodeType, 0);//(mesh, groups, nodeType, 0);
					sax3dw.endNode(msShape, supMeshName);
				}
				else
				{
					sax3dw.preWriteField(cfVal);
					sax3dw.useDecl(msShape, supMeshName, "containerField", cfVal);
				}
			}
			else
			{
				bool hasBeen = sax3dw.checkIfHasBeen(supMeshName);
				if(hasBeen == false)
				{
					sax3dw.setAsHasBeen(supMeshName);
					sax3dw.startNode(msGroup, supMeshName, shArray1, shArray2, true);
						shArray2.operator [](0) = getCFValue(4);
						if(hasMetadata) addMetadataTag(supMeshName);
						unsigned int i;
						for(i=0; i<groups.length(); i++)
						{
							if(groups.operator [](i).apiType()!= MFn::kInvalid)
							{
								MString endVal;
								endVal.set(i);
								MString rawKeeShape(supMeshName);
								rawKeeShape.operator +=("_rks_");
								rawKeeShape.operator +=(endVal);
									sax3dw.startNode(msShape, rawKeeShape, shArray1, shArray2, true);
									setUpAppearance(shaders.operator [](i), dagpath);
									setUpGeometry(dagpath, nodeType, i);//(mesh, groups, nodeType, i);
									sax3dw.endNode(msShape, rawKeeShape);
							}
						}
					sax3dw.endNode(msGroup, supMeshName);
				}
				else
				{
					sax3dw.preWriteField(cfVal);
					sax3dw.useDecl(msGroup, supMeshName, "containerField", cfVal);
				}
			}
		}
	}
	return MStatus::kSuccess;
}

//void x3dExportOrganizer::writePrimative(MFnDagNode dagFn)
void x3dExportOrganizer::writePrimative(MObject mObj)
{
	MFnDagNode dagFn(mObj);

	bool hasBeen = sax3dw.checkIfHasBeen(dagFn.name());
	MString nodeType = checkUseType(dagFn.name());
	bool hasMetadata = checkForMetadata(dagFn.name());
	if(isTreeBuilding)
	{
		if(hasBeen)
		{
			buildUITreeNode(dagFn.typeName(), dagFn.name(), nodeType, "USE", dagFn.name());
		}
		else
		{
			sax3dw.setAsHasBeen(dagFn.name());
			buildUITreeNode(dagFn.typeName(), dagFn.name(), nodeType, "DEF", dagFn.name());
			if(hasMetadata) addMetadataTag(dagFn.name());
		}
	}
	else
	{
		if(hasBeen)
		{
			sax3dw.preWriteField("geometry");
			sax3dw.useDecl(nodeType, dagFn.name(), "containerField", "geometry");
		}
		else
		{
			sax3dw.setAsHasBeen(dagFn.name());
			MStringArray array1;
			MStringArray array2;
			array1 = web3dem.getX3DFields(dagFn.typeName(), 0);
			array2 = web3dem.getX3DFieldValues(dagFn.typeName(), 0);
			array1.append("containerField");
			array2.append("geometry");
			sax3dw.startNode(nodeType, dagFn.name(), array1, array2, hasMetadata);
			if(hasMetadata)
			{
				addMetadataTag(dagFn.name());
				sax3dw.endNode(nodeType, dagFn.name());
			}
		}
	}
}

void x3dExportOrganizer::setUpAppearance(MObject shadingEngine, MDagPath dagpath)
{
	MFnDependencyNode depFn(shadingEngine);
	MString x3dAppName(depFn.name());
	bool hasMetadata = checkForMetadata(x3dAppName);

	MStringArray appArray1;
	MStringArray appArray2;
	appArray1.append(MString("containerField"));
	appArray2.append(getCFValue(1));

	if(sax3dw.checkIfHasBeen(depFn.name()))
	{
		MString contField("containerField");
		MString contVal = getCFValue(1);
		if(isTreeBuilding)
		{
			buildUITreeNode(depFn.typeName(), depFn.name(), msAppearance, "USE", x3dAppName);
		}
		else
		{
			sax3dw.preWriteField(contVal);
			sax3dw.useDecl(msAppearance, x3dAppName, contField, contVal);
		}
	}
	else
	{
		sax3dw.setAsHasBeen(x3dAppName);
		if(isTreeBuilding)
		{
			buildUITreeNode(depFn.typeName(), depFn.name(), msAppearance, "DEF", x3dAppName);
			treeTabs = treeTabs + 1;
			if(ttabsMax < treeTabs) ttabsMax = treeTabs;
				if(hasMetadata)addMetadataTag(x3dAppName);
				setUpMaterial(depFn.object(), 20);
				setUpTextures(depFn.object(), 35);
				setUpTextureTransforms(depFn.object(), 36);
			treeTabs = treeTabs - 1;
		}
		else
		{
			sax3dw.startNode(msAppearance, x3dAppName, appArray1, appArray2, true);
				if(hasMetadata) addMetadataTag(x3dAppName);
				setUpMaterial(depFn.object(), 20);
				setUpTextures(depFn.object(), 35);
				setUpTextureTransforms(depFn.object(), 36);
			sax3dw.endNode(msAppearance, x3dAppName);
		}
	}
}

//void x3dExportOrganizer::textureTraversal(MFnDependencyNode depFn, int cfVal)
void x3dExportOrganizer::textureTraversal(MObject mObj, int cfVal)
{
	MFnDependencyNode depFn(mObj);

	MString contVal = getCFValue(cfVal);
	MString contField("containerField");

	bool multiValues[3] = {false, false, false};
	bool hasMulti = false;
	MStringArray textureArray;
	MStringArray modeArray;

	MPlug mBump = depFn.findPlug("normalCamera");
	MPlug mSpecular = depFn.findPlug("specularColor");
	MPlug mColor = depFn.findPlug("color");

	bool hasColorTexture = false;

	multiValues[0] = web3dem.findSpecularMap(mSpecular, textureArray, modeArray);

	multiValues[1] = web3dem.findBumpMap(mBump, textureArray, modeArray);
	int spSub = textureArray.length();

	bool hasAnother = false;
	if(multiValues[0] == true || multiValues[1] == true) hasAnother = true;
	multiValues[2] = web3dem.findColorMap(mColor, textureArray, modeArray, hasAnother);
	int coSub = textureArray.length();

	int coTex = coSub-spSub;

	if(coTex > 0) hasColorTexture = true;


	if(multiValues[0] == false && multiValues[1] == false && multiValues[2] == false) hasMulti = false;
	else hasMulti = true;

	if(isTreeBuilding)
	{
		if((exEncoding == VRML97ENC && hasColorTexture == true) || (hasMulti == false && hasColorTexture == true))
		{
			MString tNodeName;
			if(multiValues[0] == true && multiValues[1] == true)  tNodeName = textureArray.operator [](2);
			else if(multiValues[0] == true || multiValues[1] == true) tNodeName = textureArray.operator [](1);
			else tNodeName = textureArray.operator [](0);
//			MFnDependencyNode myDep = web3dem.findNonExportTexture(tNodeName);
			MFnDependencyNode myDep(web3dem.findNonExportTexture(tNodeName));
			writeTexture(myDep.object(), "texture");
			
//			MStringArray textureData = getTextureData(tNodeName);
//			buildUITreeNode("file", "", textureData.operator [](0), "USE", textureData.operator [](1));
		}
		else if(hasMulti == true && exEncoding != VRML97ENC)
		{
			MString multiName(depFn.name());
			multiName.operator +=("_multi_t");
			
			buildUITreeNode("", "", msMultiTexture, "DEF", multiName);
			treeTabs = treeTabs + 1;
			if(ttabsMax < treeTabs) ttabsMax = treeTabs;
				unsigned int texSize = textureArray.length();
				unsigned int i;
				for(i=0; i<texSize; i++)
				{
//					MFnDependencyNode myDep = web3dem.findNonExportTexture(textureArray.operator [](i));
					MFnDependencyNode myDep(web3dem.findNonExportTexture(textureArray.operator [](i)));
					writeTexture(myDep.object(), "texture");
//					MStringArray textureData = getTextureData(textureArray.operator [](i));
//					buildUITreeNode("file", "", textureData.operator [](0), "USE", textureData.operator [](1));
				}
			treeTabs = treeTabs - 1;
		}

	}
	else
	{
		if((exEncoding == VRML97ENC && hasColorTexture == true) || (hasMulti == false && hasColorTexture == true))
		{
			MString tNodeName;
			if(multiValues[0] == true && multiValues[1] == true)  tNodeName = textureArray.operator [](2);
			else if(multiValues[0] == true || multiValues[1] == true) tNodeName = textureArray.operator [](1);
			else tNodeName = textureArray.operator [](0);
//			MStringArray textureData = getTextureData(tNodeName);
//			sax3dw.preWriteField("texture");//4779
//			MFnDependencyNode myDep = web3dem.findNonExportTexture(tNodeName);
			MFnDependencyNode myDep(web3dem.findNonExportTexture(tNodeName));
			writeTexture(myDep.object(), "texture");
//			sax3dw.useDecl(textureData.operator [](0), textureData.operator [](1), contField, contVal);
		}
		else if(hasMulti == true && exEncoding != VRML97ENC)
		{
			MString modeStrings;
			unsigned int i;
			unsigned int modeSize = modeArray.length();
			for(i=0; i<modeSize; i++)
			{
				modeStrings.operator +=("\"");
				modeStrings.operator +=(modeArray.operator [](i));
				modeStrings.operator +=("\"");
				if(i != modeSize-1) modeStrings.operator += (" ");
			}
			MStringArray multiT1;
			multiT1.append("mode");
			multiT1.append(contField);
			MStringArray multiT2;
			if(exEncoding == X3DVENC)
			{
				MString modStr("[ ");
				modStr.operator +=(modeStrings);
				modStr.operator +=(" ]");
				modeStrings = modStr;
			}
			multiT2.append(modeStrings);
			multiT2.append(contVal);

			MString multiName(depFn.name());
			multiName.operator +=("_multi_t");
			
			sax3dw.startNode(msMultiTexture, multiName, multiT1, multiT2, true);
				unsigned int texSize = textureArray.length();
				if(texSize>1)
				{
					sax3dw.preWriteField("texture");
					sax3dw.writeSBracket();
				}
				for(i=0; i<texSize; i++)
				{
//					MStringArray textureData = getTextureData(textureArray.operator [](i));
					if(texSize > 1) sax3dw.setHasMultiple(true);
//					sax3dw.preWriteField("texture");
					cout << "PreGrab Texture: " << textureArray.operator [](i) << endl;
//					MFnDependencyNode myDep = web3dem.findNonExportTexture(textureArray.operator [](i));
					MFnDependencyNode myDep(web3dem.findNonExportTexture(textureArray.operator [](i)));
					MPlug pixPlug = myDep.findPlug("tOption");
					int isPixel = 0;
					pixPlug.getValue(isPixel);
					bool hasBeen = sax3dw.checkIfHasBeen(myDep.name());
					cout << "Texture - " << myDep.name().asChar() << ": " << hasBeen << endl;
					if(isPixel == 1 && exEncoding == X3DVENC && texSize > 1 && hasBeen == false) sax3dw.writeTabs();//99009900
					writeTexture(myDep.object(), "texture");
//					sax3dw.useDecl(textureData.operator [](0), textureData.operator [](1), contField, contVal);
				}
				if(texSize>1) sax3dw.writeEBracket();
			sax3dw.endNode(msMultiTexture, multiName);
		}
	}
}

MStringArray x3dExportOrganizer::getTextureData(MString nodeName)
{
	MStringArray textureData;
	textureData.append(msImageTexture);
	textureData.append(nodeName);
//	MFnDependencyNode tNode = web3dem.getMyDepNode(nodeName);
	MFnDependencyNode tNode(web3dem.getMyDepNodeObj(nodeName));

	MPlug pixPlug = tNode.findPlug("tOption");
	int isPixel = 0;
	pixPlug.getValue(isPixel);

	if(tNode.typeName() == "file")
	{
		if(isPixel == 1) textureData.operator [](0).set(msPixelTexture);
		else textureData.operator [](0).set(msImageTexture);
	}
	else if(tNode.typeName() == "movie")
	{
		textureData.operator [](0).set(msMovieTexture);
	}
	else
	{
		if(isPixel == 1) textureData.operator [](0).set(msPixelTexture);
		else textureData.operator [](0).set(msImageTexture);
		if(!isTreeBuilding) textureData.operator [](1).operator +=("_rawkee_export");
	}
	return textureData;
}

//void x3dExportOrganizer::textureTransformTraversal(MFnDependencyNode depFn, int cfVal)
void x3dExportOrganizer::textureTransformTraversal(MObject mObj, int cfVal)
{
	MFnDependencyNode depFn(mObj);

	MStringArray ttArray1;
	MStringArray ttArray2;
	ttArray1.append("containerField");
	ttArray2.append(getCFValue(cfVal));

	bool multiValues[3] = {false, false, false};
	bool hasMulti = false;
	MStringArray textureArray;
	MStringArray modeArray;

	MPlug mBump = depFn.findPlug("normalCamera");
	MPlug mColor = depFn.findPlug("color");
	MPlug mSpecular = depFn.findPlug("specularColor");

	bool hasColorTexture = false;
	multiValues[0] = web3dem.findSpecularMap(mSpecular, textureArray, modeArray);

	multiValues[1] = web3dem.findBumpMap(mBump, textureArray, modeArray);
	int spSub = textureArray.length();

	bool hasAnother = false;
	if(multiValues[0] == true || multiValues[1] == true) hasAnother = true;
	multiValues[2] = web3dem.findColorMap(mColor, textureArray, modeArray, hasAnother);
	int coSub = textureArray.length();

	int coTex = coSub-spSub;

	if(coTex > 0) hasColorTexture = true;

	if(multiValues[0] == false && multiValues[1] == false && multiValues[2] == false) hasMulti = false;
	else hasMulti = true;

	if(isTreeBuilding)
	{
		if((exEncoding == VRML97ENC && hasColorTexture == true) || (hasMulti == false && hasColorTexture == true))
		{
			MString tNodeName;
			if(multiValues[0] == true && multiValues[1] == true)  tNodeName = textureArray.operator [](2);
			else if(multiValues[0] == true || multiValues[1] == true) tNodeName = textureArray.operator [](1);
			else tNodeName = textureArray.operator [](0);
			MStringArray tTransformData = getTextureTransform(tNodeName);

			bool hasMetadata = false;
			if(tTransformData.operator [](0) == "true")	hasMetadata = true;
			
			bool hasBeen = sax3dw.checkIfHasBeen(tTransformData.operator [](1));
			if(hasBeen) buildUITreeNode("", "", msTextureTransform, "USE", tTransformData.operator [](1));
			else
			{
				sax3dw.setAsHasBeen(tTransformData.operator [](1));
				buildUITreeNode("", "", msTextureTransform, "USE", tTransformData.operator [](1));
				if(hasMetadata) addMetadataTag(tTransformData.operator [](1));
			}
		}
		else if(hasMulti == true && exEncoding != VRML97ENC)
		{
			MString multiName(depFn.name());
			multiName.operator +=("_multi_tt");
			if(isTreeBuilding)
			{
				buildUITreeNode("", "", msMultiTextureTransform, "DEF", multiName);
				treeTabs = treeTabs + 1;
				if(ttabsMax < treeTabs) ttabsMax = treeTabs;
			}
			else sax3dw.startNode(msMultiTextureTransform, multiName, ttArray1, ttArray2, true);

			unsigned int i;
			unsigned int tTransSize = textureArray.length();
			if(tTransSize>1 && isTreeBuilding != true)
			{
				sax3dw.preWriteField("textureTransform");
				sax3dw.writeSBracket();
			}
			for(i=0; i<tTransSize; i++)
			{
				MStringArray tTransformData = getTextureTransform(textureArray.operator [](i));
				MStringArray nttArray1;
				MStringArray nttArray2;
				if(!isTreeBuilding)
				{
					MFnDependencyNode depNode(web3dem.getMyDepNodeObj(tTransformData.operator [](1)));
					nttArray1 = web3dem.getX3DFields(depNode, 0);
					nttArray2 = web3dem.getX3DFieldValues(depNode, 0);
					nttArray1.append(ttArray1.operator [](0));
					nttArray2.append(ttArray2.operator [](0));
				}

				bool hasMetadata = false;
				if(tTransformData.operator [](0) == "true")	hasMetadata = true;

				bool hasBeen = sax3dw.checkIfHasBeen(tTransformData.operator [](1));
				if(hasBeen){
					if(isTreeBuilding) buildUITreeNode("", "", msTextureTransform, "USE", tTransformData.operator [](1));
					else
					{
						if(tTransSize>1) sax3dw.setHasMultiple(true);
						sax3dw.preWriteField("textureTransform");
						sax3dw.useDecl(msTextureTransform,tTransformData.operator [](1), ttArray1.operator [](0), ttArray2.operator [](0));
					}
				}
				else
				{
					sax3dw.setAsHasBeen(tTransformData.operator [](1));
					if(isTreeBuilding)
					{
						buildUITreeNode("", "", msTextureTransform, "DEF", tTransformData.operator [](1));
						if(hasMetadata) addMetadataTag(tTransformData.operator [](1));
					}
					else
					{
						if(tTransSize>1) sax3dw.setHasMultiple(true);
						sax3dw.startNode(msTextureTransform, tTransformData.operator [](1), nttArray1, nttArray2, hasMetadata);
						if(hasMetadata){
							addMetadataTag(tTransformData.operator [](1));
							sax3dw.endNode(msTextureTransform, tTransformData.operator [](1));
						}
					}
				}
			}
			if(tTransSize > 1 && isTreeBuilding != true) sax3dw.writeEBracket();
			if(isTreeBuilding) treeTabs = treeTabs - 1;
			else sax3dw.endNode(msMultiTextureTransform, multiName);
			
		}
	}
	else
	{
		if((exEncoding == VRML97ENC && hasColorTexture == true) || (hasMulti == false && hasColorTexture == true))
		{
			MString tNodeName;
			if(multiValues[0] == true && multiValues[1] == true)  tNodeName = textureArray.operator [](2);
			else if(multiValues[0] == true || multiValues[1] == true) tNodeName = textureArray.operator [](1);
			else tNodeName = textureArray.operator [](0);
			MStringArray tTransformData = getTextureTransform(tNodeName);
			MFnDependencyNode x3dNode(web3dem.getMyDepNodeObj(tTransformData.operator [](1)));
			MStringArray nttArray1 = web3dem.getX3DFields(x3dNode, 0);
			MStringArray nttArray2 = web3dem.getX3DFieldValues(x3dNode, 0);
			nttArray1.append(ttArray1.operator [](0));
			nttArray2.append(ttArray2.operator [](0));

			bool hasMetadata = false;
			if(tTransformData.operator [](0) == "true")	hasMetadata = true;
			
			bool hasBeen = sax3dw.checkIfHasBeen(tTransformData.operator [](1));
			if(hasBeen)
			{
				sax3dw.preWriteField("textureTransform");
				sax3dw.useDecl(msTextureTransform,tTransformData.operator [](1), ttArray1.operator [](0), ttArray2.operator [](0));
			}
			else
			{
				sax3dw.setAsHasBeen(tTransformData.operator [](1));
				sax3dw.startNode(msTextureTransform, tTransformData.operator [](1), nttArray1, nttArray2, hasMetadata);
				if(hasMetadata){
					addMetadataTag(tTransformData.operator [](1));
					sax3dw.endNode(msTextureTransform, tTransformData.operator [](1));
				}
			}
		}
		else if(hasMulti == true && exEncoding != VRML97ENC)
		{
			MString multiName(depFn.name());
			multiName.operator +=("_multi_tt");
			
			sax3dw.startNode(msMultiTextureTransform, multiName, ttArray1, ttArray2, true);
				unsigned int i;
				unsigned int tTransSize = textureArray.length();
				if(tTransSize>1)
				{
					sax3dw.preWriteField("textureTransform");
					sax3dw.writeSBracket();
				}
				for(i=0; i<tTransSize; i++)
				{
					MStringArray tTransformData = getTextureTransform(textureArray.operator [](i));
					MFnDependencyNode x3dNode_a(web3dem.getMyDepNodeObj(tTransformData.operator [](1)));
					MStringArray nttArray1 = web3dem.getX3DFields(x3dNode_a, 0);
					MStringArray nttArray2 = web3dem.getX3DFieldValues(x3dNode_a, 0);
					nttArray1.append(ttArray1.operator [](0));
					nttArray2.append(ttArray2.operator [](0));

					bool hasMetadata = false;
					if(tTransformData.operator [](0) == "true")	hasMetadata = true;

					bool hasBeen = sax3dw.checkIfHasBeen(tTransformData.operator [](1));
					if(hasBeen){
						if(tTransSize>1) sax3dw.setHasMultiple(true);
						sax3dw.preWriteField("textureTransform");
						sax3dw.useDecl(msTextureTransform,tTransformData.operator [](1), ttArray1.operator [](0), ttArray2.operator [](0));
					}
					else
					{
						sax3dw.setAsHasBeen(tTransformData.operator [](1));
						if(tTransSize>1) sax3dw.setHasMultiple(true);
						sax3dw.startNode(msTextureTransform, tTransformData.operator [](1), nttArray1, nttArray2, hasMetadata);
						if(hasMetadata){
							addMetadataTag(tTransformData.operator [](1));
							sax3dw.endNode(msTextureTransform, tTransformData.operator [](1));
						}
					}
				}
				if(tTransSize > 1) sax3dw.writeEBracket();
			sax3dw.endNode(msMultiTextureTransform, multiName);
		}
	}
}

MStringArray x3dExportOrganizer::getTextureTransform(MString textureName)
{
	MStringArray tTransformData;
	MFnDependencyNode depFn(web3dem.getMyDepNodeObj(textureName));
	MPlugArray tArray;
	MPlug aPlug = depFn.findPlug("uvCoord");
	aPlug.connectedTo(tArray, true, false);
	if(tArray.length() > 0)
	{
		MObject obj = tArray.operator [](0).node();
		MFnDependencyNode depNode(obj);
		if(depNode.typeName() == "place2dTexture")
		{
			bool hasMetadata = checkForMetadata(depNode.name());
			if(hasMetadata == true && exEncoding != VRML97ENC) tTransformData.append("true");
			else tTransformData.append("false");
			tTransformData.append(depNode.name());
		}
		else
		{
			tTransformData.append("false");
			MString newName(textureName);
			newName.operator +=("_tt");
			tTransformData.append(newName);
		}
	}
	else
	{
		tTransformData.append("false");
		MString newName(textureName);
		newName.operator +=("_tt");
		tTransformData.append(newName);
	}
	return tTransformData;
}

//void x3dExportOrganizer::setUpMaterial(MFnDependencyNode depFn, int cfVal)
void x3dExportOrganizer::setUpMaterial(MObject mObj, int cfVal)
{
	MFnDependencyNode depFn(mObj);

	MPlug aPlug = depFn.findPlug("surfaceShader");
	bool hasLS = false;
	MItDependencyGraph appIter(aPlug, MFn::kLayeredShader, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	while(!appIter.isDone())
	{
		MFnDependencyNode lsTest(appIter.thisNode());
		if(lsTest.typeName() == "layeredShader") hasLS = true;
		appIter.next();
	}

	MString shaderType = depFn.typeName();
	if(hasLS)
	{
	}
	else
	{
		MFnDependencyNode shader;
		bool nFound = true;
		MItDependencyGraph shIter1(aPlug, MFn::kLambert,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
		while(!shIter1.isDone())
		{
			MFnDependencyNode lambertTest(shIter1.thisNode());
			if(lambertTest.typeName() == "lambert")
			{
				shader.setObject(lambertTest.object());
				nFound = false;
			}
			shIter1.next();
		}
		if(nFound)
		{
			MItDependencyGraph shIter2(aPlug, MFn::kBlinn,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!shIter2.isDone())
			{
				MFnDependencyNode blinnTest(shIter2.thisNode());
				if(blinnTest.typeName() == "blinn")
				{
					shader.setObject(blinnTest.object());
					nFound = false;
				}
				shIter2.next();
			}
		}
		if(nFound)
		{
			MItDependencyGraph shIter3(aPlug, MFn::kPhong,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!shIter3.isDone())
			{
				MFnDependencyNode phongTest(shIter3.thisNode());
				if(phongTest.typeName() == "phong")
				{
					shader.setObject(phongTest.object());
					nFound = false;
				}
				shIter3.next();
			}
		}
		if(nFound)
		{
			MItDependencyGraph shIter4(aPlug, MFn::kPhongExplorer,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!shIter4.isDone())
			{
				MFnDependencyNode phongETest(shIter4.thisNode());
				if(phongETest.typeName() == "phongE")
				{
					shader.setObject(phongETest.object());
					nFound = false;
				}
				shIter4.next();
			}
		}
		if(nFound != true && shader.name() != "") shaderTraversal(shader.object(), cfVal);
	}
}

//void x3dExportOrganizer::setUpTextures(MFnDependencyNode depFn, int cfVal)
void x3dExportOrganizer::setUpTextures(MObject mObj, int cfVal)
{
	MFnDependencyNode depFn(mObj);

	MPlug aPlug = depFn.findPlug("surfaceShader");
	bool hasLS = false;
	MItDependencyGraph appIter(aPlug, MFn::kLayeredShader, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	while(!appIter.isDone())
	{
		MFnDependencyNode lsTest(appIter.thisNode());
		if(lsTest.typeName() == "layeredShader") hasLS = true;
		appIter.next();
	}
	MString shaderType = depFn.typeName();
	if(hasLS)
	{
	}
	else
	{
		MFnDependencyNode shader;
		bool nFound = true;
		MItDependencyGraph shIter1(aPlug, MFn::kLambert,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
		while(!shIter1.isDone())
		{
			MFnDependencyNode lambertTest(shIter1.thisNode());
			if(lambertTest.typeName() == "lambert")
			{
				shader.setObject(lambertTest.object());
				nFound = false;
			}
			shIter1.next();
		}
		if(nFound)
		{
			MItDependencyGraph shIter2(aPlug, MFn::kBlinn,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!shIter2.isDone())
			{
				MFnDependencyNode blinnTest(shIter2.thisNode());
				if(blinnTest.typeName() == "blinn")
				{
					shader.setObject(blinnTest.object());
					nFound = false;
				}
				shIter2.next();
			}
		}
		if(nFound)
		{
			MItDependencyGraph shIter3(aPlug, MFn::kPhong,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!shIter3.isDone())
			{
				MFnDependencyNode phongTest(shIter3.thisNode());
				if(phongTest.typeName() == "phong")
				{
					shader.setObject(phongTest.object());
					nFound = false;
				}
				shIter3.next();
			}
		}
		if(nFound)
		{
			MItDependencyGraph shIter4(aPlug, MFn::kPhongExplorer,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!shIter4.isDone())
			{
				MFnDependencyNode phongETest(shIter4.thisNode());
				if(phongETest.typeName() == "phongE")
				{
					shader.setObject(phongETest.object());
					nFound = false;
				}
				shIter4.next();
			}
		}
		if(nFound != true && shader.name() != "") textureTraversal(shader.object(), cfVal);
	}
}

//void x3dExportOrganizer::setUpTextureTransforms(MFnDependencyNode depFn, int cfVal)
void x3dExportOrganizer::setUpTextureTransforms(MObject mObj, int cfVal)
{
	MFnDependencyNode depFn(mObj);

	MPlug aPlug = depFn.findPlug("surfaceShader");
	bool hasLS = false;
	MItDependencyGraph appIter(aPlug, MFn::kLayeredShader, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	while(!appIter.isDone())
	{
		MFnDependencyNode lsTest(appIter.thisNode());
		if(lsTest.typeName() == "layeredShader") hasLS = true;
		appIter.next();
	}
	MString shaderType = depFn.typeName();
	if(hasLS)
	{
	}
	else
	{
		MFnDependencyNode shader;
		bool nFound = true;
		MItDependencyGraph shIter1(aPlug, MFn::kLambert,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
		while(!shIter1.isDone())
		{
			MFnDependencyNode lambertTest(shIter1.thisNode());
			if(lambertTest.typeName() == "lambert")
			{
				shader.setObject(lambertTest.object());
				nFound = false;
			}
			shIter1.next();
		}
		if(nFound)
		{
			MItDependencyGraph shIter2(aPlug, MFn::kBlinn,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!shIter2.isDone())
			{
				MFnDependencyNode blinnTest(shIter2.thisNode());
				if(blinnTest.typeName() == "blinn")
				{
					shader.setObject(blinnTest.object());
					nFound = false;
				}
				shIter2.next();
			}
		}
		if(nFound)
		{
			MItDependencyGraph shIter3(aPlug, MFn::kPhong,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!shIter3.isDone())
			{
				MFnDependencyNode phongTest(shIter3.thisNode());
				if(phongTest.typeName() == "phong")
				{
					shader.setObject(phongTest.object());
					nFound = false;
				}
				shIter3.next();
			}
		}
		if(nFound)
		{
			MItDependencyGraph shIter4(aPlug, MFn::kPhongExplorer,  MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
			while(!shIter4.isDone())
			{
				MFnDependencyNode phongETest(shIter4.thisNode());
				if(phongETest.typeName() == "phongE")
				{
					shader.setObject(phongETest.object());
					nFound = false;
				}
				shIter4.next();
			}
		}
		if(nFound != true && shader.name() != "") textureTransformTraversal(shader.object(), cfVal);
	}
}

//void x3dExportOrganizer::shaderTraversal(MFnDependencyNode depFn, int cfVal)
void x3dExportOrganizer::shaderTraversal(MObject mObj, int cfVal)
{
	MFnDependencyNode depFn(mObj);

	bool hasBeen = sax3dw.checkIfHasBeen(depFn.name());
	bool hasMetadata = checkForMetadata(depFn.name());
	if(isTreeBuilding)
	{
		if(hasBeen)
		{
			buildUITreeNode(depFn.typeName(), depFn.name(), msMaterial, "USE", depFn.name());
		}
		else
		{
			sax3dw.setAsHasBeen(depFn.name());
			buildUITreeNode(depFn.typeName(), depFn.name(), msMaterial, "DEF", depFn.name());
			if(hasMetadata) addMetadataTag(depFn.name());
		}
	}
	else
	{

		if(hasBeen)
		{
			sax3dw.useDecl(msMaterial, depFn.name(), "containerField", getCFValue(cfVal));
		}
		else
		{
			MStringArray matArray1 = web3dem.getMaterialFields();
			MStringArray matArray2 = web3dem.getMaterialFieldValues(depFn, 0);

			bool hasMore = false;
	
			if(hasMetadata == true && exEncoding != VRML97ENC) hasMore = true;

			matArray1.append("containerField");
			matArray2.append(getCFValue(cfVal));

			sax3dw.startNode(msMaterial, depFn.name(), matArray1, matArray2, hasMore);
			if(hasMore)
			{
				if(hasMetadata) addMetadataTag(depFn.name());
				sax3dw.endNode(msMaterial, depFn.name());
			}
		}
	}
}

void x3dExportOrganizer::setUpHAnimGeometry(MDagPath dagpath, unsigned int val, MStringArray sca, MFloatVectorArray cna, MString pName)
{
	MStringArray geo1;
	MStringArray geo2;
	MObjectArray apps;
	MObjectArray comps;

	MFnMesh mesh(dagpath.node());
	mesh.getConnectedSetsAndMembers(0, apps, comps, true);

	MString meshName = mesh.name();
	bool hasMetadata = false;
	if(comps.length() > 0)
	{
		MString endVal;
		endVal.set(val);
		meshName.operator +=("_ifs");
		if(comps.length() > 1)
		{
			meshName.operator +=("_");
			meshName.operator +=(endVal);
		}//else hasMetadata = checkForMetadata(mesh.name());
	}

	MString coordName(pName);
	coordName.operator +=("_Coords");
		
	MString normName(pName);
	normName.operator +=("_Norms");

	if(isTreeBuilding)
	{
		buildUITreeNode("", "", msIndexedFaceSet, "DEF", meshName);
		treeTabs = treeTabs + 1;
//		if(ttabsMax < treeTabs) ttabsMax = treeTabs;
			buildUITreeNode("", "", msCoordinate, "USE", coordName);
			if(npvNonD == 1) buildUITreeNode("", "", msNormal, "USE", normName);
			geo2 = web3dem.getHAnimIFSFieldValues(dagpath, val, sca, cna, true);			
			if(geo2.operator [](9) != "") cawTextureNodes(dagpath, val);
			//			coordNormalColorTexCoord(dagpath, val, geo2);
		treeTabs = treeTabs - 1;
	}
	else
	{
		cout << "Before IFS" << endl;
		geo1 = web3dem.getIFSFields();
		geo2 = web3dem.getHAnimIFSFieldValues(dagpath, val, sca, cna, false);
		cout << "After IFS" << endl;

		geo1.append("containerField");
		geo2.append("geometry");
		sax3dw.startNode(msIndexedFaceSet, meshName, geo1, geo2, true);
			sax3dw.preWriteField("coord");
			sax3dw.useDecl(msCoordinate, coordName, "containerField", "coord");

			if(npvNonD == 1) 
			{
				sax3dw.preWriteField("normal");
				sax3dw.useDecl(msNormal, normName, "containerField", "normal");
			}

			if(geo2.operator [](9) != "") cawTextureNodes(dagpath, val);
//			coordNormalColorTexCoord(dagpath, val, geo2);
		sax3dw.endNode(msIndexedFaceSet, meshName);
	}
}

void x3dExportOrganizer::setUpGeometry(MDagPath dagpath, MString nodeType, unsigned int val)
{
	MStringArray geo1;
	MStringArray geo2;
	if(nodeType == "x3dIndexedFaceSet")
	{
		MObjectArray apps;
		MObjectArray comps;

		MFnMesh mesh(dagpath.node());
		mesh.getConnectedSetsAndMembers(0, apps, comps, true);

		MString meshName = mesh.name();
		bool hasMetadata = false;
		if(comps.length() > 0)
		{
			MString endVal;
			endVal.set(val);
			meshName.operator +=("_ifs");
			if(comps.length() > 1)
			{
				meshName.operator +=("_");
				meshName.operator +=(endVal);
			}//else hasMetadata = checkForMetadata(mesh.name());
		}
		
		if(isTreeBuilding)
		{
			buildUITreeNode("", "", msIndexedFaceSet, "DEF", meshName);
			treeTabs = treeTabs + 1;
			if(ttabsMax < treeTabs) ttabsMax = treeTabs;
				geo2 = web3dem.getIFSFieldValues(dagpath, val);			
				coordNormalColorTexCoord(dagpath, val, geo2);
			treeTabs = treeTabs - 1;
		}
		else
		{
//			MFnDependencyNode mDep(mesh.object());
			geo1 = web3dem.getIFSFields();
			geo2 = web3dem.getIFSFieldValues(dagpath, val);

			geo1.append("containerField");
			geo2.append("geometry");
			sax3dw.startNode(msIndexedFaceSet, meshName, geo1, geo2, true);
//			if(hasMetadata) addMetadataTag(mesh.name());
				coordNormalColorTexCoord(dagpath, val, geo2);
			sax3dw.endNode(msIndexedFaceSet, meshName);
		}
	}
}

void x3dExportOrganizer::coordNormalColorTexCoord(MDagPath dagpath, unsigned int val, MStringArray geo)
{
	cawCoordinateNode(dagpath, val);
	if(geo.operator [](3) == "") cawColorNode(dagpath, val);
	if(geo.operator [](7) == "") cawNormalNode(dagpath, val);
	if(geo.operator [](9) != "") cawTextureNodes(dagpath, val);
}

void x3dExportOrganizer::cawCoordinateNode(MDagPath dagpath, unsigned int val)
{
	MFnMesh mesh(dagpath.node());
	MString meshCoord(mesh.name());
	meshCoord.operator +=("_coord");

	MStringArray coord1 = web3dem.getCoord_Fields();
	coord1.append("containerField");

	MStringArray coord2 = web3dem.getCoord_FieldValues(dagpath, val);
	coord2.append("coord");
	
	bool hasBeen = sax3dw.checkIfHasBeen(meshCoord);
	if(hasBeen)
	{
		if(isTreeBuilding) buildUITreeNode("", "", msCoordinate, "USE", meshCoord);
		else
		{
			sax3dw.preWriteField("coord");
			sax3dw.useDecl(msCoordinate, meshCoord, coord1.operator [](coord1.length()-1), coord2.operator [](coord2.length()-1));
		}
	}
	else
	{
		sax3dw.setAsHasBeen(meshCoord);
		if(isTreeBuilding) buildUITreeNode("", "", msCoordinate, "DEF", meshCoord);
		else sax3dw.startNode(msCoordinate, meshCoord, coord1, coord2, false);
	}
}

void x3dExportOrganizer::cawNormalNode(MDagPath dagpath, unsigned int val)
{
	MFnMesh mesh(dagpath.node());
	MString meshNormal(mesh.name());
	meshNormal.operator +=("_normal");

	MStringArray norm1 = web3dem.getNormal_Fields();
	norm1.append("containerField");

	MStringArray norm2 = web3dem.getNormal_FieldValues(dagpath, val);
	norm2.append("normal");

	bool hasBeen = sax3dw.checkIfHasBeen(meshNormal);
	if(hasBeen)
	{
		if(isTreeBuilding) buildUITreeNode("", "", msNormal, "USE", meshNormal);
		else
		{
			sax3dw.preWriteField("normal");
			sax3dw.useDecl(msNormal, meshNormal, norm1.operator [](norm1.length()-1), norm2.operator [](norm2.length()-1));
		}
	}
	else
	{
		sax3dw.setAsHasBeen(meshNormal);
		if(isTreeBuilding) buildUITreeNode("", "", msNormal, "DEF", meshNormal);
		else sax3dw.startNode(msNormal, meshNormal, norm1, norm2, false);
	}
}

void x3dExportOrganizer::cawColorNode(MDagPath dagpath, unsigned int val)
{
	MFnMesh mesh(dagpath.node());
	MString meshColor(mesh.name());
	meshColor.operator +=("_color");

	MStringArray color1 = web3dem.getColorFields();
	color1.append("containerField");

	MStringArray color2 = web3dem.getColorFieldValues(dagpath, val);
	color2.append("color");

	bool hasBeen = sax3dw.checkIfHasBeen(meshColor);
	if(hasBeen)
	{
		if(isTreeBuilding) buildUITreeNode("", "", msColor, "USE", meshColor);
		else
		{
			sax3dw.preWriteField("color");
			sax3dw.useDecl(msColor, meshColor, color1.operator [](color1.length()-1), color2.operator [](color2.length()-1));
		}
	}
	else
	{
		sax3dw.setAsHasBeen(meshColor);
		if(isTreeBuilding) buildUITreeNode("", "", msColor, "DEF", meshColor);
		else sax3dw.startNode(msColor, meshColor, color1, color2, false);
	}
}

void x3dExportOrganizer::cawTextureNodes(MDagPath dagpath, unsigned int val)
{
	MFloatArray uCoord;
	MFloatArray vCoord;
	MObjectArray uvTextureAssoc;

	MString uvSetName;
	MStringArray uvSetNames;
	MFnMesh mesh(dagpath.node());
	mesh.getUVSetNames(uvSetNames);

	bool hasT = false;

	//Find out if there are multiple UVsets
	MStringArray usedUVSets = web3dem.getUsedUVSetsInOrder(mesh.object(), hasT, uvSetNames, val);
	if(hasT)
	{
		bool hasMultiUVSets = false;
		if(usedUVSets.length() > 1)
		{
			unsigned int j;
			for(j=1;j<usedUVSets.length();j++)
			{
				if(usedUVSets.operator [](0) != usedUVSets.operator [](j)) hasMultiUVSets = true;
			}
		}
		
		bool canUseMulti = false;
		if((hasMultiUVSets == true && exEncoding != VRML97ENC) && hasT == true) canUseMulti = true;

		MString multiTexCoordName(mesh.name());
		if(canUseMulti)
		{
			MString midVal;
			midVal.set(val);
			multiTexCoordName.operator +=("_");
			multiTexCoordName.operator +=(midVal);
			multiTexCoordName.operator +=("_mtc");

			if(isTreeBuilding)
			{
				buildUITreeNode("", "", msMultiTextureCoordinate, "DEF", multiTexCoordName);
				treeTabs = treeTabs + 1;
				if(ttabsMax < treeTabs) ttabsMax = treeTabs;

			}
			else
			{
				MStringArray cfName;
				cfName.append("containerField");
				MStringArray cfValue;
				cfValue.append("texCoord");

				sax3dw.preWriteField("texCoord");
				sax3dw.startNode(msMultiTextureCoordinate, multiTexCoordName, cfName, cfValue, true);
			}
		}
		else if(hasT)
		{
			MString singleSet = usedUVSets.operator [](0);
			usedUVSets.clear();
			usedUVSets.append(singleSet);
		}
		else usedUVSets.clear();

		unsigned int i;
		unsigned int uvSetLen = usedUVSets.length();
		if(uvSetLen > 1 && canUseMulti == true && isTreeBuilding != true)
		{
			sax3dw.preWriteField("texCoord");
			sax3dw.writeSBracket();
		}
		for(i=0; i<uvSetLen; i++)
		{
			MString valStr;
			valStr.set(val);
			MString texCoordName(mesh.name());
			texCoordName.operator +=("_");
			texCoordName.operator +=(usedUVSets.operator [](i));
			texCoordName.operator +=("_");
			texCoordName.operator +=(valStr);
			bool hasBeen = sax3dw.checkIfHasBeen(texCoordName);
			if(hasBeen)
			{
				if(isTreeBuilding) buildUITreeNode("", "", msTextureCoordinate, "USE", texCoordName);
				else
				{
					if(uvSetLen > 1) sax3dw.setHasMultiple(true);
					sax3dw.preWriteField("texCoord");
					sax3dw.useDecl(msTextureCoordinate, texCoordName, "containerField", "texCoord");
				}
			}
			else
			{
				sax3dw.setAsHasBeen(texCoordName);
				if(isTreeBuilding) buildUITreeNode("", "", msTextureCoordinate, "DEF", texCoordName);
				else
				{
					MStringArray array1 = web3dem.getTextCoordFields();
					array1.append("containerField");

					MStringArray array2 = web3dem.getTextCoordFieldValues(dagpath, usedUVSets.operator [](i), canUseMulti, val);
					array2.append("texCoord");
				
					if(uvSetLen > 1) sax3dw.setHasMultiple(true);
					sax3dw.startNode(msTextureCoordinate, texCoordName, array1, array2, false);
				}
			}
		}
		if(uvSetLen > 1 && canUseMulti == true && isTreeBuilding != true) sax3dw.writeEBracket();
		if(canUseMulti)
		{
			if(isTreeBuilding) treeTabs = treeTabs - 1;
			else sax3dw.endNode(msMultiTextureCoordinate, multiTexCoordName);
		}
	}
}

//MStatus x3dExportOrganizer::writeLeafNodes(MString childName, MString nodeType, MStringArray newArray1, MStringArray newArray2)
//MStatus x3dExportOrganizer::writeLeafNodes(MString mayaName, MFnDependencyNode depNode, MString x3dName, MString x3dType, MStringArray newArray1, MStringArray newArray2)
MStatus x3dExportOrganizer::writeLeafNodes(MString mayaName, MObject mObj, MString x3dName, MString x3dType, MStringArray newArray1, MStringArray newArray2)
{
	MFnDependencyNode depNode(mObj);
	return writeLeafNodes(mayaName, depNode.typeName(), x3dName, x3dType, newArray1, newArray2);
}

MStatus x3dExportOrganizer::writeLeafNodes(MString mayaName, MString mayaType, MString x3dName, MString x3dType, MStringArray newArray1, MStringArray newArray2)
{
	//Metadata check for this node
	bool hasMetadata = checkForMetadata(mayaName);
	bool hasAudio = false;
	if(mayaType.operator ==(X3D_SOUND)) hasAudio = checkForAudio(mayaName);
	MObjectArray loadNodes = getWatchedNodes(mayaName);

	unsigned int lsLen = loadNodes.length();

	bool openNode = false;
	if(hasMetadata == true || hasAudio == true || lsLen > 0) openNode = true;

	if(isTreeBuilding)
	{
			buildUITreeNode(mayaType, mayaName, x3dType, "DEF", x3dName);
			treeTabs = treeTabs + 1;
			if(ttabsMax < treeTabs) ttabsMax = treeTabs;
			if(hasMetadata) addMetadataTag(mayaName);
			if(hasAudio)
			{
				MFnDependencyNode childNode = web3dem.getMyDepNodeObj(mayaName);
				MPlug aPlug = childNode.findPlug("audioIn");

				MItDependencyGraph depIt(aPlug, MFn::kInvalid, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
				bool searching = true;
				while(!depIt.isDone() && searching == true)
				{
					MObject obj = depIt.thisNode();//5750
					MFnDependencyNode mNode(obj);
					if(mNode.typeName() == "audio" || mNode.typeName() == "movie") addAudioTag(mayaName);
					depIt.next();
				}
			}
			if(lsLen > 0)
			{
				unsigned int i;
				for(i=0;i<lsLen;i++)
				{
					MFnDependencyNode wNode(loadNodes.operator [](i));
					cout << "LoadSensor Name: " << wNode.name().asChar() << endl;
					if(lsLen>1) sax3dw.setHasMultiple(true);
					if(wNode.typeName().operator ==("audio")) writeAudioClip(wNode.object(), "watchList");
					else if(wNode.typeName().operator ==("x3dInline"))
					{
						bool hLayer = isInHiddenLayer(wNode.name());
						if(!hLayer) writeInlineC(wNode.object(), "watchList");
					}
					else
					{
						MPlug pixPlug = wNode.findPlug("tOption");
						int isPixel = 0;
						pixPlug.getValue(isPixel);
						if(isPixel == 0) writeTexture(wNode.object(), "watchList");
					}
				}
			}
			treeTabs = treeTabs - 1;
	}
	else//000777000777
	{
			sax3dw.startNode(x3dType, x3dName, newArray1, newArray2, openNode);
			
			//if node has metadata, add metadata tag and close the node
			if(hasMetadata) addMetadataTag(mayaName);
			if(hasAudio) addAudioTag(mayaName);
			if(lsLen > 0)
			{
				if(lsLen>1)
				{
					sax3dw.preWriteField("watchList");
					sax3dw.writeSBracket();
				}
				unsigned int i;
				for(i=0;i<lsLen;i++)
				{
					MFnDependencyNode wNode(loadNodes.operator [](i));
					if(lsLen>1) sax3dw.setHasMultiple(true);
					if(wNode.typeName().operator ==("movie")) writeTexture(wNode.object(), "watchList");//sax3dw.useDecl(msMovieTexture, wNode.name(), "containerField", "watchList");
					if(wNode.typeName().operator ==("file"))
					{
						MPlug pixPlug = wNode.findPlug("tOption");
						int isPixel = 0;
						pixPlug.getValue(isPixel);
						if(isPixel == 0) writeTexture(wNode.object(), "watchList");//sax3dw.useDecl(msImageTexture, wNode.name(), "containerField", "watchList");
					}
					if(wNode.typeName().operator ==("audio")) writeAudioClip(wNode.object(), "watchList");//sax3dw.useDecl(msAudioClip, wNode.name(), "containerField", "watchList");
					if(wNode.typeName().operator ==("x3dInline"))
					{
						bool hLayer = isInHiddenLayer(wNode.name());
						if(!hLayer) writeInlineC(wNode.object(), "watchList");//sax3dw.useDecl(msInline, wNode.name(), "containerField", "watchList");
					}
				}
				if(lsLen>1) sax3dw.writeEBracket();
			}
			if(openNode) sax3dw.endNode(x3dType, x3dName);
	}

	return MStatus::kSuccess;
}

//MStatus x3dExportOrganizer::writeScript(MFnDagNode aDag, MString cfVal)
MStatus x3dExportOrganizer::writeScript(MObject mObj, MString cfVal)
{
	MFnDagNode aDag(mObj);

	//Retrieve the name of this node
	MString scriptName = aDag.name();

	//Check to see if the script node has metadata
	bool hasMetadata = checkForMetadata(scriptName);

	if(isTreeBuilding)
	{
		buildUITreeNode(aDag.typeName(), scriptName, msScript, "DEF", scriptName);
		treeTabs = treeTabs + 1;
		if(ttabsMax < treeTabs) ttabsMax = treeTabs;
		if(hasMetadata) addMetadataTag(scriptName);

		MStringArray cFieldTypes = web3dem.getScriptCustomFieldTypes(aDag);
		MStringArray cFieldAccess = web3dem.getScriptCustomFieldAccess(aDag);
		unsigned int cLen = cFieldTypes.length();

		unsigned int i;
		for(i=0;i<cLen;i++)
		{
			if(cFieldTypes.operator [](i).operator ==("SFNode") || cFieldTypes.operator [](i).operator ==("MFNode"))
			{
				if(cFieldAccess.operator [](i).operator !=("inputOnly") || cFieldAccess.operator [](i).operator !=("outputOnly"))
				{
					/*
					MObjectArray objArray = web3dem.getScriptNodeObjects(aDag, i);
					
					unsigned int objLen = objArray.length();

					unsigned int j;
					for(j=0; j< objLen; j++)
					{
						MDagPath newdp = MDagPath::getAPathTo(objArray.operator [](j));
						MFnDagNode newdn(newdp);
						MFnDagNode newDagFn(newdn.object());
						processChildNode(newDagFn.object(), 0, "");
					}
					*/
				}
			}
		}
		//------------------------------
		//
		//  Leaving space for node field tree structure
		//
		//------------------------------
		
		treeTabs = treeTabs - 1;
	}
	else
	{
		//Arrays used to hold the default field names
		//for a script node and their values
		MStringArray scrArray1;
		MStringArray scrArray2;

		//Writing an X3D Script node to a file is complicated. 
		//Techniques for exporting script URL are different for 
		//both XML and Traditional style encodings, and possibly 
		//different for local and non-local URL's depending on
		//the encoding style
		scrArray1 = web3dem.getX3DFields(scriptName, 0);
		scrArray1.append(MString("containerField"));

		scrArray2 = web3dem.getX3DFieldValues(scriptName, 0);
		scrArray2.append(cfVal);
		
		//Check to see if the script node has a local url
		//for defining its functions

		//start node write out
		sax3dw.startNode(msScript,scriptName,scrArray1,scrArray2,true);
			
			if(hasMetadata) addMetadataTag(scriptName);


			MStringArray cFieldNames = web3dem.getScriptCustomFieldNames(aDag);

			MStringArray cFieldTypes = web3dem.getScriptCustomFieldTypes(aDag);

			MStringArray cFieldAccess = web3dem.getScriptCustomFieldAccess(aDag);


			//The user-defined arrays should all match in length
			unsigned int cLen = cFieldNames.length();
			unsigned int i;

			//The user-defined fields when exported as
			//XML encoding, are written in a manner similar
			//to a the way a node is written. Therefore, we
			//can use the sax3dw.startNode and writeNodeField methods
			//for writing out our nodes.

			for(i=0;i<cLen;i++)
			{
				bool useField = true;
				if(exEncoding == VRML97ENC && cFieldAccess.operator [](i).operator ==("inputOutput")) useField = false;
				if(useField)
				{
					MStringArray splitArray;
					cFieldTypes.operator [](i).split('F', splitArray);
					bool isMultiple = false;
					if(splitArray.operator [](0).operator ==("M")) isMultiple = true;

					bool hasANode = true;
					if(splitArray.operator [](1).operator !=("Node")) hasANode = false;
					if(cFieldAccess.operator [](i).operator ==("inputOnly") || cFieldAccess.operator [](i).operator ==("outputOnly")) hasANode = false;
		
					MString value = web3dem.getScriptCustomValue(aDag, i);
					MStringArray se1;
					MStringArray se2;
					se1.append("name");
					se2.append(cFieldNames.operator [](i));
					se1.append("type");
					se2.append(cFieldTypes.operator [](i));
					se1.append("accessType");
					se2.append(cFieldAccess.operator [](i));
					se1.append("value");
					se2.append(value);
					
					sax3dw.addScriptNodeField(cFieldAccess.operator [](i), cFieldTypes.operator [](i), cFieldNames.operator [](i));
					if(isMultiple == true && cFieldTypes.operator [](i).operator ==("MFNode")) sax3dw.writeSBracket();
					else if(isMultiple) sax3dw.writeScriptSBracket();
					if(exEncoding == VRML97ENC || exEncoding == X3DVENC) sax3dw.addScriptNodeFieldValue(value);
					if((exEncoding == X3DENC || exEncoding == X3DBENC)) sax3dw.startNode(msfield, msEmpty, se1, se2, hasANode);

					if(hasANode)
					{
						MObjectArray objArray = web3dem.getScriptNodeObjects(aDag, i);
						unsigned int objLen = objArray.length();

						unsigned int j;
						for(j=0; j< objLen; j++)
						{
							MDagPath ndagp = MDagPath::getAPathTo(objArray.operator [](j));
							MFnDagNode ndfdag(ndagp);
							MFnDagNode newDagFn(ndfdag.object());
							sax3dw.setHasMultiple(true);
							processChildNode(newDagFn.object(), 0, cFieldNames.operator [](i));//999000999
						}
					}

					if(isMultiple == true && cFieldTypes.operator [](i).operator ==("MFNode")) sax3dw.writeEBracket();
					else if(isMultiple) sax3dw.writeScriptEBracket();
					if((exEncoding == X3DENC || exEncoding == X3DBENC) && hasANode == true) sax3dw.endNode(msfield, msEmpty);
				}
			}
//binary script issues
//			if((exEncoding == X3DENC || exEncoding == X3DBENC) && isTreeBuilding != true)
			if(exEncoding == X3DENC && isTreeBuilding != true)
			{
				MStringArray localScripts = web3dem.getScriptLocalURLs(aDag);
				unsigned int lsLen = localScripts.length();
				unsigned int i;
				for(i=0;i<lsLen;i++)
				{
					localScripts.operator [](i) = sax3dw.processForTabs(localScripts.operator [](i));
				}
				sax3dw.outputCData(localScripts);
			}
//binary script issues begin here
			if(exEncoding == X3DBENC && isTreeBuilding != true)
			{
				MStringArray localScripts = web3dem.getScriptLocalURLs(aDag);
				unsigned int lsLen = localScripts.length();
				unsigned int i;
				for(i=0;i<lsLen;i++)
				{
					MString sName = aDag.name();
					sName.operator +=("_");
					MString snumStr;
					snumStr.set(i);
					sName.operator +=(snumStr);
					sName.operator +=(".js");
					sax3dw.writeScriptFile(sName,localScripts.operator [](i),localPath);
				}
			}
			//
			
		sax3dw.endNode(msScript,scriptName);
			
	}

	return MStatus::kSuccess;
}

//void x3dExportOrganizer::writeNodeField(MFnDagNode dagFn, MString nodeName, MString cfVal)//MString plugName, int cfVal)
void x3dExportOrganizer::writeNodeField(MObject mObj, MString nodeName, MString cfVal)//MString plugName, int cfVal)
{
//This method writes out nodes found in SFNode and MFNode fields. If a
//grouping node is found, then it traveres this node's children as well
//following the branch of the DAG until it comes to the end of that
//branch or a node it has already exported.
	MFnDagNode dagFn(mObj);

	MString tempString = checkUseType(nodeName);//Retrieved the x3dNodeType Name

	if(tempString != msEmpty)
	{
		bool hasMetadata = checkForMetadata(nodeName);
		bool hbBool = sax3dw.checkIfHasBeen(nodeName);

		//Retrieves this node's DAG node functionality
		MSelectionList tempList;
		tempList.clear();
		tempList.add(nodeName);
		MItSelectionList newMItSel(tempList);
		MObject tObject;
		newMItSel.getDependNode(tObject);
		MFnDagNode nrDag(tObject);

		if(hbBool)
		{
			if(isTreeBuilding)
			{
				buildUITreeNode(nrDag.typeName(), nrDag.name(), tempString, "USE", nodeName);
			}
			else
			{
				MString contField("containerField");
				MString contVal = cfVal;//24 =  proxy cf
				sax3dw.preWriteField(contVal);
				sax3dw.useDecl(tempString,nodeName,contField,contVal);
			}
		}
		else
		{
			sax3dw.setAsHasBeen(nodeName);
			MStringArray nfArray1;
			MStringArray nfArray2;
//			getFieldArrays(nfArray1,nfArray2,nodeName,cfVal);

			nfArray1 = web3dem.getX3DFields(nodeName, 0);
			nfArray1.append(MString("containerField"));

			nfArray2 = web3dem.getX3DFieldValues(nodeName, 0);
			nfArray2.append(cfVal);

			if(isTreeBuilding)
			{
				buildUITreeNode(nrDag.typeName(), nrDag.name(), tempString, "DEF", nodeName);
				treeTabs = treeTabs + 1;
				if(ttabsMax < treeTabs) ttabsMax = treeTabs;
				if(hasMetadata) addMetadataTag(nodeName);
				processBranchNode(nrDag.object(), 4);
				treeTabs = treeTabs - 1;
			}
			else
			{
				if(nrDag.typeName().operator ==("lodGroup") || nrDag.typeName().operator ==("x3dSwitch")|| nrDag.typeName().operator ==("x3dCollision")|| nrDag.typeName().operator ==("x3dAnchor"))
				{
					int cNum = nrDag.childCount();
					bool isOE = false;
					if(cNum > 0) isOE = true;
					if(hasMetadata) isOE = true;
					processGrouping(nrDag.object(), msEmpty, nfArray1, nfArray2, isOE, cNum, hasMetadata);
				}
				else
				{
				//Writes the start of the node
					sax3dw.startNode(tempString,nodeName,nfArray1,nfArray2,true);

						//Checks for metadata
						if(hasMetadata)  addMetadataTag(nodeName);

						//processes this node checking it for children
						processBranchNode(nrDag.object(), 4);
					sax3dw.endNode(tempString,nodeName);
				}
			}
		}
	}
}


//Metadata - this method is only called during the export hidden nodes process
MStatus x3dExportOrganizer::writeMetadataNode(MString x3dName, MString msTString, MString ctField)
{
	bool hasBeen = sax3dw.checkIfHasBeen(x3dName);
	//Checks to see if has been written already
	if(hasBeen)
	{
		if(!isTreeBuilding)
		{
			sax3dw.preWriteField(ctField);
			sax3dw.useDecl(msTString, x3dName, "containerField", ctField);
		}
		else
		{
//			treeTabs = treeTabs + 1;

			buildUITreeNode("", "", msTString, "USE", x3dName);
//			treeTabs = treeTabs - 1;
		}
	}
	else
	{
//		cout << "Has Not" << endl;
		sax3dw.setAsHasBeen(x3dName);

		MStringArray eArray1;
		MStringArray eArray2;
		if(!isTreeBuilding)
		{
			eArray1.append(MString("name"));
			eArray1.append(MString("reference"));

			//Checks to see if that the node is not a metadataSet node
			//if it is not, then the "value" field is added to the 
			//MStringArray containing field names
			if(msTString != msMetaSe) eArray1.append(MString("value"));

			eArray1.append(MString("containerField"));
		}			
		MStringArray tempArray = getMetadataAtts(x3dName);
		if(!isTreeBuilding)
		{
			//Adds the values for the name and reference fields to 
			//the field value array
			eArray2.append(tempArray.operator [](1));
			eArray2.append(tempArray.operator [](2));

			//Checks to see that the node is not a metadataSet node
			//if not it adds a value to the field values array
			if(msTString != msMetaSe) eArray2.append(tempArray.operator [](3));

			//Sets the containerField value to "metadataStorage"
			eArray2.append(ctField);
		}
		//Check this metadata node to see if it has any metadata about it
		bool hasMetadata = checkForMetadata(x3dName);
		bool isContinued = false;
		if(hasMetadata == true || msTString == msMetaSe) isContinued = true;

		//write out the starting tag to this metadata node
		//metadata string incorrectly implemented
		if(!isTreeBuilding) sax3dw.startNode(msTString, x3dName, eArray1, eArray2, isContinued);////
		else buildUITreeNode("", "", msTString, "DEF", x3dName);

		if(hasMetadata)//////////////////////////////////////////////////
		{
			if(tempArray.operator [](0) != msEmpty) {
				MString usedType = checkUseType(tempArray.operator [](0));
				if(usedType != msEmpty){
					bool mhasBeen = sax3dw.checkIfHasBeen(tempArray.operator [](0));
					if(mhasBeen)
					{
						if(!isTreeBuilding)
						{
							sax3dw.preWriteField("metadata");
							sax3dw.useDecl(usedType, tempArray.operator [](0), "containerField", "metadata");
						}
						else
						{
							treeTabs = treeTabs + 1;
							if(ttabsMax < treeTabs) ttabsMax = treeTabs;
							buildUITreeNode("", "", usedType, "USE", tempArray.operator [](0));
							treeTabs = treeTabs - 1;
						}
					}
					else
					{
						treeTabs = treeTabs + 1;
						if(ttabsMax < treeTabs) ttabsMax = treeTabs;
						writeMetadataNode(tempArray.operator [](0), usedType, "metadata");
						treeTabs = treeTabs - 1;
					}
				}
			}
		}

		if(msTString == msMetaSe)
		//In the case of a metadataSet, the values are actually
		//other metadata nodes. The following section of code retrieves
		//the names of the node and writes them out if necessary.
		{
			//get's the length of the metadataSet values array
			MFnDependencyNode depFn = web3dem.getMyDepNodeObj(x3dName);
			MPlug aPlug = depFn.findPlug("value_cc");
			int valLength;
			aPlug.getValue(valLength);
			
			MStringArray valStrings;
			int j;
			if(valLength > 0)
			{
				sax3dw.preWriteField("value");
				sax3dw.writeSBracket();
			}
			treeTabs = treeTabs + 1;
			if(ttabsMax < treeTabs) ttabsMax = treeTabs;

			MPlug kvPlug = depFn.findPlug("value");
			for(j=0;j<valLength;j++)
			{
				MPlug namePlug = kvPlug.elementByPhysicalIndex(j);
				//retrieves the node name for the metadata value node
//				MString endVal;
//				endVal.set(j);
//				MString val("value");
//				val.operator +=(endVal);

				MString tString2;
//				aPlug = depFn.findPlug(val);
				namePlug.getValue(tString2);

				//Writes that node out.
				MString usedType = checkUseType(tString2);
				if(usedType != msEmpty){
					bool mhasBeen = sax3dw.checkIfHasBeen(tString2);
					if(mhasBeen)
					{
						if(!isTreeBuilding)
						{
							sax3dw.setHasMultiple(true);
							sax3dw.useDecl(usedType, tString2, "containerField", "value");
						}else buildUITreeNode("", "", usedType, "USE", tString2);
					}
					else writeMetadataNode(tString2, usedType, "value");
				}
			}
			treeTabs = treeTabs - 1;
			if(valLength > 0 && isTreeBuilding != true)
			{
				sax3dw.writeEBracket();
			}
		}
		if(isContinued && isTreeBuilding != true) sax3dw.endNode(msTString, x3dName);
	}
	return MStatus::kSuccess;
}

void x3dExportOrganizer::addAudioTag(MString childName)
{
	MFnDependencyNode childNode = web3dem.getMyDepNodeObj(childName);
	MPlug aPlug = childNode.findPlug("audioIn");

	MItDependencyGraph depIt(aPlug, MFn::kInvalid, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	bool searching = true;
	while(!depIt.isDone() && searching == true)
	{
		MObject obj = depIt.thisNode();
		MFnDependencyNode mNode(obj);
		if(mNode.typeName() == "audio")
		{
			writeAudioClip(mNode.object(), "source");
			searching = false;
		}
		else if(mNode.typeName() == "movie")
		{
			writeTexture(mNode.object(), "source");
			searching = false;
		}

		depIt.next();
	}
}

void x3dExportOrganizer::addMetadataTag(MString childName)
{
	if(exEncoding != VRML97ENC)
	{
		//Method that adds a USE version of a metadata node
		//to nodes other than metadata nodes.
		MFnDependencyNode metaNode;
		MString mData("");
		MFnDependencyNode childNode = web3dem.getMyDepNodeObj(childName);
		MPlug aPlug = childNode.findPlug("x3dMetadataIn");

		MItDependencyGraph depIt(aPlug, MFn::kInvalid, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
		bool searching = true;
		while(!depIt.isDone() && searching == true)
		{
			MObject obj = depIt.thisNode();
			MFnDependencyNode mNode(obj);
			if(mNode.typeName() == "x3dMetadataDouble" || mNode.typeName() == "x3dMetadataFloat" || mNode.typeName() == "x3dMetadataInteger" || mNode.typeName() == "x3dMetadataString" || mNode.typeName() == "x3dMetadataSet")
			{
				metaNode.setObject(mNode.object());
				mData = metaNode.name();
				searching = false;
			}
			depIt.next();
		}

		if(mData != msEmpty) {
			MString usedType = checkUseType(mData);
			MString metaMayaType = metaNode.typeName();
			writeMetadataNode(mData, usedType, "metadata");
//			if(isTreeBuilding)
//			{
//				buildUITreeNode(metaMayaType, metaNode.name(), usedType, "USE", metaNode.name());
				//MString mayaType, MString mayaName, MString x3dType, MString x3dUse, MString x3dName
//			}
//			else
//			{
//				sax3dw.preWriteField("metadata");
//				sax3dw.useDecl(usedType, mData, "containerField", "metadata");
//			}
		}
	}
}

void x3dExportOrganizer::outputCollidableShapes()
{
	if(isTreeBuilding) cout << "Collidable Shapes: isTreeBuilding" << endl;
	MItDag rbItDag(MItDag::kDepthFirst, MFn::kRigid);
	while(!rbItDag.isDone())
	{
		MObject rbObject = rbItDag.item();
		MFnDagNode rbDag(rbObject);
		MObject rbpObject = rbDag.parent(0);
		MFnDagNode rbpDag(rbpObject);
		unsigned int clen = rbpDag.childCount();
		unsigned int i;
		for(i=0;i<clen;i++)
		{
			MObject achild = rbpDag.child(i);
			MFnDagNode aNode(achild);
			if(aNode.typeName() == "mesh")
			{
				sax3dw.setHasMultiple(true);
				writeCollidableShape(aNode.object(), rbpDag.object(), rbDag.object(), "children");
			}
		}
		rbItDag.next();
	}
}

//void x3dExportOrganizer::writeAudioClip(MFnDependencyNode audioNode, MString ctField)
void x3dExportOrganizer::writeAudioClip(MObject mObj, MString ctField)
{
	MFnDependencyNode audioNode(mObj);
	MStringArray sArr1;
	MStringArray sArr2;
	MString nodeName = audioNode.name();
	bool hasBeen = sax3dw.checkIfHasBeen(nodeName);
	bool hasMetadata = checkForMetadata(nodeName);
	if(hasBeen)
	{
		if(!isTreeBuilding)	sax3dw.useDecl(msAudioClip, nodeName, "containerField", ctField);
		else buildUITreeNode("", "", msAudioClip, "USE", nodeName);
	}
	else
	{
		sax3dw.setAsHasBeen(nodeName);
		if(!isTreeBuilding)
		{
			sArr1 = web3dem.getX3DFields(nodeName, 0);
			sArr2 = web3dem.getX3DFieldValues(nodeName, 0);
	
			sArr1.append("containerField");
			sArr2.append(ctField);
			
			if(hasMetadata) sax3dw.setHasMultiple(true);
			sax3dw.startNode(msAudioClip, audioNode.name(), sArr1, sArr2, hasMetadata);
		}
		else buildUITreeNode("", "", msAudioClip, "DEF", nodeName);
		if(hasMetadata == true && exEncoding != VRML97ENC)
		{
			treeTabs = treeTabs + 1;
			if(ttabsMax < treeTabs) ttabsMax = treeTabs;
			addMetadataTag(audioNode.name());
			treeTabs = treeTabs - 1;
			if(!isTreeBuilding) sax3dw.endNode(msAudioClip, nodeName);
		}
		else if (hasMetadata == true && isTreeBuilding != true ) sax3dw.endNode(msAudioClip, nodeName);
	}
}

//Audio always seems to be the pain in the butt for most programs either 
//viewers or exporters. This is no exception. This audio
//export featues are slated to undergo a drastic rewrite
//so I'm not even going to document this section for now. Right now,
//this method writes AudioClip node and their Sound node parents
//to the hidden nodes section of the x3d file.
void x3dExportOrganizer::outputAudio()//MStringArray audioNames, unsigned int aSize)
{

	//Provide user feedback... blah blah blah again...
	if(!isTreeBuilding)
	{
		sax3dw.msg.set("Exporting AudioClip Nodes Hidden in a Script Node");
		cout << sax3dw.msg.asChar() << endl;
		sax3dw.msg.set(" ");
		cout << sax3dw.msg.asChar() << endl;
	}

	MItDependencyNodes audioIt(MFn::kAudio);
	while(!audioIt.isDone())
	{
		MObject obj =  audioIt.item();
		MFnDependencyNode audioNode(obj);
		writeAudioClip(audioNode.object(), "audioStorage");
		audioIt.next();
	}
}

//void x3dExportOrganizer::writeInline(MFnDependencyNode inNode, MString ctField)
void x3dExportOrganizer::writeInline(MObject mObj, MString ctField)
{
	MFnDependencyNode inNode(mObj);
	MStringArray sArr1;
	MStringArray sArr2;
	
	MString nodeName = inNode.name();
	
	bool hasMetadata = checkForMetadata(nodeName);
	if(!isTreeBuilding)
	{
		sArr1 = web3dem.getX3DFields(nodeName, 0);
		sArr2 = web3dem.getX3DFieldValues(nodeName, 0);
	
		sArr1.append("containerField");
		sArr2.append(ctField);
	
		sax3dw.setHasMultiple(true);
		sax3dw.startNode(msInline, nodeName, sArr1, sArr2, hasMetadata);
	}else buildUITreeNode("", "", msInline, "DEF", nodeName);
	if(hasMetadata == true && exEncoding != VRML97ENC)
	{
		treeTabs = treeTabs + 1;
		if(ttabsMax < treeTabs) ttabsMax = treeTabs;
		addMetadataTag(nodeName);
		treeTabs = treeTabs - 1;
		if(!isTreeBuilding) sax3dw.endNode(msInline, nodeName);
	} else if (hasMetadata == true && isTreeBuilding != true) sax3dw.endNode(msInline, nodeName);
}

//void x3dExportOrganizer::writeInlineC(MFnDependencyNode inNode, MString ctField)
void x3dExportOrganizer::writeInlineC(MObject mObj, MString ctField)
{
	MFnDependencyNode inNode(mObj);
	MStringArray sArr1;
	MStringArray sArr2;
	
	MString nodeName = inNode.name();
	
	bool hasMetadata = checkForMetadata(nodeName);
	bool hasBeen  = sax3dw.checkIfHasBeen(nodeName);
	
	if(hasBeen)
	{
		if(!isTreeBuilding)
		{
			sax3dw.useDecl(msInline, nodeName, "containerField", ctField);
		}
		else buildUITreeNode("", "", msInline, "USE", nodeName);
	}
	else
	{
		if(!isTreeBuilding)
		{
			sArr1 = web3dem.getX3DFields(nodeName, 0);
			sArr2 = web3dem.getX3DFieldValues(nodeName, 0);
		
			sArr1.append("containerField");
			sArr2.append(ctField);
		
			sax3dw.setHasMultiple(true);
			sax3dw.startNode(msInline, nodeName, sArr1, sArr2, hasMetadata);
		}
		else buildUITreeNode("", "", msInline, "DEF", nodeName);
		if(hasMetadata == true && exEncoding != VRML97ENC)
		{
			treeTabs = treeTabs + 1;
			if(ttabsMax < treeTabs) ttabsMax = treeTabs;
			addMetadataTag(nodeName);
			treeTabs = treeTabs - 1;
			if(!isTreeBuilding) sax3dw.endNode(msInline, nodeName);
		} else if (hasMetadata == true && isTreeBuilding != true) sax3dw.endNode(msInline, nodeName);
	}
}

void x3dExportOrganizer::outputInlines()
{
	if(!isTreeBuilding)
	{
		sax3dw.msg.set("Exporting Inline Nodes Hidden in a Script Node");
		cout << sax3dw.msg.asChar() << endl;
		cout << " " << endl;
	}
	
	MStringArray inlineNames = getInlineNodeNames();
	unsigned int inLen = inlineNames.length();
	unsigned int i;
	for(i=0;i<inLen;i++){
		MFnDependencyNode inNode = web3dem.getMyDepNodeObj(inlineNames.operator [](i));
		
	}
}

//void x3dExportOrganizer::writeTexture(MFnDependencyNode depNode, MString ctField)
void x3dExportOrganizer::writeTexture(MObject mObj, MString ctField)
{
	MFnDependencyNode depNode(mObj);
	MStringArray fieldValues;
	MStringArray fieldNames;
	MStringArray nodeNameParts;

	MString cNodeName(depNode.name());
	cout << "DepNode Name: " << depNode.name().asChar() << endl;
	MStringArray textureData = getTextureData(cNodeName);//555555
	MString textureType = textureData.operator [](0);
	MFnDependencyNode newTexture(web3dem.getMyDepNodeObj(textureData.operator [](1)));
	MString nodeName = newTexture.name();
	if(nodeName != "")
	{
		bool hasBeen = sax3dw.checkIfHasBeen(nodeName);
		if(hasBeen)
		{
			if(!isTreeBuilding)
			{
				sax3dw.preWriteField(ctField);
				sax3dw.useDecl(textureType, nodeName, "containerField", ctField);
			}
			else
			{
				MString newName(nodeName);
				if(newTexture.typeName() != "file" && newTexture.typeName() != "movie")
				{
					newName.operator +=("_rawkee_export");
				}
				buildUITreeNode("", "", textureType, "USE", newName);
			}
		}
		else
		{
			sax3dw.setAsHasBeen(nodeName);
			cout << "Set As Has Been: " << nodeName << endl;
		
			bool hasMetadata = checkForMetadata(nodeName);
			if(!isTreeBuilding)
			{
				fieldNames = web3dem.getFieldNamesTexture(newTexture, textureType);
				fieldNames.append("containerField");
				fieldValues = web3dem.getFieldValuesTexture(newTexture, textureType);
				fieldValues.append(ctField);
				
				if(hasMetadata) sax3dw.setHasMultiple(true);
				if(textureType.operator !=(msPixelTexture))
				{
					sax3dw.startNode(textureType, nodeName, fieldNames, fieldValues, hasMetadata);
				}
				else
				{
					// 88778877
					if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
					{
						sax3dw.preWriteField(ctField);
						sax3dw.writeRawCode("DEF ");
						sax3dw.writeRawCode(nodeName);
						sax3dw.writeRawCode(" ");
						sax3dw.writeRawCode(textureType);
						sax3dw.writeRawCode(" {\n");
						sax3dw.tabNumber = sax3dw.tabNumber + 1;
						sax3dw.writeTabs();
						sax3dw.writeRawCode("image ");
					}
					else
					{
						sax3dw.writeTabs();
						sax3dw.writeRawCode("<");
						sax3dw.writeRawCode(textureType);
						sax3dw.writeRawCode(" DEF='");
						sax3dw.writeRawCode(nodeName);
						sax3dw.writeRawCode("' image='");
					}
					MImage pixImage;
					pixImage.readFromTextureNode(newTexture.object());
		
					bool adjTex;
					MPlug adjPlug = newTexture.findPlug("adjsize");
					adjPlug.getValue(adjTex);
		
					int xw = 0;
					MPlug xwp = newTexture.findPlug("imgdimw");
					xwp.getValue(xw);
		
					int xh = 0;
					MPlug xhp = newTexture.findPlug("imgdimh");
					xhp.getValue(xh);
		
					if(adjTex)
					{
						MStatus iStat = pixImage.resize(xw, xh, false);
					}
		
					int pixLen = web3dem.getPixelLength(newTexture);
					unsigned int myWidth;
					unsigned int myHeight;
					MStatus status = pixImage.getSize(myWidth, myHeight);
		
					MString mh;
					MString pixels;
					mh.set(myHeight);
					pixels.set(myWidth);
					pixels.operator +=(" ");
					pixels.operator +=(mh);
					pixels.operator +=(" ");
					pixels.operator +=(pixLen);
					sax3dw.writeRawCode(pixels);
					pixels.set("");
		
					unsigned char* myColor = pixImage.pixels();
					unsigned int i;
					unsigned int j;
		
					unsigned char rValue, gValue, bValue, aValue;
					char valueBuffer[17];
		
					cout << "Writing Out Pixel Texture" << endl;
					cout << "Please Be Patient" << endl;
		
					double denom = myHeight;
		
					unsigned int rlimit = 0;
					for(j=0; j<myHeight; j++)
					{
						for(i=0; i<myWidth; i++)
						{
							rValue = myColor[(myHeight-1-j) * myWidth * 4 + i * 4 + 0];
							gValue = myColor[(myHeight-1-j) * myWidth * 4 + i * 4 + 1];
							bValue = myColor[(myHeight-1-j) * myWidth * 4 + i * 4 + 2];
							aValue = myColor[(myHeight-1-j) * myWidth * 4 + i * 4 + 3];
							if(pixLen==1) sprintf(valueBuffer," 0x%02X",rValue);
							else if(pixLen==2) sprintf(valueBuffer," 0x%02X%02X",rValue,gValue);
							else if(pixLen==3) sprintf(valueBuffer," 0x%02X%02X%02X",rValue,gValue,bValue);
							else sprintf(valueBuffer," 0x%02X%02X%02X%02X",rValue,gValue,bValue,aValue);
							pixels.operator +=(valueBuffer);
							if(rlimit == 7)
							{
								if(j < myHeight-1) pixels.operator +=("\n");
								else if(i < myWidth-1) pixels.operator +=("\n");
								sax3dw.writeRawCode(pixels);
								if(!(i == myWidth-1 && j == myHeight-1)) sax3dw.writeTabs();
								pixels.set("");
								rlimit = 0;
							}
							else
							{
								rlimit = rlimit+1;
							}
		
						}
						double perc = j/denom;
						perc = perc * 100;
						cout << "Pixel Texture Export - "<< perc << "% Complete!" << endl;
					}
					sax3dw.writeRawCode(pixels);
					if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
					{
						sax3dw.writeRawCode("\n");
						sax3dw.writeTabs();
						sax3dw.writeRawCode("repeatS ");
						sax3dw.writeRawCode(fieldValues.operator [](fieldValues.length()-3));
						sax3dw.writeRawCode("\n");
						sax3dw.writeTabs();
						sax3dw.writeRawCode("repeatT ");
						sax3dw.writeRawCode(fieldValues.operator [](fieldValues.length()-2));
						sax3dw.writeRawCode("\n");
						sax3dw.tabNumber = sax3dw.tabNumber - 1;
						sax3dw.writeTabs();
						sax3dw.writeRawCode("}\n");
					}
					else
					{
						sax3dw.writeRawCode("' repeatS='");
						sax3dw.writeRawCode(fieldValues.operator [](fieldValues.length()-3));
						sax3dw.writeRawCode("' repeatT='");
						sax3dw.writeRawCode(fieldValues.operator [](fieldValues.length()-2));
						sax3dw.writeRawCode("' containerField='");
						sax3dw.writeRawCode(fieldValues.operator [](fieldValues.length()-1));
						sax3dw.writeRawCode("'/>\n");
					}
				}
		//				cout << "isApp break" << endl;
		
			}
			else
			{
				MString newName(nodeName);
				if(newTexture.typeName() != "file" && newTexture.typeName() != "movie")
				{
					newName.operator +=("_rawkee_export");
				}
				buildUITreeNode("", "", textureType, "DEF", newName);
			}
			if(hasMetadata == true && exEncoding != VRML97ENC)
			{
				treeTabs = treeTabs + 1;
				if(ttabsMax < treeTabs) ttabsMax = treeTabs;
				addMetadataTag(nodeName);
				treeTabs = treeTabs - 1;
				if(!isTreeBuilding) if(textureType.operator !=(msPixelTexture))	sax3dw.endNode(textureType, nodeName);
			}
			else if(hasMetadata == true && isTreeBuilding != true) sax3dw.endNode(textureType, nodeName);
		}
	}
	cout << "Texture Name: " << nodeName << endl;
}

//This method adds ImageTexture that are Maya "file" nodes 
//out the the hidden nodes section of the exported x3d file
//under a dumby MultiTexture node 
void x3dExportOrganizer::outputFiles()
{
	if(!isTreeBuilding)
	{
		sax3dw.msg.set("Getting File Texture Node Information");
		cout << sax3dw.msg.asChar() << endl;
		sax3dw.msg.set(" ");
		cout << sax3dw.msg.asChar() << endl;
	}

//	MStringArray fileNodeNames;
//	MGlobal::executeCommand(MString("ls -sn -et file"), fileNodeNames);
//	unsigned int fnLength = fileNodeNames.length();
//	unsigned int i;
//	for(i=0;i<fnLength;i++)
//	{
	MItDependencyNodes ftIt(MFn::kFileTexture);//6460
	while(!ftIt.isDone())
	{
		MObject obj = ftIt.item();
		MFnDependencyNode depNode(obj);
		writeTexture(depNode.object(), "textureStorage");
		ftIt.next();//tells the iterator to procede to the next object
	}
//	}
}

bool x3dExportOrganizer::checkForAudio(MString aName)
{
	bool hasAudio = false;

	MFnDependencyNode depNode(web3dem.getMyDepNodeObj(aName));
	MPlug aPlug = depNode.findPlug("audioIn");

	MItDependencyGraph depIt(aPlug, MFn::kInvalid, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	bool searching = true;
	while(!depIt.isDone() && searching == true)
	{
		MObject obj = depIt.thisNode();
		MFnDependencyNode mNode(obj);
		if(mNode.typeName() == "audio" || mNode.typeName() == "movie")
		{
			hasAudio = true;
			searching = false;
		}
		depIt.next();
	}
	return hasAudio;
}

//This method simply checks to see if 1) a metadate node
//attribute exists, and 2) if it actually has a metadata
//node name in that attribute
bool x3dExportOrganizer::checkForMetadata(MString aName)
{
	bool hasMetadata = false;

	MFnDependencyNode depNode(web3dem.getMyDepNodeObj(aName));
	MPlug aPlug = depNode.findPlug("x3dMetadataIn");

	MItDependencyGraph depIt(aPlug, MFn::kInvalid, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	bool searching = true;
	while(!depIt.isDone() && searching == true)
	{
		MObject obj = depIt.thisNode();
		MFnDependencyNode mNode(obj);
		if(mNode.typeName() == "x3dMetadataDouble" || mNode.typeName() == "x3dMetadataFloat" || mNode.typeName() == "x3dMetadataInteger" || mNode.typeName() == "x3dMetadataString" || mNode.typeName() == "x3dMetadataSet")
		{
			if(mNode.name().operator !=(depNode.name()))
			{
				hasMetadata = true;
				searching = false;
			}
		}
		depIt.next();
	}
	if(!exMetadata) hasMetadata = false;

	return hasMetadata;
}


//This method simple retreives the x3d node type
//of the node in question
MString x3dExportOrganizer::checkUseType(MString nodeName)
{
	//First we find out what the Maya node type is by
	//using the MEL nodeType command and passing it
	//the name of the Maya node.
	MFnDependencyNode depNode(web3dem.getMyDepNodeObj(nodeName));
	MString nodeType = depNode.typeName();

	//Then we compare it to the list of known maya node types
	//and return the corresponding X3D node type
	if(nodeType == x3dMetadataDouble::typeName) return msMetaD;
	if (nodeType == x3dMetadataFloat::typeName) return msMetaF;
	if (nodeType == x3dMetadataInteger::typeName) return msMetaI;
	if (nodeType == x3dMetadataSet::typeName) return msMetaSe;
	if (nodeType == x3dMetadataString::typeName) return msMetaSt;
	if (nodeType == x3dBox::typeName) return msBox;///new ones
	if (nodeType == x3dCollision::typeName) return msCollision;
	if (nodeType == x3dColor::typeName) return msColor;
	if (nodeType == x3dColorRGBA::typeName) return msColorRGBA;
	if (nodeType == x3dCone::typeName) return msCone;
	if (nodeType == x3dCoordinate::typeName) return msCoordinate;
	if (nodeType == x3dCylinder::typeName) return msCylinder;
	if (nodeType == x3dGroup::typeName) return msGroup;
	if (nodeType == x3dAnchor::typeName) return msAnchor;
	if (nodeType == x3dBillboard::typeName) return msBillboard;
	if (nodeType == x3dInline::typeName) return msInline;
	if (nodeType == x3dIndexedFaceSet::typeName) return msIndexedFaceSet;
	if (nodeType == "lodGroup") return msLOD;
	if (nodeType == x3dNavigationInfo::typeName) return msNavigationInfo;
	if (nodeType == x3dNormal::typeName) return msNormal;

	if (nodeType == x3dOrientationInterpolator::typeName) return msOrientationInterpolator;
	if (nodeType == x3dPositionInterpolator::typeName) return msPositionInterpolator;
	if (nodeType == x3dNormalInterpolator::typeName) return msNormalInterpolator;
	if (nodeType == x3dCoordinateInterpolator::typeName) return msCoordinateInterpolator;
	if (nodeType == x3dColorInterpolator::typeName) return msColorInterpolator;
	if (nodeType == x3dScalarInterpolator::typeName) return msScalarInterpolator;
	if (nodeType == x3dBooleanSequencer::typeName) return msBooleanSequencer;
	if (nodeType == x3dIntegerSequencer::typeName) return msIntegerSequencer;

	if (nodeType == x3dScript::typeName) return msScript;
	if (nodeType == x3dSphere::typeName) return msSphere;
	if (nodeType == x3dSwitch::typeName) return msSwitch;
	if (nodeType == x3dTextureCoordinate::typeName) return msTextureCoordinate;
	if (nodeType == x3dTimeSensor::typeName) return msTimeSensor;
	if (nodeType == x3dTouchSensor::typeName) return msTouchSensor;

	if (nodeType == x3dProximitySensor::typeName) return msProximitySensor;
	if (nodeType == x3dVisibilitySensor::typeName) return msVisibilitySensor;

	if (nodeType == x3dPlaneSensor::typeName) return msPlaneSensor;
	if (nodeType == x3dSphereSensor::typeName) return msSphereSensor;
	if (nodeType == x3dCylinderSensor::typeName) return msCylinderSensor;
	if (nodeType == x3dStringSensor::typeName) return msStringSensor;
	if (nodeType == x3dKeySensor::typeName) return msKeySensor;
	if (nodeType == x3dLoadSensor::typeName) return msLoadSensor;

	if (nodeType == x3dBooleanToggle::typeName) return msBooleanToggle;
	if (nodeType == x3dBooleanFilter::typeName) return msBooleanFilter;
	if (nodeType == x3dBooleanTrigger::typeName) return msBooleanTrigger;
	if (nodeType == x3dIntegerTrigger::typeName) return msIntegerTrigger;
	if (nodeType == x3dTimeTrigger::typeName) return msTimeTrigger;

	if (nodeType == "mesh") return msShape;
	if (nodeType == "shadingEngine") return msAppearance;
	if (nodeType == "lambert") return msMaterial;
	if (nodeType == "blinn") return msMaterial;
	if (nodeType == "phong") return msMaterial;
	if (nodeType == "phongE") return msMaterial;
	if (nodeType == "movie") return msMovieTexture;
	if (nodeType == "file") return msImageTexture;
	if (nodeType == "buldge") return msImageTexture;
	if (nodeType == "checker") return msImageTexture;
	if (nodeType == "cloth") return msImageTexture;
	if (nodeType == "fractal") return msImageTexture;
	if (nodeType == "grid") return msImageTexture;
	if (nodeType == "noise") return msImageTexture;
	if (nodeType == "water") return msImageTexture;
	if (nodeType == "layeredTexture") return msMultiTexture;
	if (nodeType == "place2dTexture") return msTextureTransform;
	if (nodeType == "audio") return msAudioClip;
	if (nodeType == "x3dSound") return msSound;
	if (nodeType == x3dWorldInfo::typeName) return msWorldInfo;
	//msMultiTextureTransform
	if (nodeType == "transform") return msTransform;
	if (nodeType == "cameraShape") return msViewpoint;
	if (nodeType == "directionalLightShape") return msDirectionalLight;
	if (nodeType == "spotLightShape") return msSpotLight;
	if (nodeType == "pointLightShape") return msPointLight;
	return msEmpty;
}

//Needs much re-writes, it simply checks to see if the object
//has a node name. If it does, we assume that it is a 
//texture node and return a true
bool x3dExportOrganizer::checkForTexture(bool isMulti, MObject texNode, MObject mTexNode)
{
	bool hasTex = false;

	if(isMulti == true)
	{
		MFnDependencyNode depFn(mTexNode);
		MString tName = depFn.name();
		if(tName != msEmpty) hasTex = true;
	}
	else
	{
		MFnDependencyNode depFn(texNode);
		MString tName = depFn.name();
		if(tName != msEmpty) hasTex = true;
	}

	return hasTex;
}

//This method sets a string value for the MString object
//returned base on the int passed to the method. It is used
//to set a containerField value. At this point it is not 
//necessary to pass the nodeName. Might remove it in a 
//future version.
MString x3dExportOrganizer::getCFValue(int value)
{
	MString contVal("");
	switch(value)
	{
		case 1:
			contVal.set("appearance");
			break;
		case 2:
			contVal.set("backTexture");
			break;
		case 3:
			contVal.set("bottomTexture");
			break;
		case 4:
			contVal.set("children");
			break;
		case 5:
			contVal.set("color");
			break;
		case 6:
			contVal.set("controlPoint");
			break;
		case 7:
			contVal.set("controlPoints");
			break;
		case 8:
			contVal.set("coord");
			break;
		case 9:
			contVal.set("crossSectionCurve");
			break;
		case 10:
			contVal.set("data");
			break;
		case 11:
			contVal.set("displacers");
			break;
		case 12:
			contVal.set("fillProperties");
			break;
		case 13:
			contVal.set("fontStyle");
			break;
		case 14:
			contVal.set("frontTexture");
			break;
		case 15:
			contVal.set("geometry");
			break;
		case 16:
			contVal.set("geoOrigin");
			break;
		case 17:
			contVal.set("joints");
			break;
		case 18:
			contVal.set("leftTexture");
			break;
		case 19:
			contVal.set("lineProperties");
			break;
		case 20:
			contVal.set("material");
			break;
		case 21:
			contVal.set("metadata");
			break;
		case 22:
			contVal.set("normal");
			break;
		case 23:
			contVal.set("profileCurve");
			break;
		case 24:
			contVal.set("proxy");
			break;
		case 25:
			contVal.set("rightTexture");
			break;
		case 26:
			contVal.set("rootNode");
			break;
		case 27:
			contVal.set("segments");
			break;
		case 28:
			contVal.set("sites");
			break;
		case 29:
			contVal.set("skeleton");
			break;
		case 30:
			contVal.set("skin");
			break;
		case 31:
			contVal.set("skinCoord");
			break;
		case 32:
			contVal.set("skinNormal");
			break;
		case 33:
			contVal.set("source");
			break;
		case 34:
			contVal.set("texCoord");
			break;
		case 35:
			contVal.set("texture");
			break;
		case 36:
			contVal.set("textureTransform");
			break;
		case 37:
			contVal.set("topTexture");
			break;
		case 38:
			contVal.set("trajectoryCurve");
			break;
		case 39:
			contVal.set("trimmingContour");
			break;
		case 40:
			contVal.set("value");
			break;
		case 41:
			contVal.set("viewpoints");
			break;
		case 42:
			contVal.set("watchList");
			break;

		case 101:
			contVal.set("choice");
			break;
		case 102:
			contVal.set("level");
			break;
		default:
			contVal.set("");
			break;

	}

	return contVal;
}

//****************************************
//****************************************
//****************************************
//  Jan 31, 2005
//  MEL Procedure Conversions to C++
//****************************************
//****************************************
//****************************************

MStringArray x3dExportOrganizer::x3dMetadataNames(unsigned int metaChoice)
{
	MSelectionList tempList;
	tempList.clear();
	MItDependencyNodes mDataIt(MFn::kInvalid);
	while(!mDataIt.isDone())
	{
		MObject obj = mDataIt.item();
		MFnDependencyNode depNode(obj);
//		bool isRef = isReferenceNode(depNode.name());
//		if(isRef != true)
//		{
			switch(metaChoice)
			{
				case 1:
					if(depNode.typeName() == "x3dMetadataFloat") tempList.add(depNode.name());
					break;
				case 2:
					if(depNode.typeName() == "x3dMetadataInteger") tempList.add(depNode.name());
					break;
				case 3:
					if(depNode.typeName() == "x3dMetadataSet") tempList.add(depNode.name());
					break;
				case 4:
					if(depNode.typeName() == "x3dMetadataString") tempList.add(depNode.name());
					break;
				default:
					if(depNode.typeName() == "x3dMetadataDouble") tempList.add(depNode.name());
					break;
			}
//		}
		mDataIt.next();//tells the iterator to procede to the next object
	}

	MStringArray newArray;
	tempList.getSelectionStrings(newArray);
	return newArray;

}

MPlug x3dExportOrganizer::findMyPlug(MString nodeName, MString plugName)
{
	MStatus nStatus;
	MSelectionList tempList;
	tempList.clear();
	tempList.add(nodeName);
	MItSelectionList newMItSel(tempList);
	MObject tObject;
	newMItSel.getDependNode(tObject);
	MFnDependencyNode newDepFn(tObject);

	MPlug aPlug;
	aPlug = newDepFn.findPlug(plugName, &nStatus);
	return aPlug;
}

MStringArray x3dExportOrganizer::getMetadataAtts(MString mName)
{
	cout << "Get Metadata Atts" << endl;
	MStringArray newArray;

	MFnDependencyNode depNode(web3dem.getMyDepNodeObj(mName));

	MPlug aPlug = depNode.findPlug("x3dMetadataIn");
	MString metaNodeName("");
	MItDependencyGraph depIt(aPlug, MFn::kInvalid, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	bool searching = true;
	MFnDependencyNode metaNode;
	while(!depIt.isDone() && searching == true)
	{
		MObject obj = depIt.thisNode();
		MFnDependencyNode mNode(obj);
		if(mNode.typeName() == "x3dMetadataDouble" || mNode.typeName() == "x3dMetadataFloat" || mNode.typeName() == "x3dMetadataInteger" || mNode.typeName() == "x3dMetadataString" || mNode.typeName() == "x3dMetadataSet")
		{
			if(mNode.name() != mName)
			{
				metaNode.setObject(obj);
				metaNodeName = mNode.name();
				searching = false;
			}
		}
//		cout << "In while loop" << endl;
		depIt.next();
	}
	newArray.append(metaNodeName);

	if(!isTreeBuilding)
	{
		MString aValue("");
		aPlug = findMyPlug(mName, "name");
		aPlug.getValue(aValue);

		MString nameString("");
		if(exEncoding == X3DVENC && aValue.operator !=("")) nameString.operator +=("\"");
		nameString.operator +=(aValue);
		if(exEncoding == X3DVENC && aValue.operator !=("")) nameString.operator +=("\"");
		newArray.append(nameString);

		aPlug = findMyPlug(mName, "reference");
		aPlug.getValue(aValue);

		MString refString("");
		if(exEncoding == X3DVENC && aValue.operator !=("")) refString.operator +=("\"");
		refString.operator +=(aValue);
		if(exEncoding == X3DVENC && aValue.operator !=("")) refString.operator +=("\"");
		newArray.append(refString);

		aPlug = metaNode.findPlug("value_cc");
	
		unsigned int valInt;
		int tValue;
		aPlug.getValue(tValue);


		if(tValue < 1 || depNode.typeName() == "x3dMetadataSet") newArray.append("");
		else
		{
			MString valString("");
			valInt = tValue;

			if(exEncoding == X3DVENC && tValue > 1) valString.operator +=("[ ");
			if(depNode.typeName() == "x3dMetadataInteger")
			{
				MString hString = web3dem.getMFInt32Metadata("value", depNode);
				valString.operator +=(hString);
			}
			else if(depNode.typeName() == "x3dMetadataFloat")
			{
				MString hString = web3dem.getMFFloatMetadata("value", depNode);
				valString.operator +=(hString);
			}
			else if(depNode.typeName() == "x3dMetadataDouble")
			{
				MString hString = web3dem.getMFDoubleNonScript("value", depNode);
				valString.operator +=(hString);
			}
			else if(depNode.typeName() == "x3dMetadataString")
			{
				MString hString = web3dem.getMFStringNonScript("value", depNode);
				valString.operator +=(hString);
			}

			if(exEncoding == X3DVENC && tValue > 1) valString.operator +=(" ]");
			newArray.append(valString);
		}
	}
//	cout << "End of Atts" << endl;
	return newArray;
}

bool x3dExportOrganizer::isReferenceNode(MString nodeName)
{
	bool refNode = false;
	MStringArray files;
	MFileIO::getReferences(files);
	
	unsigned int fLen = files.length();
	unsigned int i;
	for(i=0;i<fLen;i++)
	{
		MStringArray nodes;
		MFileIO::getReferenceNodes(files.operator [](i), nodes);

		unsigned int nLen = nodes.length();
		unsigned int j;
		for(j=0;j<nLen;j++) if(nodes.operator [](j).operator ==(nodeName)) refNode = true;
	}

	return refNode;
}

bool x3dExportOrganizer::isInHiddenLayer(MString nodeName)
{
	bool hLayer = false;
	MFnDependencyNode depFn(web3dem.getMyDepNodeObj(nodeName));
	MPlug dOver = depFn.findPlug("drawOverride");
		
	MItDependencyGraph depIt(dOver, MFn::kInvalid, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kPlugLevel);
	bool searching = true;
	while(!depIt.isDone() && searching == true)
	{
		MObject obj = depIt.thisNode();
		MFnDependencyNode depNode(obj);
		if(depNode.typeName() == "displayLayer")
		{
			MPlug dtPlug = depNode.findPlug("displayType");
			MPlug visPlug = depNode.findPlug("visibility");
			int dtInt = 0;
			int visInt = 0;
			dtPlug.getValue(dtInt);
			visPlug.getValue(visInt);
			if(dtInt!=0 || visInt!=1) hLayer = true;
			searching = false;
		}
		depIt.next();
	}
	return hLayer;
}

MObjectArray	x3dExportOrganizer::getWatchedNodes(MString nodeName)
{	
	MObjectArray oArray;
	MFnDependencyNode depNode(web3dem.getMyDepNodeObj(nodeName));
	if(depNode.typeName().operator ==(X3D_LOADSENSOR))
	{
		MPlug imPlug = depNode.findPlug("images");
		MPlug moPlug = depNode.findPlug("movies");
		MPlug auPlug = depNode.findPlug("audios");
		MPlug inPlug = depNode.findPlug("inlines");

		MString imStr;
		MString moStr;
		MString auStr;
		MString inStr;

		imPlug.getValue(imStr);
		moPlug.getValue(moStr);
		auPlug.getValue(auStr);
		inPlug.getValue(inStr);

		MStringArray imArr;
		MStringArray moArr;
		MStringArray auArr;
		MStringArray inArr;

		imStr.split('*', imArr);
		moStr.split('*', moArr);
		auStr.split('*', auArr);
		inStr.split('*', inArr);
		int i;
		for(i=0; i<imArr.length();i++)
		{
//			MFnDependencyNode tdep = web3dem.findNonExportTexture(imArr.operator [](i));
			MFnDependencyNode tdep(web3dem.findNonExportTexture(imArr.operator [](i)));
			cout << "TDEP: " << tdep.name().asChar() << endl;
			if(tdep.typeName() != "file")
			{
				if(!isTreeBuilding)
				{
					MString tStr(imArr.operator [](i));
					tStr.operator +=("_rawkee_export");
					MFnDependencyNode tdep2(web3dem.getMyDepNodeObj(tStr));
					tdep.setObject(tdep2.object());
				}
			}
			oArray.append(tdep.object());
		}

		for(i=0;i<moArr.length();i++)
		{
			MFnDependencyNode tdep(web3dem.getMyDepNodeObj(moArr.operator [](i)));
			oArray.append(tdep.object());
		}

		for(i=0;i<auArr.length();i++)
		{
			MFnDependencyNode tdep(web3dem.getMyDepNodeObj(auArr.operator [](i)));
			oArray.append(tdep.object());
		}

		for(i=0;i<inArr.length();i++)
		{
			MFnDependencyNode tdep(web3dem.getMyDepNodeObj(inArr.operator [](i)));
			oArray.append(tdep.object());
		}
	}
	return oArray;
}
double		x3dExportOrganizer::getFrameRate()
{
	MAnimControl aControl;
	MTime cTime = aControl.currentTime();
	double retDouble = 24;
	switch(cTime.uiUnit())
	{
		case 5: 
			retDouble = 15;
			break;

		case 6:
			retDouble = 24;
			break;

		default:
			retDouble = 24;
			break;
	}
	return retDouble;
}

MStringArray x3dExportOrganizer::getInlineNodeNames()
{
	MStringArray nodes;
	MItDag itDag(MItDag::kDepthFirst, MFn::kInvalid);

	while(!itDag.isDone())
	{
		MObject tItem = itDag.item();
		MFnDependencyNode nNode(tItem);
		if(nNode.typeName() == "x3dInline")
		{
			bool hLayer = isInHiddenLayer(nNode.name());
			if(!hLayer)
			{
				unsigned int nodLen = nodes.length();
				unsigned int i;
				bool hasFound = false;
				for(i=0;i<nodLen;i++)
				{
					if(nNode.name() == nodes.operator [](i)) hasFound = true;
				}
				if(!hasFound) nodes.append(nNode.name());
			}
		}
		itDag.next();
	}

	return nodes;
}

void x3dExportOrganizer::setAdditionalComps()
{
	sax3dw.additionalComps.clear();
	unsigned int acVal = 0;
	if(exRigidBody == true)
	{
		sax3dw.additionalComps.append("xj3d_RigidBodyPhysics");
		sax3dw.additionalCompsLevels.append("2");
		acVal = acVal + 1;
	}
	if(exHAnim == true)
	{
		sax3dw.additionalComps.append("H-Anim");
		sax3dw.additionalCompsLevels.append("1");
		acVal = acVal + 1;
	}
	if(exIODevice == true)
	{
		sax3dw.additionalComps.append("xj3d_IODevice");
		sax3dw.additionalCompsLevels.append("2");
		acVal = acVal + 1;
	}
}

//bool x3dExportOrganizer::getRigidBodyState(MFnDagNode parentDagFn)
bool x3dExportOrganizer::getRigidBodyState(MObject mObj)
{
	MFnDagNode parentDagFn(mObj);
	unsigned int clen = parentDagFn.childCount();
	unsigned int i = 0;
	while(i<clen)
	{
		MObject achild = parentDagFn.child(i);
		MFnDagNode aNode(achild);
		cout << aNode.typeName() << endl;
		if(aNode.typeName().operator ==("rigidBody"))
		{
			return true;
		}
		else i = i+1;
	}
	return false;
}

/*
MFnDagNode x3dExportOrganizer::getRigidBodyNode(MFnDagNode parentDagFn)
{
	MFnDagNode rigidBodyNode;
	unsigned int clen = parentDagFn.childCount();
	unsigned int i = 0;
	while(i<clen)
	{
		MObject achild = parentDagFn.child(i);
		MFnDagNode aNode(achild);
		if(aNode.typeName() == "rigidBody") return aNode;
		else i = i+1;
	}
	return rigidBodyNode;
}
*/

MObject x3dExportOrganizer::getRigidBodyNode(MObject mObj)
{
	MFnDagNode parentDagFn(mObj);
	MFnDagNode rigidBodyNode;
	unsigned int clen = parentDagFn.childCount();
	unsigned int i = 0;
	while(i<clen)
	{
		MObject achild = parentDagFn.child(i);
		MFnDagNode aNode(achild);
		if(aNode.typeName() == "rigidBody") return aNode.object();
		else i = i+1;
	}
	return rigidBodyNode.object();
}

//bool x3dExportOrganizer::getCharacterState(MFnDependencyNode meshNode)
bool x3dExportOrganizer::getCharacterState(MObject mObj)
{
	MFnDependencyNode meshNode(mObj);
	bool cState = false;
	MPlug aPlug = meshNode.findPlug("inMesh");
	MItDependencyGraph jointIter(aPlug, MFn::kJoint, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
	while(!jointIter.isDone() && cState == false)
	{
		MFnDependencyNode lsTest(jointIter.thisNode());
		if(lsTest.typeName() == "joint") cState = true;
		jointIter.next();
	}

	if(exHAnim == false) cState = false;
	return cState;
}

/*
void x3dExportOrganizer::buildMeshDagList(MFnDagNode root)
{
	if(root.typeName().operator ==("mesh"))
	{
		if(!root.isIntermediateObject())
		{
			avatarMeshNames.append(root.name());

			MDagPath dagpath;
			root.getPath(dagpath);
			avatarDagPaths.append(dagpath);
		}
	}
	unsigned int i;
	for(i=0;i<root.childCount();i++)
	{
		MFnDagNode newDag(root.child(i));
		buildMeshDagList(newDag);
	}
}
*/

void x3dExportOrganizer::processDynamics()
{
	MStringArray gFields;
	MStringArray gValues;
	sax3dw.startNode(msGroup, "", gFields, gValues, true);
	outputCollidableShapes();
	sax3dw.endNode(msGroup, "");
	
	MStringArray rBodySolvers;
	MGlobal::executeCommand("ls -type rigidSolver", rBodySolvers);

	unsigned int i;
	for(i=0;i<rBodySolvers.length();i++)
	{
		MFnDependencyNode depNode(web3dem.getMyDepNodeObj(rBodySolvers.operator [](i)));
		processRigidBody(depNode.object());
	}
}

//void x3dExportOrganizer::processRigidBody(MFnDependencyNode depNode)
void x3dExportOrganizer::processRigidBody(MObject mObj)
{
		MFnDependencyNode depNode(mObj);
		MString sName(depNode.name());
		sName.operator +=("_CollisionSensor");

		MString ccName(depNode.name());
		ccName.operator +=("_CollisionCollection");

		if(isTreeBuilding)
		{
			buildUITreeNode(depNode.typeName(), depNode.name(), msRigidBodyCollection, "DEF", depNode.name());
				treeTabs = treeTabs + 1;
				if(checkForMetadata(depNode.name())) addMetadataTag(depNode.name());
				processRBBodies(depNode.object());
				processRBJoints(depNode.object());
				processRBCollider(depNode.object());
				treeTabs = treeTabs - 1;
			buildUITreeNode(depNode.typeName(), depNode.name(), msCollisionSensor, "DEF", sName);
				treeTabs = treeTabs+5;
				buildUITreeNode(depNode.typeName(), depNode.name(), msCollisionCollection, "USE", ccName);
				treeTabs = treeTabs -5;
		}
		else
		{
			MStringArray rbc1 = web3dem.getRBCFields();
			MStringArray rbc2 = web3dem.getRBCFieldValues(depNode, 0);
			rbc1.append("containerField");
			rbc2.append("");
			sax3dw.startNode(msRigidBodyCollection, depNode.name(), rbc1, rbc2, true);
				if(checkForMetadata(depNode.name())) addMetadataTag(depNode.name());
				processRBBodies(depNode.object());
				processRBJoints(depNode.object());
				processRBCollider(depNode.object());
			sax3dw.endNode(msRigidBodyCollection, depNode.name());

			MStringArray cs1 = web3dem.getCollisionSensorFields();
			MStringArray cs2 = web3dem.getCollisionSensorFieldValues(depNode);
			sax3dw.startNode(msCollisionSensor, sName, cs1, cs2, true);
				sax3dw.preWriteField("collidables");
				sax3dw.useDecl(msCollisionCollection, ccName, "containerField", "collidables");
			sax3dw.endNode(msCollisionSensor, sName);
		}
}

//void x3dExportOrganizer::processRBBodies(MFnDependencyNode depNode)
void x3dExportOrganizer::processRBBodies(MObject mObj)
{
	MFnDependencyNode depNode(mObj);
	if(!isTreeBuilding)
	{
		sax3dw.preWriteField("bodies");
		sax3dw.writeSBracket();
	}
 
	MPlug gForce = depNode.findPlug("generalForce");
	MItDependencyGraph rbItDep(gForce, MFn::kRigid, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel); //(MItDag::kDepthFirst, MFn::kRigid);
	while(!rbItDep.isDone())
	{
		MObject rbObject = rbItDep.thisNode();
		MFnDagNode rbDag(rbObject);
		MObject rbpObject = rbDag.parent(0);
		MFnDagNode rbpDag(rbpObject);
		MPlug pAct = rbDag.findPlug("active");
		bool isActive = true;
		pAct.getValue(isActive);

		if(isActive == true)
		{
			if(isTreeBuilding)
			{
				unsigned int clen = rbpDag.childCount();
				unsigned int i;
				for(i=0;i<clen;i++)
				{
					MObject achild = rbpDag.child(i);
					MFnDagNode aNode(achild);
					if(aNode.typeName() == "mesh")
					{
						MString rbName("rigidBody_");
						rbName.operator +=(aNode.name());

						if(sax3dw.checkIfHasBeen(rbName))
						{
							buildUITreeNode("", "", msRigidBody, "USE", rbName);
						}
						else
						{
							buildUITreeNode("", "", msRigidBody, "DEF", rbName);
							treeTabs = treeTabs+5;
							writeCollidableShape(aNode.object(), rbpDag.object(), rbDag.object(), "geometry");
							treeTabs = treeTabs-5;
						}
					}
				}
			}
			else
			{
				unsigned int clen = rbpDag.childCount();
				unsigned int i;
				for(i=0;i<clen;i++)
				{
					MObject achild = rbpDag.child(i);
					MFnDagNode aNode(achild);
					if(aNode.typeName() == "mesh")
					{
						MString rbName("rigidBody_");
						rbName.operator +=(aNode.name());

						MStringArray rbArray1 = web3dem.getRigidBodyFields();
						MStringArray rbArray2 = web3dem.getRigidBodyFieldValues(rbDag, rbpDag);
						
						rbArray1.append("containerField");
						rbArray2.append("bodies");
						sax3dw.setHasMultiple(true);
						if(sax3dw.checkIfHasBeen(rbName))
						{
							sax3dw.useDecl(msRigidBody, rbName, "containerField", "bodies");
						}
						else
						{
							sax3dw.startNode(msRigidBody, rbName, rbArray1, rbArray2, true);
					//Geometry
					//				sax3dw.setHasMultiple(true);
									writeCollidableShape(aNode.object(), rbpDag.object(), rbDag.object(), "geometry");
					//End Geometry
							sax3dw.endNode(msRigidBody, rbName);
						}
					}
				}
			}
		}
		cout << rbpDag.name().asChar() << endl;
		rbItDep.next();
	}
	if(!isTreeBuilding) sax3dw.writeEBracket();
}

//Not Yet Implemented as of 1.2.0
//void x3dExportOrganizer::processRBJoints(MFnDependencyNode depNode)
void x3dExportOrganizer::processRBJoints(MObject mObj)
{
}

//void x3dExportOrganizer::processRBCollider(MFnDependencyNode depNode)
void x3dExportOrganizer::processRBCollider(MObject mObj)
{
	MFnDependencyNode depNode(mObj);
	MString ccName(depNode.name());
	ccName.operator +=("_CollisionCollection");
	
	bool hasBeen = sax3dw.checkIfHasBeen(ccName);
	if(hasBeen)
	{	
		if(isTreeBuilding) buildUITreeNode(depNode.typeName(), depNode.name(), msCollisionCollection, "USE", ccName);
		else sax3dw.useDecl(msCollisionCollection, ccName, "containerField", "collider");
	}
	else
	{
		if(isTreeBuilding)
		{
			buildUITreeNode(depNode.typeName(), depNode.name(), msCollisionCollection, "DEF", ccName);
			treeTabs = treeTabs+5;
		}
		else
		{
			MStringArray ccArray1 = web3dem.getCollisionCollectionFields();
			MStringArray ccArray2 = web3dem.getCollisionCollectionFieldValues(depNode);

			ccArray1.append("containerField");
			ccArray2.append("collider");
			sax3dw.startNode(msCollisionCollection, ccName, ccArray1, ccArray2, true);
				sax3dw.preWriteField("collidables");
				sax3dw.writeSBracket();
		}

	MPlug gForce = depNode.findPlug("generalForce");
	MItDependencyGraph rbItDep(gForce, MFn::kRigid, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel); //(MItDag::kDepthFirst, MFn::kRigid);
		while(!rbItDep.isDone())
		{
			MObject rbObject = rbItDep.thisNode();
			MFnDagNode rbDag(rbObject);
			MObject rbpObject = rbDag.parent(0);
			MFnDagNode rbpDag(rbpObject);
			MPlug pAct = rbDag.findPlug("active");
			bool isActive = true;
			pAct.getValue(isActive);

			bool hasUseCS = false;
//			if(!isActive)
//			{
				unsigned int clen = rbpDag.childCount();
//				if(clen > 1)
				if(clen == -1)
				{
					MString cSpace(rbpDag.name());
					cSpace.operator +=("_CollisionSpace");
					hasUseCS = sax3dw.checkIfHasBeen(cSpace);

					if(isTreeBuilding)
					{
						if(hasUseCS)
						{
							buildUITreeNode(rbpDag.typeName(), rbpDag.name(), msCollisionSpace, "USE", cSpace);
						}
						else
						{
							buildUITreeNode(rbpDag.typeName(), rbpDag.name(), msCollisionSpace, "DEF", cSpace);
							treeTabs = treeTabs+5;
							unsigned int i;
							for(i=0;i<clen;i++)
							{
								MObject achild = rbpDag.child(i);
								MFnDagNode aNode(achild);
								if(aNode.typeName() == "mesh") writeCollidableShape(aNode.object(), rbpDag.object(), rbDag.object(), "collidables");
							}
							treeTabs = treeTabs-5;
						}
					}
					else
					{
						if(hasUseCS) sax3dw.useDecl(msCollisionSpace, cSpace, "containerField", "collidables");
						else 
						{
							MStringArray cspace1 = web3dem.getCollisionSpaceFields();
							cspace1.append("containerField");
							MStringArray cspace2 = web3dem.getCollisionSpaceFieldValues(rbpDag);
							cspace2.append("collidables");
							sax3dw.startNode(msCollisionSpace, cSpace, cspace1, cspace2, true);
								sax3dw.preWriteField("collidables");
								sax3dw.writeSBracket();
								unsigned int i;
								for(i=0;i<clen;i++)
								{
//									sax3dw.setHasMultiple(true);
									MObject achild = rbpDag.child(i);
									MFnDagNode aNode(achild);
									if(aNode.typeName() == "mesh")
									{
//										sax3dw.setHasMultiple(true);
										writeCollidableShape(aNode.object(), rbpDag.object(), rbDag.object(), "collidables");
									}
								}
								sax3dw.writeEBracket();
							sax3dw.endNode(msCollisionSpace, cSpace);
						}
					}
				}
				else
				{
					unsigned int i;
					for(i=0;i<clen;i++)
					{
						MObject achild = rbpDag.child(i);
						MFnDagNode aNode(achild);
						if(!isTreeBuilding) sax3dw.setHasMultiple(true);
						if(aNode.typeName() == "mesh") writeCollidableShape(aNode.object(), rbpDag.object(), rbDag.object(), "collidables");
					}
				}
			//}
			rbItDep.next();
		}

		if(isTreeBuilding)
		{
			treeTabs = treeTabs - 1;
		}
		else
		{
				sax3dw.writeEBracket();
			sax3dw.endNode(msCollisionCollection, ccName);
		}
	}	
}

void	x3dExportOrganizer::processScripts()
{
	MStringArray sArray;
	MGlobal::executeCommand("ls -type x3dScript", sArray);

	unsigned int i;
	for(i=0;i<sArray.length();i++)
	{
		cout << sArray.operator [](i) << endl;
		bool isHid = isInHiddenLayer(sArray.operator [](i));
		if(!isHid)
		{
			MFnDependencyNode dpNode(web3dem.getMyDepNodeObj(sArray.operator [](i)));
			MDagPath sdagp = MDagPath::getAPathTo(dpNode.object());
			MFnDagNode tDag(sdagp);
			MFnDagNode dgNode(tDag.object());
			writeScript(dgNode.object(), "");
		}
	}
}

//bool	x3dExportOrganizer::checkForAvatar(MFnDagNode dagNode)
bool	x3dExportOrganizer::checkForAvatar(MObject mObj)
{
	MFnDagNode dagNode(mObj);

	bool hasAvatar = false;
	unsigned int cdn = dagNode.childCount();
	
	unsigned int i;
	for(i=0;i<cdn;i++)
	{
		if(hasAvatar == false)
		{
			MObject mobj = dagNode.child(i);
			MFnDependencyNode depNode(mobj);
			
			if(depNode.typeName().operator ==("joint")) hasAvatar = true;
			else if(depNode.typeName().operator ==("mesh"))
			{
				MPlug inPlug = depNode.findPlug("inMesh");
				MItDependencyGraph depIt(inPlug, MFn::kJoint, MItDependencyGraph::kUpstream, MItDependencyGraph::kDepthFirst, MItDependencyGraph::kNodeLevel);
				
				while(!depIt.isDone() && hasAvatar == false)
				{
					MObject aObj = depIt.thisNode();
					MFnDependencyNode depANode(aObj);
					if(depANode.typeName().operator ==("joint")) hasAvatar = true;
					depIt.next();
				}
			}
		}
	}

	return hasAvatar;
}
