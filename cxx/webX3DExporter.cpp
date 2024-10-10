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

// File: webX3DExporter.cpp
//
// MEL Command: x3d
//
// Author: Maya SDK Wizard
//
//         Aaron Bergstrom
//         Computer Visualization Manger
//         NDSU Archaeology Technologies Laboratory
//         http://atl.ndsu.edu/
//
//*M* - means: As stated by the Maya API documentation
// 

#include <rawkee/impl.h>
#include <maya/MFnPlugin.h>

///////////////////////////////////////////////////////////////////////////////

// Special declaration to export public methods using link-formats which
// default to private. Usually this is the default on Windows, but since g++
// 4.0.0 we can do the same. On older g++ versions, this should have no impact.

// extern LF_PUBLIC MStatus initializePlugin   ( MObject );
// extern LF_PUBLIC MStatus uninitializePlugin ( MObject );

// extern LF_PUBLIC char MApiVersion[];

///////////////////////////////////////////////////////////////////////////////

void webX3DExporter::constructWeb3DScenegraphTree(unsigned int exportType, MString optionsString, bool isFrom)
{
	MGlobal::executeCommand("setX3DProcTreeTrue");
	x3dExportOrganizer newX3dEO;
	sax3dWriter newSax3d;
	newX3dEO.sax3dw = newSax3d;
	newX3dEO.isTreeBuilding = true;
	newX3dEO.hasPassed = false;
	newX3dEO.treeTabs = 0;
	newX3dEO.exEncoding = exportType;

	cout << optionsString << endl;

	newX3dEO.optionsString.operator =(optionsString);

	newX3dEO.organizeExport();
	newX3dEO.x3dTreeStrings.set("");
	newX3dEO.x3dTreeDelStrings.set("");

	//newX3dEO.writeHiddenNodes();
	//newX3dEO.exportAll();
	newX3dEO.exportSelected();
	
	MGlobal::executeCommand("setX3DProcTreeFalse");

	MString excmd("optionVar -iv x3dNodeTreeWidth ");
	int ttmax = newX3dEO.ttabsMax;
	excmd.operator +=(ttmax);
	MGlobal::executeCommand(excmd);
	newX3dEO.ttabsMax = 0;

	MGlobal::displayInfo(newX3dEO.x3dTreeStrings);
	if(isFrom)
	{
		MGlobal::displayInfo(newX3dEO.x3dTreeStrings);
		MGlobal::executeCommand("loadFromNodeInterface(\""+newX3dEO.x3dTreeStrings+"\")");
		MGlobal::displayInfo(newX3dEO.x3dTreeStrings);
	}
	else
	{
		MGlobal::executeCommand("loadToNodeInterface(\""+newX3dEO.x3dTreeStrings+"\")");
	}
//	MGlobal::executeCommand("listX3DTree(\""+newX3dEO.x3dTreeStrings+"\")");
/*
	MStringArray routeNames;
	MGlobal::executeCommand("ls -type x3dRoute", routeNames);

	unsigned int rnLen = routeNames.length();

	unsigned int i;
	for(i=0; i<rnLen; i++)
	{
		MFnDependencyNode depFn = newX3dEO.web3dem.getMyDepNode(routeNames.operator [](i));

		MStatus mstat;
		MPlug cs = depFn.findPlug("checkString", &mstat);
		if(mstat == MStatus::kSuccess)
		{
			cs.setValue(newX3dEO.x3dTreeDelStrings);

			MPlug sd = depFn.findPlug("selfDelete");
			bool sdVal = false;
			sd.getValue(sdVal);

			MPlug sddi = depFn.findPlug("sdDoIt");
			sddi.setValue(sdVal);
		}
	}
	*/
}

MStatus webX3DExporter::doIt( const MArgList& args )
{
	unsigned int fValue;
	bool isFrom = true;
	MStatus status;
	MString helpString("\nWelcome to createWeb3dTree Help!\nFlag '-f' or '-format' takes an int value of 0-3. Obviously the '-h' or '-help' flags spit this back at you.");
	bool flagFound = false;
	bool canRun = false;
	MString newOptions;
	for(unsigned int i=0; i < args.length();i++)
	{
		if(args.asString(i) == "-f" || args.asString(i) == "-format")
		{
			fValue = args.asInt(++i);
			if(fValue >= 0 || fValue < 4)
			{
				canRun = true;
				flagFound = true;
			}
		}
		else if(args.asString(i) == "-ue" || args.asString(i) == "-useEmpties")
		{
			MString tempString(args.asString(++i));
			newOptions.operator +=("x3dUseEmpties*");
			newOptions.operator +=(tempString);
			newOptions.operator +=("*");
			flagFound = true;
		}
		else if(args.asString(i) == "-meta" || args.asString(i) == "-metadata")
		{
			MString tempString(args.asString(++i));
			newOptions.operator +=("x3dExportMetadata*");
			newOptions.operator +=(tempString);
			newOptions.operator +=("*");
			flagFound = true;
		}
		else if(args.asString(i) == "-cpv" || args.asString(i) == "-colorPerVertex")
		{
			MString tempString(args.asString(++i));
			newOptions.operator +=("x3dCPV*");
			newOptions.operator +=(tempString);
			newOptions.operator +=("*");
			flagFound = true;
		}
		else if(args.asString(i) == "-npv" || args.asString(i) == "-normalPerVertex")
		{
			MString tempString(args.asString(++i));
			newOptions.operator +=("x3dNPV*");
			newOptions.operator +=(tempString);
			newOptions.operator +=("*");
			flagFound = true;
		}
		else if(args.asString(i) == "-ha" || args.asString(i) == "-isHAnim")
		{
			MString tempString(args.asString(++i));
			newOptions.operator +=("x3dHAnimExport*");
			newOptions.operator +=(tempString);
			newOptions.operator +=("*");
			flagFound = true;
		}
		else if(args.asString(i) == "-rb" || args.asString(i) == "-isRigid")
		{
			MString tempString(args.asString(++i));
			newOptions.operator +=("x3dRigidBodyExport*");
			newOptions.operator +=(tempString);
			newOptions.operator +=("*");
			flagFound = true;
		}
		else if(args.asString(i) == "-upm" || args.asString(i) == "-updateMethod")
		{
			MString tempString(args.asString(++i));
			newOptions.operator +=("updateMethod*");
			newOptions.operator +=(tempString);
//			newOptions + "*";
			flagFound = true;
		}
		else if(args.asString(i) == "-nsha" || args.asString(i) == "-nonStandardHAnim")
		{
			MString tempString(args.asString(++i));
			newOptions.operator +=("x3dNSHAnim*");
			newOptions.operator +=(tempString);
//			newOptions + "*";
			flagFound = true;
		}
		else if(args.asString(i) == "-if" || args.asString(i) == "-isFrom")
		{
			MString tempString(args.asString(++i));
			if(tempString.operator ==("0")) isFrom = false;
			else isFrom = true;
		}
		else if(args.asString(i) == "-h" || args.asString(i) == "-help")
		{
			MGlobal::displayInfo(helpString);
			flagFound = true;
		}
	}

	if(canRun) constructWeb3DScenegraphTree(fValue, newOptions, isFrom);
	if(!flagFound) MGlobal::displayInfo("\nNo valid flags found. Use '-f/-format' of '-h/-help'.");


	return MStatus::kSuccess;
}
//END OF NEW CODE

void * webX3DExporter::creator()
{
	//allows Maya to allocate an instance of this method
	return new webX3DExporter;//();
}
//*************************************************
//*************************************************

///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//Method for initializing the plug-in to Maya
//-----------------------------------------
MStatus initializePlugin( MObject obj ){//Maya calls this method itself
	                                    //we will never need to call this
										//method in any code we write

	MStatus stat; //An MStatus tells us whether or not
	              //an operation was successful, and
	              //sometimes why it wasn't.

	//This creates add Maya Plug-in functionality to object, afterwhich
	//the object must be referenced my the new object name "pluginFn" in order
	//for this functionality to work.
	//
	//"RawKee X3D Exporter Group" is the vendor name of our plugin
	//"0.1" is the plugin's version number.
	//
	//"ANY" states that the plugin can be used with any version of Maya.
	//But yeah... not really... just the version for which it is compiled.

	MFnPlugin pluginFn( obj, RAWKEE_author, RAWKEE_titlev, "Any" );
	pluginFn.setName("RawKee", false);

	//This next line registers our newly defined plugin object
	//as a file translator for Maya. This means it can now
	//be used to "export" or "import" files.
	//This version of RawKee is only setup to
	//export files.
	//
	//"X3D" is the name of the file translator
	//"" is the pathname of the icon used in file selection dialogs *M*
	//
	//webX3DExporter::creator - a pointer to a function that will 
	//return a pointer to a new instance of the class 
	//(derived from MPxFileTranslator) that implements the new file type. *M*
	//
	//x3dOptions - name of MEL script procedure for displaying the Export
	//options panel for this file translator.
	//
	//options1=1 - not entirely sure
	//
	//true - must be set to true in order to use the "MGlobal::executeCommand"
	stat = pluginFn.registerFileTranslator("RawKee - X3D XML","x3d_logo.bmp",x3dFileTranslator::creator,"x3dFormatOptions","option1=1",true);
	stat = pluginFn.registerFileTranslator("RawKee - X3D Classic","x3d_logo.bmp",x3dvFileTranslator::creator,"x3dvFormatOptions","option1=1",true);
//	stat = pluginFn.registerFileTranslator("RawKee - X3D Binary","x3d_logo.bmp",x3dbFileTranslator::creator,"x3dbFormatOptions","option1=1",true);
	stat = pluginFn.registerFileTranslator("RawKee - VRML 97","x3d_logo.bmp",vrml97FileTranslator::creator,"vrml97FormatOptions","option1=1",true);
	stat = pluginFn.registerCommand("createWeb3dTree", webX3DExporter::creator);
//	stat = pluginFn.registerCommand("x3dscriptvars", x3dscriptvars::creator, x3dscriptvars::newSyntax);

	if(!stat ){
		stat.perror( "registerFileTranslator" );
	}else{

		//Sourcing plug-in MEL scripts
		//These mel scripts must be sourced for the plugin
		//to do many things. To find out more about them
		//please refer to their documentaion.
		MGlobal::executeCommand( MString( "source x3d.mel" ) );
		MGlobal::executeCommand( MString( "source x3dUtilCommands.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_scenegraph_ui_tree.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_exporter_procedures.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_routing_scripts.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_ie_menus.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_switch_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_lod_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_collision_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_navigationinfo_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_worldinfo_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_transform_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_proximitysensor_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_touchsensor_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_timesensor_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_viewpoint_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_orientationinterpolator_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_positioninterpolator_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_script_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_node_creation_procs.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_appearance_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_box_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_color_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_colorrgba_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_cone_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_coordinate_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_cylinder_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_directionallight_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_group_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_imagetexture_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_movietexture_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_indexedfaceset_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_material_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_metadatadouble_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_metadatafloat_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_metadatainteger_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_metadataset_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_metadatastring_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_normal_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_pointlight_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_shape_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_spotlight_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_texturetransform_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_texturecoordinate_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_sphere_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_anchor_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_billboard_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_inline_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_colorinterpolator_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_scalarinterpolator_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_coordinateinterpolator_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_normalinterpolator_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_booleansequencer_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_integersequencer_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_booleantrigger_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_booleantoggle_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_integertrigger_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_timetrigger_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_cylindersensor_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_keysensor_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_loadsensor_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_planesensor_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_spheresensor_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_stringsensor_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_visibilitysensor_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_pixeltexture_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_multitexturecoordinate_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_multitexturetransform_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_multitexture_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_audioclip_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_sound_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_booleanfilter_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_collidableshape_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_hanimhumanoid_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_hanimjoint_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_hanimsite_tables.mel" ) );
		MGlobal::executeCommand( MString( "source x3d_gamepadsensor_tables.mel") );
		MGlobal::executeCommand( MString( "source x3d_rigidbodycollection_tables.mel") );
		MGlobal::executeCommand( MString( "source x3d_rigidbody_tables.mel") );
		MGlobal::executeCommand( MString( "source x3d_collisioncollection_tables.mel") );
		MGlobal::executeCommand( MString( "source x3d_collisionspace_tables.mel") );
		MGlobal::executeCommand( MString( "source x3d_collisionsensor_tables.mel") );
		MGlobal::executeCommand( MString( "setUpX3DMenus" ) );
		
		//Here we are registering our RawKee defined nodes with Maya.
		//Some nodes are derived from the MPxTransform class. Nodes
		//can only be used in the underworld if they are derived in 
		//this manner.
		//Some grouping nodes are also derived from the MPxTransform class
		//so that they can be placed within the DAG, moved around within
		//the DAG tree, and hold children.

		stat = pluginFn.registerTransform(x3dBox::typeName, x3dBox::typeId, &x3dBox::creator, &x3dBox::initialize, &MPxTransformationMatrix::creator, x3dBox::typeId);
		stat = pluginFn.registerTransform(x3dCone::typeName, x3dCone::typeId, &x3dCone::creator, &x3dCone::initialize, &MPxTransformationMatrix::creator, x3dCone::typeId);
		stat = pluginFn.registerTransform(x3dCylinder::typeName, x3dCylinder::typeId, &x3dCylinder::creator, &x3dCylinder::initialize, &MPxTransformationMatrix::creator, x3dCylinder::typeId);
		stat = pluginFn.registerTransform(x3dIndexedFaceSet::typeName, x3dIndexedFaceSet::typeId, &x3dIndexedFaceSet::creator, &x3dIndexedFaceSet::initialize, &MPxTransformationMatrix::creator, x3dIndexedFaceSet::typeId);
		stat = pluginFn.registerTransform(x3dSphere::typeName, x3dSphere::typeId, &x3dSphere::creator, &x3dSphere::initialize, &MPxTransformationMatrix::creator, x3dSphere::typeId);

		stat = pluginFn.registerTransform(x3dCollision::typeName, x3dCollision::typeId, &x3dCollision::creator, &x3dCollision::initialize, &MPxTransformationMatrix::creator, x3dCollision::typeId);
		stat = pluginFn.registerTransform(x3dBillboard::typeName, x3dBillboard::typeId, &x3dBillboard::creator, &x3dBillboard::initialize, &MPxTransformationMatrix::creator, x3dBillboard::typeId);
		stat = pluginFn.registerTransform(x3dAnchor::typeName, x3dAnchor::typeId, &x3dAnchor::creator, &x3dAnchor::initialize, &MPxTransformationMatrix::creator, x3dAnchor::typeId);
		stat = pluginFn.registerTransform(x3dInline::typeName, x3dInline::typeId, &x3dInline::creator, &x3dInline::initialize, &MPxTransformationMatrix::creator, x3dInline::typeId);
		stat = pluginFn.registerTransform(x3dGroup::typeName, x3dGroup::typeId, &x3dGroup::creator, &x3dGroup::initialize, &MPxTransformationMatrix::creator, x3dGroup::typeId);
		stat = pluginFn.registerTransform(x3dSwitch::typeName, x3dSwitch::typeId, &x3dSwitch::creator, &x3dSwitch::initialize, &MPxTransformationMatrix::creator, x3dSwitch::typeId);

		stat = pluginFn.registerTransform(x3dColor::typeName, x3dColor::typeId, &x3dColor::creator, &x3dColor::initialize, &MPxTransformationMatrix::creator, x3dColor::typeId);
		stat = pluginFn.registerTransform(x3dColorRGBA::typeName, x3dColorRGBA::typeId, &x3dColorRGBA::creator, &x3dColorRGBA::initialize, &MPxTransformationMatrix::creator, x3dColorRGBA::typeId);
		stat = pluginFn.registerTransform(x3dNormal::typeName, x3dNormal::typeId, &x3dNormal::creator, &x3dNormal::initialize, &MPxTransformationMatrix::creator, x3dNormal::typeId);
		stat = pluginFn.registerTransform(x3dCoordinate::typeName, x3dCoordinate::typeId, &x3dCoordinate::creator, &x3dCoordinate::initialize, &MPxTransformationMatrix::creator, x3dCoordinate::typeId);
		stat = pluginFn.registerTransform(x3dTextureCoordinate::typeName, x3dTextureCoordinate::typeId, &x3dTextureCoordinate::creator, &x3dTextureCoordinate::initialize, &MPxTransformationMatrix::creator, x3dTextureCoordinate::typeId);
//		stat = pluginFn.registerTransform(x3dTextureCoordinateGenerator::typeName, x3dTextureCoordinateGenerator::typeId, &x3dTextureCoordinateGenerator::creator, &x3dTextureCoordinateGenerator::initialize, &MPxTransformationMatrix::creator, 0x00108F00);

		//Leaf nodes are generally derived from the kLocatorNode class
		//These nodes cannot be positioned, rotated, or scaled.
		//Currently, the only leaf node not done in this manner 
		//is the x3dProximitySensor node. It is derived from the
		//MPxTransform node. But this will most likely change in future
		//versions of RawKee.
		//
		//Some kLocatorNode class are DAG nodes, some are merely
		//DependencyGraph nodes. To find out which, check that
		//nodes documentation.
		stat = pluginFn.registerNode(x3dLoadSensor::typeName, x3dLoadSensor::typeId, &x3dLoadSensor::creator, &x3dLoadSensor::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dKeySensor::typeName, x3dKeySensor::typeId, &x3dKeySensor::creator, &x3dKeySensor::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dStringSensor::typeName, x3dStringSensor::typeId, &x3dStringSensor::creator, &x3dStringSensor::initialize, MPxNode::kLocatorNode);

		stat = pluginFn.registerNode(x3dCylinderSensor::typeName, x3dCylinderSensor::typeId, &x3dCylinderSensor::creator, &x3dCylinderSensor::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dPlaneSensor::typeName, x3dPlaneSensor::typeId, &x3dPlaneSensor::creator, &x3dPlaneSensor::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dSphereSensor::typeName, x3dSphereSensor::typeId, &x3dSphereSensor::creator, &x3dSphereSensor::initialize, MPxNode::kLocatorNode);

		stat = pluginFn.registerNode(x3dProximitySensor::typeName, x3dProximitySensor::typeId, &x3dProximitySensor::creator, &x3dProximitySensor::initialize, MPxNode::kLocatorNode);
//		stat = pluginFn.registerNode("x3dProximitySensorManip", x3dProximitySensorManip::typeId, &x3dProximitySensorManip::creator, &x3dProximitySensorManip::initialize, MPxNode::kManipContainer);
		stat = pluginFn.registerNode(x3dVisibilitySensor::typeName, x3dVisibilitySensor::typeId, &x3dVisibilitySensor::creator, &x3dVisibilitySensor::initialize, MPxNode::kLocatorNode);

		stat = pluginFn.registerNode(x3dBooleanToggle::typeName, x3dBooleanToggle::typeId, &x3dBooleanToggle::creator, &x3dBooleanToggle::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dBooleanTrigger::typeName, x3dBooleanTrigger::typeId, &x3dBooleanTrigger::creator, &x3dBooleanTrigger::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dBooleanFilter::typeName, x3dBooleanFilter::typeId, &x3dBooleanFilter::creator, &x3dBooleanFilter::initialize, MPxNode::kLocatorNode);

		stat = pluginFn.registerNode(x3dIntegerTrigger::typeName, x3dIntegerTrigger::typeId, &x3dIntegerTrigger::creator, &x3dIntegerTrigger::initialize, MPxNode::kLocatorNode);

		stat = pluginFn.registerNode(x3dTimeTrigger::typeName, x3dTimeTrigger::typeId, &x3dTimeTrigger::creator, &x3dTimeTrigger::initialize, MPxNode::kLocatorNode);

		stat = pluginFn.registerNode(x3dSound::typeName, x3dSound::typeId, &x3dSound::creator, &x3dSound::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dWorldInfo::typeName, x3dWorldInfo::typeId, &x3dWorldInfo::creator, &x3dWorldInfo::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dNavigationInfo::typeName, x3dNavigationInfo::typeId, &x3dNavigationInfo::creator, &x3dNavigationInfo::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dTouchSensor::typeName, x3dTouchSensor::typeId, &x3dTouchSensor::creator, &x3dTouchSensor::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dGamepadSensor::typeName, x3dGamepadSensor::typeId, &x3dGamepadSensor::creator, &x3dGamepadSensor::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dTimeSensor::typeName, x3dTimeSensor::typeId, &x3dTimeSensor::creator, &x3dTimeSensor::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dScript::typeName, x3dScript::typeId, &x3dScript::creator, &x3dScript::initialize, MPxNode::kLocatorNode);

		stat = pluginFn.registerNode(x3dPositionInterpolator::typeName, x3dPositionInterpolator::typeId, &x3dPositionInterpolator::creator, &x3dPositionInterpolator::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dOrientationInterpolator::typeName, x3dOrientationInterpolator::typeId, &x3dOrientationInterpolator::creator, &x3dOrientationInterpolator::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dCoordinateInterpolator::typeName, x3dCoordinateInterpolator::typeId, &x3dCoordinateInterpolator::creator, &x3dCoordinateInterpolator::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dNormalInterpolator::typeName, x3dNormalInterpolator::typeId, &x3dNormalInterpolator::creator, &x3dNormalInterpolator::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dScalarInterpolator::typeName, x3dScalarInterpolator::typeId, &x3dScalarInterpolator::creator, &x3dScalarInterpolator::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dColorInterpolator::typeName, x3dColorInterpolator::typeId, &x3dColorInterpolator::creator, &x3dColorInterpolator::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dBooleanSequencer::typeName, x3dBooleanSequencer::typeId, &x3dBooleanSequencer::creator, &x3dBooleanSequencer::initialize, MPxNode::kLocatorNode);
		stat = pluginFn.registerNode(x3dIntegerSequencer::typeName, x3dIntegerSequencer::typeId, &x3dIntegerSequencer::creator, &x3dIntegerSequencer::initialize, MPxNode::kLocatorNode);

		stat = pluginFn.registerNode(x3dRoute::typeName, x3dRoute::typeId, &x3dRoute::creator, &x3dRoute::initialize);//, MPxNode);
		stat = pluginFn.registerNode(x3dMetadataDouble::typeName, x3dMetadataDouble::typeId, &x3dMetadataDouble::creator, &x3dMetadataDouble::initialize);//, MPxNode);
		stat = pluginFn.registerNode(x3dMetadataFloat::typeName, x3dMetadataFloat::typeId, &x3dMetadataFloat::creator, &x3dMetadataFloat::initialize);//, MPxNode);
		stat = pluginFn.registerNode(x3dMetadataInteger::typeName, x3dMetadataInteger::typeId, &x3dMetadataInteger::creator, &x3dMetadataInteger::initialize);//, MPxNode);
		stat = pluginFn.registerNode(x3dMetadataSet::typeName, x3dMetadataSet::typeId, &x3dMetadataSet::creator, &x3dMetadataSet::initialize);//, MPxNode);
		stat = pluginFn.registerNode(x3dMetadataString::typeName, x3dMetadataString::typeId, &x3dMetadataString::creator, &x3dMetadataString::initialize);//, MPxNode);
		if(!stat ){
			stat.perror( "registerTransform" );
		}
	}

	///////////////////////////////////////////////////
	//This is our first message to the Maya Output Window.
	//msg is a Maya MString object. You may set the string
	//as showed below. The message isn't actually sent to
	//the output window until the cout line is used as shown
	//below.

	//In the initializePlugin method, the msg string must
	//include the webX3DExporter:: class designator at the front.
	//or it will throw errors. I don't know why. Let me know
	//if you do. Any other time msg will suffice.
//	webX3DExporter::msg.set("Plugin Initialized Successfully!");

//	cout << webX3DExporter::msg << endl;


	//This method requires a MStatus be returned.
	//only use with 6.0 and newer
//	MUserEventMessage::registerUserEvent("x3dSceneUpdate");

	//only use with 6.0 and newer
//	MUserEventMessage::addUserEventCallback("x3dSceneUpdate", webX3DExporter::x3dSceneUpdateMethod);

	//works with all versions supported
	MDGMessage::addNodeAddedCallback(webX3DExporter::setRawKeeNodeAdded);
	MDGMessage::addNodeRemovedCallback(webX3DExporter::setRawKeeNodeRemoved);
	MEventMessage::addEventCallback("SelectionChanged", webX3DExporter::showSelectedRoute);
	MSceneMessage::addCallback(MSceneMessage::kAfterNew, webX3DExporter::afterFile);
	MSceneMessage::addCallback(MSceneMessage::kAfterOpen, webX3DExporter::afterFile);
	MSceneMessage::addCallback(MSceneMessage::kAfterImport, webX3DExporter::afterFile);
	webX3DExporter::runFileSetup();
	
	return stat;
}

///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
//Method for uninitializing the plug-in to Maya
//It has somebugs, sometimes uninitializing the
//plug-in causes Maya to lockup. I don't know
//why.
//-----------------------------------------
MStatus uninitializePlugin( MObject obj ){

	MStatus stat;
	MFnPlugin pluginFn( obj ); //Adding plugin functionality to an object

	stat = pluginFn.deregisterFileTranslator( "X3D XML - RawKee" ); //removing communication to the plugin from Maya
	stat = pluginFn.deregisterFileTranslator( "X3D Classic - RawKee" ); //removing communication to the plugin from Maya
	stat = pluginFn.deregisterFileTranslator( "VRML 97 - RawKee" ); //removing communication to the plugin from Maya
//	stat = pluginFn.deregisterFileTranslator( "X3D Binary" );  //removing communication to the plugin from Maya

	stat = pluginFn.deregisterCommand("createWeb3dTree");
//	stat = pluginFn.deregisterCommand("x3dscriptvars");

	if ( !stat ){
		stat.perror( "deregisterFileTranslator" ); //operation was unsuccessful
	}else{
		MGlobal::executeCommand( MString( "removeX3DMenus" ) ); // removing the RawKee
		                                                        // menu system from the
		                                                        // Maya's UI

		//Removing RawKee node types.
 		stat = pluginFn.deregisterNode(x3dBox::typeId);         
		stat = pluginFn.deregisterNode(x3dSphere::typeId);
		stat = pluginFn.deregisterNode(x3dCylinder::typeId);
		stat = pluginFn.deregisterNode(x3dIndexedFaceSet::typeId);
		stat = pluginFn.deregisterNode(x3dSphere::typeId);
		stat = pluginFn.deregisterNode(x3dNavigationInfo::typeId);
		stat = pluginFn.deregisterNode(x3dWorldInfo::typeId);
		stat = pluginFn.deregisterNode(x3dTouchSensor::typeId);
		stat = pluginFn.deregisterNode(x3dGamepadSensor::typeId);
		stat = pluginFn.deregisterNode(x3dTimeSensor::typeId);
		stat = pluginFn.deregisterNode(x3dScript::typeId);

		stat = pluginFn.deregisterNode(x3dPositionInterpolator::typeId);
		stat = pluginFn.deregisterNode(x3dOrientationInterpolator::typeId);
		stat = pluginFn.deregisterNode(x3dScalarInterpolator::typeId);
		stat = pluginFn.deregisterNode(x3dCoordinateInterpolator::typeId);
		stat = pluginFn.deregisterNode(x3dColorInterpolator::typeId);
		stat = pluginFn.deregisterNode(x3dNormalInterpolator::typeId);
		stat = pluginFn.deregisterNode(x3dBooleanSequencer::typeId);
		stat = pluginFn.deregisterNode(x3dIntegerSequencer::typeId);


		stat = pluginFn.deregisterNode(x3dRoute::typeId);
		stat = pluginFn.deregisterNode(x3dMetadataDouble::typeId);
		stat = pluginFn.deregisterNode(x3dMetadataFloat::typeId);
		stat = pluginFn.deregisterNode(x3dMetadataInteger::typeId);
		stat = pluginFn.deregisterNode(x3dMetadataSet::typeId);
		stat = pluginFn.deregisterNode(x3dMetadataString::typeId);
//		stat = pluginFn.deregisterNode(x3dTextureCoordinateGenerator::typeId);
		stat = pluginFn.deregisterNode(x3dTextureCoordinate::typeId);
		stat = pluginFn.deregisterNode(x3dCoordinate::typeId);
		stat = pluginFn.deregisterNode(x3dNormal::typeId);
		stat = pluginFn.deregisterNode(x3dColorRGBA::typeId);
		stat = pluginFn.deregisterNode(x3dColor::typeId);

		stat = pluginFn.deregisterNode(x3dLoadSensor::typeId);
		stat = pluginFn.deregisterNode(x3dKeySensor::typeId);
		stat = pluginFn.deregisterNode(x3dStringSensor::typeId);

		stat = pluginFn.deregisterNode(x3dCylinderSensor::typeId);
		stat = pluginFn.deregisterNode(x3dPlaneSensor::typeId);
		stat = pluginFn.deregisterNode(x3dSphereSensor::typeId);

		stat = pluginFn.deregisterNode(x3dBooleanToggle::typeId);
		stat = pluginFn.deregisterNode(x3dBooleanTrigger::typeId);
		stat = pluginFn.deregisterNode(x3dBooleanFilter::typeId);

		stat = pluginFn.deregisterNode(x3dIntegerTrigger::typeId);

		stat = pluginFn.deregisterNode(x3dTimeTrigger::typeId);

		stat = pluginFn.deregisterNode(x3dProximitySensor::typeId);
//		stat = pluginFn.deregisterNode(x3dProximitySensorManip::typeId);
		stat = pluginFn.deregisterNode(x3dVisibilitySensor::typeId);

		stat = pluginFn.deregisterNode(x3dSound::typeId);
		stat = pluginFn.deregisterNode(x3dCollision::typeId);
		stat = pluginFn.deregisterNode(x3dGroup::typeId);
		stat = pluginFn.deregisterNode(x3dBillboard::typeId);
		stat = pluginFn.deregisterNode(x3dAnchor::typeId);
		stat = pluginFn.deregisterNode(x3dInline::typeId);
		stat = pluginFn.deregisterNode(x3dSwitch::typeId);

		if(!stat){
			stat.perror("deregisterNode");
		}
	}

	return stat; //Must return an MStatus object
}

//***************************************************
//***************************************************
void	webX3DExporter::runFileSetup()
{
	MItDependencyNodes mitDep(MFn::kInvalid);
	MGlobal::displayInfo("Start");
	while(!mitDep.isDone())
	{
		MObject temp=mitDep.item();
		rawKeeNodeSetups(temp);
		mitDep.next();
	}
}

void	webX3DExporter::afterFile(void* clientData)
{
	MGlobal::executeCommand("createX3DIE");
	MGlobal::executeCommand("x3dOldTextureAtts");
	MGlobal::displayInfo("End of file in");
}

void	webX3DExporter::rawKeeNodeSetups(MObject & node)
{
	MFnDependencyNode depNode(node);

	MStatus fStat;
	MPlug metaPlug = depNode.findPlug("x3dMetadataIn", &fStat);

	if(fStat != MStatus::kSuccess)
	{
		MFnNumericAttribute createMeta;
		MObject x3dMetadataIn = createMeta.create("x3dMetadataIn", "x3dMetaIn", MFnNumericData::kBoolean, true);
		MFnAttribute metaAttribute(x3dMetadataIn);
		metaAttribute.setReadable(false);
		depNode.addAttribute(x3dMetadataIn);
	}

	MPlug prePlug = depNode.findPlug("x3dpre", &fStat);
	MPlug interPlug = depNode.findPlug("intermediateObject");
	bool interVal = true;
	interPlug.getValue(interVal);

	if(fStat != MStatus::kSuccess || interVal == false)
	{
		MStatus isAtty;

		if(depNode.typeName().operator ==("x3dSwitch"))
		{
			MNodeMessage::addAttributeChangedCallback(node, webX3DExporter::changeSwitchVisibility);
		}
		MFnTypedAttribute createAtt;
		MObject objAttr = createAtt.create("x3dPreviousNodeName", "x3dpnn", MFnData::kString);
		MFnAttribute typedAttr(objAttr);
		typedAttr.setHidden(true);

		depNode.findPlug("x3dppn", &isAtty);
		if(isAtty != MStatus::kSuccess) depNode.addAttribute(objAttr);

		MFnNumericAttribute createNum;
		MObject bAttr = createNum.create("x3dPresets", "x3dpre", MFnNumericData::kBoolean, true);
		MFnAttribute boolAttr(bAttr);
		boolAttr.setHidden(true);

		depNode.findPlug("x3dpre", &isAtty);
		if(isAtty != MStatus::kSuccess) depNode.addAttribute(bAttr);

		MPlug aPlug = depNode.findPlug("x3dpnn");
		MString temp=depNode.name();
		aPlug.setValue(temp);

		MFnNumericAttribute numAtt;
		MObject lostUV = numAtt.create("lostUV", "louv", MFnNumericData::k2Float, 0);
		MFnAttribute tLostUV(lostUV);
		tLostUV.setKeyable(false);
		tLostUV.setHidden(false);

		MObject ambIntensity = numAtt.create("ambientIntensity", "amb", MFnNumericData::kDouble, 0);
		MFnNumericAttribute ambIntAtt(ambIntensity);
		ambIntAtt.setKeyable(true);

		MObject attenuation0 = numAtt.create("attenuation[0]", "atten[0]", MFnNumericData::kDouble, 1);
		MFnNumericAttribute att0att(attenuation0);
		att0att.setKeyable(true);

		MObject attenuation1 = numAtt.create("attenuation[1]", "atten[1]", MFnNumericData::kDouble, 0);
		MFnNumericAttribute att1att(attenuation1);
		att1att.setKeyable(true);

		MObject attenuation2 = numAtt.create("attenuation[2]", "atten[2]", MFnNumericData::kDouble, 0);
		MFnNumericAttribute att2att(attenuation2);
		att2att.setKeyable(true);

		MObject attenuation = numAtt.create("attenuation", "atten", attenuation0, attenuation1, attenuation2);

		MObject description = createAtt.create("description", "descrip", MFnData::kString);

		MObject loop = createNum.create("loop", "lop", MFnNumericData::kBoolean, false);

		MObject audioOut = createNum.create("audioOut", "audOut", MFnNumericData::kBoolean, true);
		MFnAttribute audioAttribute(audioOut);
		audioAttribute.setWritable(false);

		MObject pitch = createNum.create("pitch", "ptch", MFnNumericData::kFloat, 1.0);

		MObject speed = createNum.create("speed", "sped", MFnNumericData::kFloat, 1.0);

		MObject pauseTime = createNum.create("pauseTime", "pauseT", MFnNumericData::kFloat, 0);

		MObject resumeTime = createNum.create("resumeTime", "resumeT", MFnNumericData::kFloat, 0);

		MObject startTime = createNum.create("startTime", "startT", MFnNumericData::kFloat, 0);

		MObject stopTime = createNum.create("stopTime", "stopT", MFnNumericData::kFloat, 0);

		MObject x3dMetadataOut = createNum.create("x3dMetadataOut", "x3dMetaOut", MFnNumericData::kBoolean, true);
		MFnAttribute metaAttribute(x3dMetadataOut);
		metaAttribute.setWritable(false);

//		MObject x3dRouteAtt = createNum.create("x3dRoute", "x3drt", MFnNumericData::kBoolean, true);
//		createNum.setObject(x3dRouteAtt);
//		createNum.setHidden(true);

		MString nType = depNode.typeName();

		MFnNumericAttribute rNum;
		MObject rAtt = rNum.create("x3dRouteAtt", "x3dra", MFnNumericData::kBoolean, true);
		rNum.setObject(rAtt);
		rNum.setWritable(false);

		depNode.findPlug("x3dra", &isAtty);
		if(isAtty != MStatus::kSuccess) depNode.addAttribute(rAtt);

//9999

		if(depNode.typeName() == "bulge") addTextureAttributes(depNode.object());
		if(depNode.typeName() == "checker") addTextureAttributes(depNode.object());
		if(depNode.typeName() == "cloth") addTextureAttributes(depNode.object());
		if(depNode.typeName() == "file") addTextureAttributes(depNode.object());
		if(depNode.typeName() == "fractal") addTextureAttributes(depNode.object());
		if(depNode.typeName() == "grid") addTextureAttributes(depNode.object());
		if(depNode.typeName() == "mountain") addTextureAttributes(depNode.object());
		if(depNode.typeName() == "noise") addTextureAttributes(depNode.object());
		if(depNode.typeName() == "ocean") addTextureAttributes(depNode.object());
		if(depNode.typeName() == "psdFileTex") addTextureAttributes(depNode.object());
		if(depNode.typeName() == "ramp") addTextureAttributes(depNode.object());
		if(depNode.typeName() == "water") addTextureAttributes(depNode.object());

		if(nType.operator ==("x3dPositionInterpolator"))
		{

			MFnNumericAttribute numFn;
			MObject positionX = numFn.create("positionX", "px", MFnNumericData::kFloat);
			numFn.setDefault(0.0);

			MObject positionY = numFn.create("positionY", "py", MFnNumericData::kFloat);
			numFn.setDefault(0.0);

			MObject positionZ = numFn.create("positionZ", "pz", MFnNumericData::kFloat);
			numFn.setDefault(0.0);

			MObject position = numFn.create("position", "pos", positionX, positionY, positionZ);

			depNode.findPlug("pos", &isAtty);
			if(isAtty != MStatus::kSuccess)
			{
				depNode.addAttribute(position);
				depNode.addAttribute(positionX);
				depNode.addAttribute(positionY);
				depNode.addAttribute(positionZ);
			}

			MPlug aPlug = depNode.findPlug("localPosition");
			MObject aObj = aPlug.attribute();
			MFnAttribute aAttr(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("worldPosition");
			aObj = aPlug.attribute();
			aAttr.setObject(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("key");
			MPlug bPlug = aPlug.elementByLogicalIndex(0);
			int intVal = 0;
			bPlug.setValue(intVal);

			bPlug = aPlug.elementByLogicalIndex(1);
			intVal = 1;
			bPlug.setValue(intVal);
		}

		if(nType.operator ==("x3dColorInterpolator"))
		{
			MFnNumericAttribute numFn;
/*
			MObject red = numFn.create("red", "rd", MFnNumericData::kFloat);
			numFn.setObject(red);
			numFn.setDefault(0.0);

			MObject green = numFn.create("green", "grn", MFnNumericData::kFloat);
			numFn.setObject(green);
			numFn.setDefault(0.0);

			MObject blue = numFn.create("blue", "blu", MFnNumericData::kFloat);
			numFn.setObject(blue);
			numFn.setDefault(0.0);
*/
			MObject color = numFn.createColor("color", "clr");

			depNode.findPlug("clr", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(color);

			MPlug aPlug = depNode.findPlug("localPosition");
			MObject aObj = aPlug.attribute();
			MFnAttribute aAttr(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("worldPosition");
			aObj = aPlug.attribute();
			aAttr.setObject(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("key");
			MPlug bPlug = aPlug.elementByLogicalIndex(0);
			int intVal = 0;
			bPlug.setValue(intVal);

			bPlug = aPlug.elementByLogicalIndex(1);
			intVal = 1;
			bPlug.setValue(intVal);
		}

		if(nType.operator ==("x3dOrientationInterpolator"))
		{
			MFnNumericAttribute numFn;
			MFnUnitAttribute unitFn;
			MObject orientationX = unitFn.create("orientationX", "ox", MFnUnitAttribute::kAngle, 0);

			MObject orientationY = unitFn.create("orientationY", "oy", MFnUnitAttribute::kAngle, 0);

			MObject orientationZ = unitFn.create("orientationZ", "oz", MFnUnitAttribute::kAngle, 0);

			MObject orientation = numFn.create("orientation", "ori", orientationX, orientationY, orientationZ);
			
			depNode.findPlug("ori", &isAtty);
			if(isAtty != MStatus::kSuccess)
			{
				depNode.addAttribute(orientation);
				depNode.addAttribute(orientationX);
				depNode.addAttribute(orientationY);
				depNode.addAttribute(orientationZ);
			}

			MPlug aPlug = depNode.findPlug("localPosition");
			MObject aObj = aPlug.attribute();
			MFnAttribute aAttr(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("worldPosition");
			aObj = aPlug.attribute();
			aAttr.setObject(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("key");
			MPlug bPlug = aPlug.elementByLogicalIndex(0);
			int intVal = 0;
			bPlug.setValue(intVal);

			bPlug = aPlug.elementByLogicalIndex(1);
			intVal = 1;
			bPlug.setValue(intVal);
		}
	
		if(nType.operator ==("x3dLoadSensor"))
		{
			MFnNumericAttribute numFn;
			MObject watchList = numFn.create("watchList", "wList", MFnNumericData::kBoolean);
			numFn.setObject(watchList);
			numFn.setArray(true);
			numFn.setWritable(true);
			numFn.setReadable(false);

			depNode.findPlug("wList", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(watchList);
		}

		if(nType.operator ==("joint"))
		{
			MFnNumericAttribute numFn;
			MObject hTranslateX = numFn.create("hTranslateX", "htrx", MFnNumericData::kFloat);
			numFn.setDefault(0.0);

			MObject hTranslateY = numFn.create("hTranslateY", "htry", MFnNumericData::kFloat);
			numFn.setDefault(0.0);

			MObject hTranslateZ = numFn.create("hTranslateZ", "htrz", MFnNumericData::kFloat);
			numFn.setDefault(0.0);

			MObject hTranslate = numFn.create("hTranslate", "htr", hTranslateX, hTranslateY, hTranslateZ);

			depNode.findPlug("htr", &isAtty);
			if(isAtty != MStatus::kSuccess)
			{
				depNode.addAttribute(hTranslate);
				depNode.addAttribute(hTranslateX);
				depNode.addAttribute(hTranslateY);
				depNode.addAttribute(hTranslateZ);
			}

			MFnAttribute aAttr(hTranslate);
			aAttr.setHidden(true);
		}

		if(nType.operator ==("x3dInline") || nType.operator ==("audio") || nType.operator ==("movie"))
		{
			MFnNumericAttribute numFn;
			MObject watchMe = numFn.create("watchMe", "wMe", MFnNumericData::kBoolean, true);
			numFn.setObject(watchMe);
			numFn.setWritable(false);
			numFn.setReadable(true);

			depNode.findPlug("wMe", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(watchMe);
		}

		if(nType.operator ==("x3dScalarInterpolator"))
		{
			MFnNumericAttribute numFn;
			MObject scalar = numFn.create("scalar", "scalr", MFnNumericData::kFloat);

			depNode.findPlug("scalr", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(scalar);

			MPlug aPlug = depNode.findPlug("localPosition");
			MObject aObj = aPlug.attribute();
			MFnAttribute aAttr(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("worldPosition");
			aObj = aPlug.attribute();
			aAttr.setObject(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("key");
			MPlug bPlug = aPlug.elementByLogicalIndex(0);
			int intVal = 0;
			bPlug.setValue(intVal);

			bPlug = aPlug.elementByLogicalIndex(1);
			intVal = 1;
			bPlug.setValue(intVal);
		}

		if(nType.operator ==("x3dBooleanSequencer"))
		{
			MFnNumericAttribute numFn;
			MObject boolean = numFn.create("boolean", "bln", MFnNumericData::kBoolean);

			depNode.findPlug("bln", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(boolean);

			MPlug aPlug = depNode.findPlug("localPosition");
			MObject aObj = aPlug.attribute();
			MFnAttribute aAttr(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("worldPosition");
			aObj = aPlug.attribute();
			aAttr.setObject(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("key");
			MPlug bPlug = aPlug.elementByLogicalIndex(0);
			int intVal = 0;
			bPlug.setValue(intVal);

			bPlug = aPlug.elementByLogicalIndex(1);
			intVal = 1;
			bPlug.setValue(intVal);
		}

		if(nType.operator ==("x3dIntegerSequencer"))
		{
			MFnNumericAttribute numFn;
			MObject integer = numFn.create("integer", "intgr", MFnNumericData::kInt);

			depNode.findPlug("intgr", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(integer);

			MPlug aPlug = depNode.findPlug("localPosition");
			MObject aObj = aPlug.attribute();
			MFnAttribute aAttr(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("worldPosition");
			aObj = aPlug.attribute();
			aAttr.setObject(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("key");
			MPlug bPlug = aPlug.elementByLogicalIndex(0);
			int intVal = 0;
			bPlug.setValue(intVal);

			bPlug = aPlug.elementByLogicalIndex(1);
			intVal = 1;
			bPlug.setValue(intVal);
		}

		if(nType.operator ==("x3dCoordinateInterpolator"))
		{
			MFnTypedAttribute typFn;
			MObject coordinate = typFn.create("coordinate", "coord", MFnData::kVectorArray);

			MObject x3dCoordsIn = createNum.create("x3dCoordsIn", "x3dCI", MFnNumericData::kBoolean, true);
			MFnAttribute newAttribute(x3dCoordsIn);
			newAttribute.setReadable(false);

			depNode.findPlug("coord", &isAtty);
			if(isAtty != MStatus::kSuccess)
			{
				depNode.addAttribute(x3dCoordsIn);
				depNode.addAttribute(coordinate);
			}
			MPlug aPlug = depNode.findPlug("localPosition");
			MObject aObj = aPlug.attribute();
			MFnAttribute aAttr(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("worldPosition");
			aObj = aPlug.attribute();
			aAttr.setObject(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("key");
			MPlug bPlug = aPlug.elementByLogicalIndex(0);
			int intVal = 0;
			bPlug.setValue(intVal);

			bPlug = aPlug.elementByLogicalIndex(1);
			intVal = 1;
			bPlug.setValue(intVal);
		}

		if(nType.operator ==("x3dNormalInterpolator"))
		{
			MFnTypedAttribute typFn;
			MObject normal = typFn.create("normal", "nrml", MFnData::kVectorArray);

			depNode.findPlug("nrml", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(normal);

			MObject x3dNormalsIn = createNum.create("x3dNormalsIn", "x3dNI", MFnNumericData::kBoolean, true);
			MFnAttribute newAttribute(x3dNormalsIn);
			newAttribute.setReadable(false);
			
			depNode.findPlug("x3dNI", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(x3dNormalsIn);

			MPlug aPlug = depNode.findPlug("localPosition");
			MObject aObj = aPlug.attribute();
			MFnAttribute aAttr(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("worldPosition");
			aObj = aPlug.attribute();
			aAttr.setObject(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("key");
			MPlug bPlug = aPlug.elementByLogicalIndex(0);
			int intVal = 0;
			bPlug.setValue(intVal);

			bPlug = aPlug.elementByLogicalIndex(1);
			intVal = 1;
			bPlug.setValue(intVal);
		}

		if(nType.operator ==("rigidSolver"))
		{
		}

		if(nType.operator ==("x3dGroup"))
		{
			MPlug aPlug = depNode.findPlug("translateX");
			MObject aObj = aPlug.attribute();
			MFnAttribute attr(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);
			aPlug.setLocked(true);

			aPlug = depNode.findPlug("translateY");
			aObj = aPlug.attribute();
			attr.setObject(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);
			aPlug.setLocked(true);

			aPlug = depNode.findPlug("translateZ");
			aObj = aPlug.attribute();
			attr.setObject(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);
			aPlug.setLocked(true);

			aPlug = depNode.findPlug("translate");
			aObj = aPlug.attribute();
			attr.setObject(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);
			aPlug.setLocked(true);

			aPlug = depNode.findPlug("scaleX");
			aObj = aPlug.attribute();
			attr.setObject(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);
			aPlug.setLocked(true);

			aPlug = depNode.findPlug("scaleY");
			aObj = aPlug.attribute();
			attr.setObject(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);
			aPlug.setLocked(true);

			aPlug = depNode.findPlug("scaleZ");
			aObj = aPlug.attribute();
			attr.setObject(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);
			aPlug.setLocked(true);

			aPlug = depNode.findPlug("scale");
			aObj = aPlug.attribute();
			attr.setObject(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);
			aPlug.setLocked(true);

			aPlug = depNode.findPlug("rotateX");
			aObj = aPlug.attribute();
			attr.setObject(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);
			aPlug.setLocked(true);

			aPlug = depNode.findPlug("rotateY");
			aObj = aPlug.attribute();
			attr.setObject(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);
			aPlug.setLocked(true);

			aPlug = depNode.findPlug("rotateZ");
			aObj = aPlug.attribute();
			attr.setObject(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);
			aPlug.setLocked(true);

			aPlug = depNode.findPlug("rotate");
			aObj = aPlug.attribute();
			attr.setObject(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);
			aPlug.setLocked(true);

			aPlug = depNode.findPlug("visibility");
			aObj = aPlug.attribute();
			attr.setObject(aObj);
			attr.setHidden(true);
			attr.setKeyable(false);

			aPlug = depNode.findPlug("localPosition");
			aObj = aPlug.attribute();
			MFnAttribute aAttr(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("worldPosition");
			aObj = aPlug.attribute();
			aAttr.setObject(aObj);
			aAttr.setHidden(true);

		}

		if(nType.operator ==("x3dSound"))
		{
			MObject audioIn = createNum.create("audioIn", "audIn", MFnNumericData::kBoolean, true);
			MFnAttribute newAttribute(audioIn);
			newAttribute.setReadable(false);

			depNode.findPlug("audIn", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(audioIn);

			MPlug aPlug = depNode.findPlug("localPosition");
			MObject aObj = aPlug.attribute();
			MFnAttribute aAttr(aObj);
			aAttr.setHidden(true);

			aPlug = depNode.findPlug("worldPosition");
			aObj = aPlug.attribute();
			aAttr.setObject(aObj);
			aAttr.setHidden(true);

		}

		depNode.findPlug("amb", &isAtty);

		if(nType.operator ==("directionalLight") && isAtty != MStatus::kSuccess)
		{
			depNode.addAttribute(ambIntensity);
		}

		if(nType.operator ==("spotLight") && isAtty != MStatus::kSuccess)
		{
			depNode.addAttribute(ambIntensity);
			depNode.addAttribute(attenuation);
		}

		if(nType.operator ==("pointLight") && isAtty != MStatus::kSuccess)
		{
			depNode.addAttribute(ambIntensity);
			depNode.addAttribute(attenuation);
		}
		
		if(nType.operator ==("mesh"))
		{
			depNode.findPlug("louv", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(lostUV);

			MObject x3dCoordsOut = createNum.create("x3dCoordsOut", "x3dCO", MFnNumericData::kBoolean, true);
			MFnAttribute newAttribute(x3dCoordsOut);
			newAttribute.setWritable(false);

			depNode.findPlug("x3dCO", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(x3dCoordsOut);

			MObject x3dCPVOut = createNum.create("x3dCPVOut", "x3dCPVO", MFnNumericData::kBoolean, true);
			newAttribute.setObject(x3dCPVOut);
			newAttribute.setWritable(false);

			depNode.findPlug("x3dCPVO", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(x3dCPVOut);

			MObject x3dTexCoordsOut = createNum.create("x3dTexCoordsOut", "x3dTCO", MFnNumericData::kBoolean, true);
			newAttribute.setObject(x3dTexCoordsOut);
			newAttribute.setWritable(false);

			depNode.findPlug("x3dTCO", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(x3dTexCoordsOut);

			MObject x3dNormalsOut = createNum.create("x3dNormalsOut", "x3dNO", MFnNumericData::kBoolean, true);
			newAttribute.setObject(x3dNormalsOut);
			newAttribute.setWritable(false);

			depNode.findPlug("x3dNO", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(x3dNormalsOut);

			MObject x3dCreaseAngle = createNum.create("x3dCreaseAngle", "x3dCA", MFnNumericData::kFloat, 0);
			createNum.setObject(x3dCreaseAngle);
			createNum.setMin(0);
			createNum.setMax(3.14);

			depNode.findPlug("x3dCA", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(x3dCreaseAngle);

			MObject useLocalX3dCreaseAngle = createNum.create("useLocalX3dCreaseAngle", "useLocX3dCA", MFnNumericData::kBoolean, false);

			depNode.findPlug("useLocX3dCA", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(useLocalX3dCreaseAngle);

			MObject x3dConvex = createNum.create("x3dConvex", "x3dConv", MFnNumericData::kBoolean, true);

			depNode.findPlug("x3dConv", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(x3dConvex);


		}

		if(nType.operator ==("audio"))
		{
			depNode.findPlug("loop", &isAtty);
			if(isAtty != MStatus::kSuccess)
			{
	  			depNode.addAttribute(description);
  				depNode.addAttribute(loop);
  				depNode.addAttribute(pitch);
  				depNode.addAttribute(pauseTime);
	  			depNode.addAttribute(resumeTime);
  				depNode.addAttribute(startTime);
  				depNode.addAttribute(stopTime);
  				depNode.addAttribute(audioOut);
			}
		}
		
		if(nType.operator ==("movie"))
		{
			depNode.findPlug("loop", &isAtty);
			if(isAtty != MStatus::kSuccess)
			{
	  			depNode.addAttribute(loop);
				depNode.addAttribute(speed);
				depNode.addAttribute(pauseTime);
				depNode.addAttribute(resumeTime);
				depNode.addAttribute(startTime);
				depNode.addAttribute(stopTime);
				depNode.addAttribute(audioOut);
			}
		}

		if(nType.operator ==("camera"))
		{
			depNode.findPlug("description", &isAtty);
			if(isAtty != MStatus::kSuccess) depNode.addAttribute(description);
		}

		if(nType.operator ==("x3dMetadataDouble"))
		{
			MStatus metaStat;
			MPlug plugCheck = depNode.findPlug("x3dMetadataOut", &metaStat);
			if(metaStat != MStatus::kSuccess) depNode.addAttribute(x3dMetadataOut);
		}
		if(nType.operator ==("x3dMetadataInteger"))
		{
			MStatus metaStat;
			MPlug plugCheck = depNode.findPlug("x3dMetadataOut", &metaStat);
			if(metaStat != MStatus::kSuccess) depNode.addAttribute(x3dMetadataOut);
		}
		if(nType.operator ==("x3dMetadataFloat"))
		{
			MStatus metaStat;
			MPlug plugCheck = depNode.findPlug("x3dMetadataOut", &metaStat);
			if(metaStat != MStatus::kSuccess) depNode.addAttribute(x3dMetadataOut);
		}
		if(nType.operator ==("x3dMetadataString"))
		{
			MStatus metaStat;
			MPlug plugCheck = depNode.findPlug("x3dMetadataOut", &metaStat);
			if(metaStat != MStatus::kSuccess) depNode.addAttribute(x3dMetadataOut);
		}
		if(nType.operator ==("x3dMetadataSet"))
		{
			MStatus metaStat;
			MPlug plugCheck = depNode.findPlug("x3dMetadataOut", &metaStat);
			if(metaStat != MStatus::kSuccess) depNode.addAttribute(x3dMetadataOut);
		}
	}

//	if(interVal == true)
//	{
		MNodeMessage::addNameChangedCallback(node, webX3DExporter::rawKeeIsRenaming);
//	}
}

void		webX3DExporter::setRawKeeNodeAdded(MObject & node, void* clientData)
{
	
	MFnDependencyNode depNode(node);
	if(depNode.typeName() != "x3dRoute") rawKeeNodeSetups(node);
	else {
		MNodeMessage::addAttributeChangedCallback(node, webX3DExporter::trackSelfDelete);
		MFnNumericAttribute rNum;
		MObject frAtt = rNum.create("x3dRouteFrom", "x3dfr", MFnNumericData::kBoolean, true);

		MObject trAtt = rNum.create("x3dRouteTo", "x3dto", MFnNumericData::kBoolean, true);

		depNode.addAttribute(frAtt);
		depNode.addAttribute(trAtt);
	}
}

void	webX3DExporter::changeSwitchVisibility(MNodeMessage::AttributeMessage msg, MPlug &plug, MPlug &otherPlug, void *clientData)
{
	if ( msg & MNodeMessage::kAttributeSet )
	{
		if(plug.partialName(false, false, false, false, false, true) == "whichChoice")
		{
			double wcd;
			plug.getValue(wcd);

			unsigned int wc = static_cast<unsigned int>(wcd);

			MFnDagNode dNode(plug.node());

			unsigned int i;
			for(i=0; i<dNode.childCount();i++)
			{
				MObject cObj = dNode.child(i);
				MFnDependencyNode cNode(cObj);
				MStatus cStat;
				MPlug vPlug = cNode.findPlug("visibility", &cStat);
				if(cStat.operator ==(MStatus::kSuccess))
				{
					vPlug.setValue(false);
				}
			}

			if(wcd >= 0)
			{
				if(wc >= dNode.childCount())
				{
					for(i=0; i<dNode.childCount();i++)
					{
						MObject cObj = dNode.child(i);
						MFnDependencyNode cNode(cObj);
						MStatus cStat;
						MPlug vPlug = cNode.findPlug("visibility", &cStat);
						if(cStat.operator ==(MStatus::kSuccess))
						{
							vPlug.setValue(true);
						}
					}
				}
				else
				{
					MObject cObj = dNode.child(wc);
					MFnDependencyNode cNode(cObj);
					MStatus cStat;
					MPlug vPlug = cNode.findPlug("visibility", &cStat);
					if(cStat.operator ==(MStatus::kSuccess))
					{
						vPlug.setValue(true);
					}
				}
			}
		}
	}
}

void	webX3DExporter::trackSelfDelete(MNodeMessage::AttributeMessage msg, MPlug &plug, MPlug &otherPlug, void *clientData)
{
	if ( msg & MNodeMessage::kAttributeSet )
	{
		if(plug.partialName(false, false, false, false, false, true) == "sdDoIt")
		{
			bool delVal = false;
			plug.getValue(delVal);
			if(delVal)
			{
				MObject mObj = plug.node();
				MFnDependencyNode depFn(mObj);
//				MGlobal::executeCommand("delete "+depFn.name());

    				// Create an MDGModifier
    				MDGModifier modifier;

    				// Add the delete operation to the modifier
    				MStatus status = modifier.deleteNode(mObj);
    				if (!status) MGlobal::displayError("Failed to delete node: " + depFn.name());
			}
		}
	}
}

void		webX3DExporter::showSelectedRoute(void *clientData)
{
	MGlobal::executeCommand("x3dProcessSelectedRoute");
}

void		webX3DExporter::setRawKeeNodeRemoved(MObject &node, void *clientData)
{
		MFnDependencyNode depNode(node);
		if(depNode.typeName() != "x3dRoute")
		{
			MGlobal::displayInfo("Not an X3D Route!");
			MGlobal::displayInfo(depNode.typeName());

			MStringArray routeNames;
			MGlobal::executeCommand("ls -type x3dRoute", routeNames);

			unsigned int rnLen = routeNames.length();
			MString rstring("Total number of X3D Routes");
			rstring += rnLen;
			MGlobal::displayInfo(rstring);

			unsigned int i;
			for(i=0; i<rnLen; i++)
			{
//				MFnDependencyNode depFn = getMyDepNode(routeNames.operator [](i));
				MFnDependencyNode depFn(getMyDepNodeObj(routeNames.operator [](i)));


				MPlug nameFrom = depFn.findPlug("nameFrom1");
				MPlug nameTo = depFn.findPlug("nameTo1");

				MString nf1;
				MString nf2;
				MString delName = depNode.name();
				nameFrom.getValue(nf1);
				nameTo.getValue(nf2);

				if(nf1.operator ==(delName) || (nf2.operator ==(delName)))
				{
					MPlug cs = depFn.findPlug("checkString");
					cs.setValue(delName);

					MPlug sd = depFn.findPlug("selfDelete");
					bool sdVal = false;
					sd.getValue(sdVal);

					MPlug sddi = depFn.findPlug("sdDoIt");
					sddi.setValue(sdVal);
				}
			}
		}
		else MGlobal::displayInfo("Deleting an X3D Route");

}

void		webX3DExporter::rawKeeIsRenaming(MObject & node, void * clientData)
{
		MFnDependencyNode depNode(node);
		if(depNode.typeName() != "x3dRoute")
		{
			MFnDependencyNode depNode(node);
			MPlug oldNamePlug = depNode.findPlug("x3dpnn");
			MString oldNameValue;
			oldNamePlug.getValue(oldNameValue);

			MStringArray routeNames;
			MGlobal::executeCommand("ls -type x3dRoute", routeNames);

			unsigned int rnLen = routeNames.length();

			unsigned int i;
			for(i=0; i<rnLen; i++)
			{
//				MFnDependencyNode depFn = getMyDepNode(routeNames.operator [](i));
				MFnDependencyNode depFn(getMyDepNodeObj(routeNames.operator [](i)));
				MPlug nameFrom = depFn.findPlug("nameFrom1");
				MPlug nameTo = depFn.findPlug("nameTo1");

				MString nf1;
				MString nf2;
				MString newName = depNode.name();
				nameFrom.getValue(nf1);
				nameTo.getValue(nf2);
				if(nf1.operator ==(oldNameValue)) nameFrom.setValue(newName);
				if(nf2.operator ==(oldNameValue)) nameTo.setValue(newName);
			}

			MString temp=depNode.name();
			oldNamePlug.setValue(temp);
		}
}

void	webX3DExporter::x3dSceneUpdateMethod(void* clientData)
{
//	int isProcessing = 0;
//	MGlobal::executeCommand("optionVar -q x3dIsProcTree", isProcessing);
//	if(isProcessing == 0) runWeb3dSGFromAPI(0);
}

void	webX3DExporter::runWeb3dSGFromAPI(int updateMethod)
{
	int fValue;
	MGlobal::executeCommand("optionVar -q x3dEncoding", fValue);

	int intVal = 0;
	bool isFrom = true;
	MString tempString = "";

	MString newOptions("");
	MGlobal::executeCommand("optionVar -q x3dUseEmpties", intVal);
	tempString.set(intVal);

	newOptions.operator +=("x3dUseEmpties*");
	newOptions.operator +=(tempString);
	newOptions.operator +=("*");

	MGlobal::executeCommand("optionVar -q x3dExportMetadata", intVal);
	tempString.set(intVal);

	newOptions.operator +=("x3dExportMetadata*");
	newOptions.operator +=(tempString);
	newOptions.operator +=("*");

	MGlobal::executeCommand("optionVar -q x3dCPV", intVal);
	tempString.set(intVal);

	newOptions.operator +=("x3dCPV*");
	newOptions.operator +=(tempString);
	newOptions.operator +=("*");

	MGlobal::executeCommand("optionVar -q x3dIsFrom", isFrom);

	MGlobal::executeCommand("optionVar -q x3dNPV", intVal);
	tempString.set(intVal);

	MGlobal::executeCommand("optionVar -q x3dRigidBodyExport", intVal);
	tempString.set(intVal);

	MGlobal::executeCommand("optionVar -q x3dHAnimExport", intVal);
	tempString.set(intVal);

	newOptions.operator +=("x3dNPV*");
	newOptions.operator +=(tempString);
	newOptions.operator +=("*");

	newOptions.operator +=("x3dRigidBodyExport*");
	newOptions.operator +=(tempString);
	newOptions.operator +=("*");

	newOptions.operator +=("x3dHAnimExport*");
	newOptions.operator +=(tempString);
	newOptions.operator +=("*");

	newOptions.operator +=("updateMethod*");
	newOptions.operator +=(updateMethod);
//	newOptions.operator +=("*");

	constructWeb3DScenegraphTree(fValue, newOptions, isFrom);
}

/*
MFnDependencyNode webX3DExporter::getMyDepNode(MString nodeName)
{
	MSelectionList tempList;
	tempList.clear();
	tempList.add(nodeName);
	MItSelectionList newMItSel(tempList);
	MObject tObject;
	newMItSel.getDependNode(tObject);
	MFnDependencyNode newDep(tObject);
	return newDep;
}
*/

MObject webX3DExporter::getMyDepNodeObj(MString nodeName)
{
	MSelectionList tempList;
	tempList.clear();
	tempList.add(nodeName);
	MItSelectionList newMItSel(tempList);
	MObject tObject;
	newMItSel.getDependNode(tObject);
	return tObject;
}

//void	webX3DExporter::addTextureAttributes(MFnDependencyNode depNode)
void	webX3DExporter::addTextureAttributes(MObject mObj)
{
	MFnDependencyNode depNode(mObj);
	MFnNumericAttribute numFn;
	MFnTypedAttribute typeFn;
	MFnEnumAttribute enumfn;
/*
	MObject imageFormat0 = numFn.create("imageFormatCurrent", "imgfmtcur", MFnNumericData::kBoolean, true);
	MObject imageFormat1 = numFn.create("imageFormatGif", "imgfmtgif", MFnNumericData::kBoolean, false);
	MObject imageFormat2 = numFn.create("imageFormatJpg", "imgfmtjpg", MFnNumericData::kBoolean, false);
	MObject imageFormat3 = numFn.create("imageFormatPng", "imgfmtpng", MFnNumericData::kBoolean, false);
	MObject x3dNodeType = numFn.create("exportAsPixelTexture", "x3dpix",  MFnNumericData::kBoolean, false);

	MObject imageMode0 = numFn.create("doNotSpecify", "dns", MFnNumericData::kBoolean, true);
	MObject imageMode1 = numFn.create("singleTextureModeReplace", "stmr", MFnNumericData::kBoolean, false);
	MObject imageMode2 = numFn.create("singleTextureModeModulate", "stmm", MFnNumericData::kBoolean, false);
	MObject imageMode3 = numFn.create("singleTextureModeADD", "stma", MFnNumericData::kBoolean, false);
*/
	MObject adjustSize = numFn.create("adjustSize", "adjsize", MFnNumericData::kBoolean, false);
	MObject imageDimensionW = numFn.create("imageDimensionW", "imgdimw", MFnNumericData::kInt, 256);
	MObject imageDimensionH = numFn.create("imageDimensionH", "imgdimh", MFnNumericData::kInt, 256);

	MObject formatChoice = enumfn.create("formatChoice", "fChoice", 0);
	enumfn.addField("Current", 0);
	enumfn.addField("GIF", 1);
	enumfn.addField("JPG", 2);
	enumfn.addField("PNG", 3);

	MObject textureType = enumfn.create("textureOption", "tOption", 0);
	enumfn.addField("ImageTexture", 0);
	enumfn.addField("PixelTexture", 1);

	MObject pixelLength = enumfn.create("pixelLength", "pLength", 2);
	enumfn.addField("0x00", 0);
	enumfn.addField("0x0000", 1);
	enumfn.addField("0x000000", 2);
	enumfn.addField("0x00000000", 3);


	MObject imageMode = enumfn.create("singleTextureMode", "stMode", 0);
	enumfn.addField("Default", 0);
	enumfn.addField("MultiTexture Replace", 1);
	enumfn.addField("MultiTexture Modulate", 2);
	enumfn.addField("MultiTexture Add", 3);

	MStatus isAtty;
	depNode.findPlug("formatChoice", &isAtty);
	if(isAtty != MStatus::kSuccess)
	{
		depNode.addAttribute(formatChoice);
		depNode.addAttribute(textureType);
		depNode.addAttribute(pixelLength);
		depNode.addAttribute(imageMode);

/*
		depNode.addAttribute(imageFormat0);
		depNode.addAttribute(imageFormat1);
		depNode.addAttribute(imageFormat2);
		depNode.addAttribute(imageFormat3);
		depNode.addAttribute(x3dNodeType);
		depNode.addAttribute(imageMode0);
		depNode.addAttribute(imageMode1);
		depNode.addAttribute(imageMode2);
		depNode.addAttribute(imageMode3);
*/
	
		depNode.addAttribute(adjustSize);
		depNode.addAttribute(imageDimensionW);
		depNode.addAttribute(imageDimensionH);
	}
	
}


