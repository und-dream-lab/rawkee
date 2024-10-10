#ifndef RAWKEE_IMPL_H
#define RAWKEE_IMPL_H

///////////////////////////////////////////////////////////////////////////////

// #include <rawkee/project.h>

///////////////////////////////////////////////////////////////////////////////

// #if defined( RAWKEE_LINUX )
// #    include <rawkee/linux/public>
// #elif defined( RAWKEE_OSX )
// #    include <rawkee/osx/public>
// #elif defined( RAWKEE_WINDOWS )
// #    include <rawkee/windows/public>
// #else
// #    error "RAWKEE platform is not defined."
// #endif

// #ifndef RAWKEE_versionMajor
// #define RAWKEE_versionMajor 1
// #endif

// #ifndef RAWKEE_versionMinor
// #define RAWKEE_versionMinor 2
// #endif

// #ifndef RAWKEE_versionPoint
// #define RAWKEE_versionPoint 0
// #endif

// #ifndef RAWKEE_author
// #define RAWKEE_author "UND DREAM Lab"
// #endif

// #ifndef RAWKEE_titlev
// #define RAWKEE_titlev "1.2.0"
// #endif

///////////////////////////////////////////////////////////////////////////////

#include <cmath>

///////////////////////////////////////////////////////////////////////////////

#define _BOOL
#define REQUIRE_IOSTREAM

#define RAWKEE_versionMajor 1
#define RAWKEE_versionMinor 2
#define RAWKEE_versionPoint 0
#define RAWKEE_author "UND DREAM Lab"
#define RAWKEE_titlev "1.2.0"

///////////////////////////////////////////////////////////////////////////////

#include <maya/M3dView.h>
#include <maya/MAnimControl.h>
#include <maya/MArgList.h>
#include <maya/MArrayDataBuilder.h>
#include <maya/MArrayDataHandle.h>
#include <maya/MBoundingBox.h>
#include <maya/MColorArray.h>
#include <maya/MDGMessage.h>
#include <maya/MDGModifier.h>
#include <maya/MDagMessage.h>
#include <maya/MDagPath.h>
#include <maya/MDagPathArray.h>
#include <maya/MDataBlock.h>
#include <maya/MDataHandle.h>
#include <maya/MDistance.h>
#include <maya/MDoubleArray.h>
#include <maya/MEulerRotation.h>
#include <maya/MEventMessage.h>
#include <maya/MFileIO.h>
#include <maya/MFileObject.h>
#include <maya/MFloatArray.h>
#include <maya/MFloatMatrix.h>
#include <maya/MFloatPointArray.h>
#include <maya/MFloatVector.h>
#include <maya/MFloatVectorArray.h>
#include <maya/MFnCompoundAttribute.h>
#include <maya/MFnDagNode.h>
#include <maya/MFnData.h>
#include <maya/MFnDependencyNode.h>
#include <maya/MFnDoubleArrayData.h>
#include <maya/MFnEnumAttribute.h>
#include <maya/MFnFreePointTriadManip.h>
#include <maya/MFnIkJoint.h>
#include <maya/MFnIntArrayData.h>
#include <maya/MFnLight.h>
#include <maya/MFnMesh.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnNumericData.h>
#include <maya/MFnPointArrayData.h>
#include <maya/MFnSkinCluster.h>
#include <maya/MFnStringArrayData.h>
#include <maya/MFnStringData.h>
#include <maya/MFnTypedAttribute.h>
#include <maya/MFnUnitAttribute.h>
#include <maya/MFnVectorArrayData.h>
#include <maya/MGlobal.h>
#include <maya/MIOStream.h>
#include <maya/MImage.h>
#include <maya/MItDag.h>
#include <maya/MItDependencyGraph.h>
#include <maya/MItDependencyNodes.h>
#include <maya/MItGeometry.h>
#include <maya/MItMeshPolygon.h>
#include <maya/MItSelectionList.h>
#include <maya/MMatrix.h>
#include <maya/MNodeMessage.h>
#include <maya/MObject.h>
#include <maya/MPlug.h>
#include <maya/MPlugArray.h>
#include <maya/MPoint.h>
#include <maya/MPointArray.h>
#include <maya/MPxCommand.h>
#include <maya/MPxFileTranslator.h>
#include <maya/MPxLocatorNode.h>
#include <maya/MPxManipContainer.h>
#include <maya/MPxNode.h>
#include <maya/MPxTransform.h>
#include <maya/MPxTransformationMatrix.h>
#include <maya/MQuaternion.h>
#include <maya/MSceneMessage.h>
#include <maya/MSelectionList.h>
#include <maya/MStatus.h>
#include <maya/MString.h>
#include <maya/MStringArray.h>
#include <maya/MTime.h>
#include <maya/MTypeId.h>
#include <maya/MVector.h>
#include <maya/MVectorArray.h>
// #include <maya/MGL.h>
// #include <GL/gl.h>

//const unsigned int RAWKEE_versionMajor = 1;
//const unsigned int RAWKEE_versionMinor = 2;
//cosnt unsigned int RAWKEE_versionPoint = 0;
//const MString RAWKEE_author("UND DREAM Lab");
//const MString RAWKEE_titlev("1.2.0");



///////////////////////////////////////////////////////////////////////////////

#include <rawkee/sax3dWriter.h>

#include <rawkee/web3dExportMethods.h>
#include <rawkee/x3dExportOrganizer.h>

#include <rawkee/web3dFileTranslator.h>
#include <rawkee/vrml97FileTranslator.h>
#include <rawkee/x3dFileTranslator.h>
#include <rawkee/x3dbFileTranslator.h>
#include <rawkee/x3dvFileTranslator.h>

#include <rawkee/webX3DExporter.h>

///////////////////////////////////////////////////////////////////////////////

#endif // RAWKEE_IMPL_H
