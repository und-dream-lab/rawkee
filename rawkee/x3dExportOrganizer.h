#ifndef __X3DEXPORTORGANIZER_H
#define __X3DEXPORTORGANIZER_H

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

// File: x3dExportOrganizer.h
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#if MAYA_API_VERSION >= 600 //For versions of Maya 6.0 and higher
#include <iostream>
#include <fstream>
#else //For versions of Maya below 6.0
#include "iostream.h"
#include "fstream.h"
#endif//Maya Versions

#include "stdio.h"
#ifdef _WIN32
#include "direct.h"
#else
#include <sys/types.h>
#include <sys/stat.h>
#endif

#if MAYA_API_VERSION >= 600 //For versions of Maya 6.0 and higher
using namespace std;
#endif

class x3dExportOrganizer {
public:
		x3dExportOrganizer();
		virtual ~x3dExportOrganizer();

		static	MObject			worldRoot;

//		static	MString			exTextureFormat;


//				ostream*		newFile;
		static	MString			fileName;
		static	MString			localPath;
		static	MString			localImagePath;
		static	MString			localAudioPath;
		static	MString			localInlinePath;

		static	MString			tempTexturePath;

		static	MString			exBaseURL;
		static	MString			exTextureURL;
		static	MString			exAudioURL;
		static	MString			exInlineURL;
		

		static	MString			getTextureDir;
		static	MString			getAudioDir;
		static	MString			getInlineDir;

		static	MString			externLaunchCMD;

		static	MStringArray	avatarMeshNames;
		static	MDagPathArray	avatarDagPaths;

		static  MStringArray	mayaArray;
		static	MStringArray	x3dArray;
		static	MString	x3dTreeStrings;
		static	MString x3dTreeDelStrings;

		static bool hasCoord;
		static bool hasNormal;
		static bool hasColor;
		static bool hasTexCoord;
		static bool hasGeometry;
		static bool hasTexture;
		static bool useRelURL;
		static bool useRelURLW;
		
		static bool asSyblings;
		static bool useEmpties;

//		static bool internalPixel;
//		static bool externalPixel;

		static bool isTreeBuilding;
		static bool hasPassed;
		static int	updateMethod;
		static bool isDone;

		static bool fileOverwrite;

		static MStringArray textureNames;

		static int	exEncoding;
		static int	exMetadata;
		static int	exTextures;
		static int	exAudio;
		static int  exInline;
		static int	launchExtern;
//		static int	x3dTextureForInt;
		static int	conMedia;
//		static int	adjTexture;
//		static int	saveMayaTex;

//		static int	cpvNonD;
		static int	npvNonD;
		static float caGlobalValue;
//		static int	solidGlobalValue;
//		static int x3dTextureWidth;
//		static int x3dTextureHeight;
		static unsigned int treeTabs;
		static unsigned int ttabsMax;

//		Components in Addtion to the Immersive Profile
		static bool exRigidBody;
		static bool exHAnim;
		static bool exIODevice;
		static bool nonStandardHAnim;
		static unsigned int exBCFlag;

		void setFileSax3dWriter(ofstream &stream);
		void setExportStyle(MString filter);
		void buildUITreeNode(MString mayaType, MString mayaName, MString x3dType, MString x3dUse, MString x3dName);

		bool			isReferenceNode(MString nodeName);
		bool			isInHiddenLayer(MString nodeName);
//		bool			getCharacterState(MFnDependencyNode meshNode);
		bool			getCharacterState(MObject mObj);
		void			textureSetup();
//		void			writeTexture(MFnDependencyNode depNode, MString ctField);
		void			writeTexture(MObject mObj, MString ctField);
//		void			writeAudioClip(MFnDependencyNode audioNode, MString ctField);
		void			writeAudioClip(MObject mObj, MString ctField);
//		void			writeInline(MFnDependencyNode inNode, MString ctField);
		void			writeInline(MObject mObj, MString ctField);
//		void			writeInlineC(MFnDependencyNode inNode, MString ctField);
		void			writeInlineC(MObject mObj, MString ctField);
		void			soundSetup();
		void			inlineSetup();
		void			grabExporterOptions();
		void			prepareUnderworldNodes();
		void			prepareInterpolatorNodes();
		void			writeHiddenNodes();
		void			createResourceDir();
		void			setIgnoreStatusForDefaults();
		void			writeRoutes();

		MStatus		exportAll();
		MStatus		exportSelected();
		void			organizeExport();
//		bool			showHiddenForTree(MFnDependencyNode depNode);
		bool			showHiddenForTree(MObject mObj);
		void			setAdditionalComps();
		void			writeHumanoidRootNode(bool open, MString humanName);//temporary hanim fix - Dec 6, 2005
//		bool			checkForAvatar(MFnDagNode dagNode);
		bool			checkForAvatar(MObject mObj);

		sax3dWriter		sax3dw;
		web3dExportMethods	web3dem;

		static	MString			optionsString;

	protected:

//		void			buildMeshDagList(MFnDagNode root);

		MStringArray	getInlineNodeNames();
		
//		MStatus		processBranchNode(MFnDagNode dagFn, int cfChoice1);//const MFnDagNode dagFn, int cfChoice1);
		MStatus		processBranchNode(MObject mObj, int cfChoice1);//const MFnDagNode dagFn, int cfChoice1);

//		void			processChildNode(MFnDagNode newDagFn, int cfChoice1);
		void			processChildNode(MObject mObj, int cfChoice1);
//		void			processChildNode(MFnDagNode newDagFn, int cfChoice1, MString cfString);
		void			processChildNode(MObject mObj, int cfChoice1, MString cfString);

//		MString		extractPixelValues(MFnDependencyNode depNode);

		MString		checkUseType(MString nodeName);
		MString		getCFValue(int value);

//		void			processGrouping(MFnDagNode dagFn, MString proxyNode, MStringArray fNames, MStringArray fValues, bool isOE, int remNum, bool hasMeta);
		void			processGrouping(MObject mObj, MString proxyNode, MStringArray fNames, MStringArray fValues, bool isOE, int remNum, bool hasMeta);
//		void			processUsedGrouping(MFnDagNode newDagFn, MString childName, MString tempString, MString contVal, MString contField);
		void			processUsedGrouping(MObject mObj, MString childName, MString tempString, MString contVal, MString contField);
//		void			evalForSyblings(MFnDagNode dagFn, MString contFieldName, unsigned int& remNum, unsigned int& remNum1);
		void			evalForSyblings(MObject mObj, MString contFieldName, unsigned int& remNum, unsigned int& remNum1);
		bool			evalIntermediacy(MString nodeName);
		bool			checkIfIgnored(MString nodeName);

		void			moveFiles(int mediaType);
		void			mayaTextureWriteToDisk();
		void			outputFiles();
		void			outputMovies();
		void			outputNonFiles();
		void			outputAudio();
		void			outputInlines();
		void			outputCollidableShapes();

		bool			checkForMetadata(MString aName);
		bool			checkForAudio(MString aName);
		MObjectArray	getWatchedNodes(MString nodeName);
		bool			checkForTexture(bool isMulti, MObject texNode, MObject mTexNode);
		
//		bool			getRigidBodyState(MFnDagNode parentDagFn);
		bool			getRigidBodyState(MObject mObj);
//		MFnDagNode		getRigidBodyNode(MFnDagNode parentDagFn);
		MObject		getRigidBodyNode(MObject mObj);

		void			addMetadataTag(MString childName);
		void			addAudioTag(MString childName);

		void			processFileTextures();

//		void			writeNodeField(MFnDagNode dagFn, MString plugName, MString cfVal);
		void			writeNodeField(MObject mObj, MString plugName, MString cfVal);

		MStatus		writeMetadataNode(MString x3dName, MString msTString, MString ctField);
		void			setUpMetadataNodes();

//		MStatus		writeLeafNodes(MString childName, MString nodeType, MStringArray newArray1, MStringArray newArray2);
		MStatus		writeLeafNodes(MString mayaName, MString mayaType, MString x3dName, MString x3dType, MStringArray newArray1, MStringArray newArray2);

//		MStatus		writeLeafNodes(MString mayaName, MFnDependencyNode depNode, MString x3dName, MString x3dType, MStringArray newArray1, MStringArray newArray2);
		MStatus		writeLeafNodes(MString mayaName, MObject mObj, MString x3dName, MString x3dType, MStringArray newArray1, MStringArray newArray2);

//		MStatus		writeScript(MFnDagNode aDag, MString cfVal);
		MStatus		writeScript(MObject mObj, MString cfVal);

//		MStatus		writeMeshShape(MFnDagNode newDag, MString cfVal);
		MStatus		writeMeshShape(MObject mObj, MString cfVal);
//		MStatus		writeCollidableShape(MFnDagNode newDag, MFnDagNode pDag, MFnDagNode rbDag, MString cfVal);
		MStatus		writeCollidableShape(MObject mObj, MObject pObj, MObject rbObj, MString cfVal);
//		MStatus		writeHAnimHumanoid(MFnDagNode newDag, MFnDagNode pDag, unsigned int childNum, MStringArray grArray1, MStringArray grArray2);
		MStatus		writeHAnimHumanoid(MObject mObj, MObject pObj, unsigned int childNum, MStringArray grArray1, MStringArray grArray2);
//		MStatus		writeHeadlessHAnimHumanoid(MFnDagNode newDag);
		MStatus		writeHeadlessHAnimHumanoid(MObject mObj);

//		void			buildHAnimHumanoidBody(MFnDagNode newDag, MString pName);
//		void			buildHAnimHumanoidBody(MFnDagNode pDag);
		void			buildHAnimHumanoidBody(MObject mObj);
//		MObjectArray	getCharacterRootJoints(MFnDagNode pDag);
		MObjectArray	getCharacterRootJoints(MObject mObj);
//		void			writeHAnimJointForTree(MFnDagNode newDag);
		void			writeHAnimJointForTree(MObject mObj);

//		void			traverseSkeleton(MFnDagNode newDag, MString pName, MFnSkinCluster sc, MString cfString, double pos[], double pVal[]);
//		void			traverseSkeleton(MFnDagNode newDag, MString pName, MObjectArray scObjs, MString cfString, double pos[], double pVal[]);
		void			traverseSkeleton(MObject mObj, MString pName, MObjectArray scObjs, MString cfString, double pos[], double pVal[]);

//		void			gatherMeshData(MFnSkinCluster sc, MStringArray sca, MFloatVectorArray cna, MString pName);
		void			gatherMeshData(MObjectArray scObjs, MStringArray sca, MFloatVectorArray cna, MString pName);

		void			setUpHAnimGeometry(MDagPath dagpath, unsigned int val, MStringArray sca, MFloatVectorArray cna, MString pName);
		MString		extractCoordinates(MStringArray coordArray);
		MString		extractNormals(MStringArray normArray);
//		MStringArray	getSkinCoords(MFnSkinCluster sc);
		MStringArray	getSkinCoords(MObjectArray scObjs);
		MStringArray	getSkinNorms(MFloatVectorArray finalArray);
		MFloatVectorArray	getTempSkinNormFloats(MObjectArray scObjs);
//		MFloatVectorArray	getTempSkinNormFloats(MFnSkinCluster sc);
		MFloatVectorArray	addUniqueFloatVectors(MFloatVectorArray newArray, MFloatVectorArray finalArray);
//		void			getSkinClusters(MFnDagNode jdag, MObjectArray &scObjs);
		void			getSkinClusters(MObject mObj, MObjectArray &scObjs);

		bool			getMeshDagPath(MString mName, MDagPath dPath);
		bool			checkSArray(MStringArray against, MString check);

		void			setUpAppearance(MObject shader, MDagPath dagpath);
		void			setUpGeometry(MDagPath dagpath, MString nodeType, unsigned int val);
//		void			writePrimative(MFnDagNode dagFn);
		void			writePrimative(MObject mObj);

//		void			setUpMaterial(MFnDependencyNode depFn, int cfVal);
		void			setUpMaterial(MObject mObj, int cfVal);
//		void			shaderTraversal(MFnDependencyNode depFn, int cfVal);
		void			shaderTraversal(MObject mObj, int cfVal);

//		void			setUpTextures(MFnDependencyNode depFn, int cfVal);
		void			setUpTextures(MObject mObj, int cfVal);
//		void			textureTraversal(MFnDependencyNode depFn, int cfVal);
		void			textureTraversal(MObject mObj, int cfVal);
		MStringArray	getTextureData(MString nodeName);

		void			coordNormalColorTexCoord(MDagPath dagpath, unsigned int val, MStringArray geo);
		void			cawCoordinateNode(MDagPath dagpath, unsigned int val);
		void			cawNormalNode(MDagPath dagpath, unsigned int val);
		void			cawColorNode(MDagPath dagpath, unsigned int val);
		void			cawTextureNodes(MDagPath dagpath, unsigned int val);

//		void			setUpTextureTransforms(MFnDependencyNode depFn, int cfVal);
		void			setUpTextureTransforms(MObject mObj, int cfVal);
//		void			textureTransformTraversal(MFnDependencyNode depFn, int cfVal);
		void			textureTransformTraversal(MObject mObj, int cfVal);
		MStringArray	getTextureTransform(MString textureName);

		void			processDynamics();
		void			processScripts();
//		void			processRigidBody(MFnDependencyNode depNode);
		void			processRigidBody(MObject mObj);
//		void			processRBBodies(MFnDependencyNode depNode);
		void			processRBBodies(MObject mObj);
//		void			processRBJoints(MFnDependencyNode depNode);
		void			processRBJoints(MObject mObj);
//		void			processRBCollider(MFnDependencyNode depNode);
		void			processRBCollider(MObject mObj);


		void			posInterCollect();
		void			oriInterCollect();
		void			normalInterCollect();
		void			coordInterCollect();
		void			colorInterCollect();
		void			scalarInterCollect();
		void			boolSeqCollect();
		void			intSeqCollect();
		double		getFrameRate();
		MSelectionList	getNodeList(MString cString);
//		void			gatherKey(MFnDependencyNode depNode);
		void			gatherKey(MObject mObj);

//Jan 31, 2005
//MEL Conversion methods
		MStringArray	x3dMetadataNames(unsigned int metaChoice);
		MStringArray	getMetadataAtts(MString mName);

		MPlug			findMyPlug(MString nodeName, MString plugName);
//		MStringArray	getFieldNamesTexture(MFnDependencyNode depNode, MString textureType);
//		MStringArray	getFieldValuesTexture(MFnDependencyNode depNode, MString textureType);
};


#endif
