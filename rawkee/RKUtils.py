import sys
import maya.api.OpenMaya as aom
import maya.cmds         as cmds
import maya.mel          as mel

def trackSelfDelete(msg, plug, otherPlug, data):
    if msg == aom.MNodeMessage.kAttributeSet:
        if plug.partialname(False, False, False, False, False, True) == "sdDoIt":

            delVal = plug.asBool()
            
            if delVal == True:
                mObj = plug.node()
                depFn = aom.MFnDependencyNode(mObj)
                
                modifier = aom.MDGModifier()
                modifier.doIt()
                modifier.deleteNode(mObj, False)
                modifier.doIt()
                
    
def rawKeeNodeSetups(nodeObj):
    depNode = aom.MFnDependencyNode(nodeObj)

    if depNode != None:
        createMeta = aom.MFnNumericAttribute()
        x3dMetadataIn = createMeta.create("x3dMetadataIn", "x3dMetaIn", aom.MFnMeshData.kBoolen, True)
        x3dMetadataIn.readable = False
        depNode.addAttribute(x3dMetadataIn)
        
    prePlug = depNode.findPlug("x3dpre")
    interPlug = depNode.findPlug("intermediateObject")
    interVal = interPlug.asBool()
    
    if depNode != None:
        pass

'''
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
'''


def getMyDepNodeObj(nodeName):
    tempList = aom.MGlobal.getActiveSelectionList() #MSelectionList()
    tempList.clear()
    tempList.add(nodeName)
    newMItSel = aom.MItSelectionList(tempList)
    tObject = newMItSel.getDependNode()
    return tObject
    


def setRawKeeNodeAdded(nodeObj, data):
    depNode = aom.MFnDependencyNode(nodeObj)

    if depNode.typeName != "x3dRoute":
        rawKeeNodeSetups(nodeObj)
    else:
        aom.MNodeMessage.addAttributeAddedOrRemovedCallback(nodeObj, trackSelfDelete);
        
        numFn = aom.MFnNumericAttribute()
        frAtt = numFn.create("x3dRouteFrom", "x3dfr", aom.MFnNumericData.kBoolean, true)
        trAtt = numFn.create("x3dRouteTo",   "x3dto", aom.MFnNumericData.kBoolean, true)
        
        depNode.addAttribute(frAtt)
        depNode.addAttribute(trAtt)


        
def setRawKeeNodeRemoved(nodeObj, data):
    depNode = aom.MFnDependencyNode(nodeObj)

    if depNode.typeName != "x3dRoute":
        print("Not an X3D Route!")
        print(depNode.typeName)
        
        routeNames = cmds.ls( type='x3dRoute')
        rnLen = len(routeNames)
        print("Total number of X3D Routes: " + str(rnLen))
        
        for rNames in routeNames:
            depFn = aom.MFnDependencyNode(getMyDepNodeObj(rNames))
            nameFrom = depFn.findPlug("nameFrom1")
            nameTo = depFn.findPlug("nameTo1")
            
            delName = depNode.name
            
            nf1 = nameFrom.asString()
            nf2 = nameTo.asString()
            
            if nf1 == delName or nf2 == delName:
                depFn.findPlug("checkString").setString(delName)
                depFn.findPlug("selfDelete").setBool(False)
                depFn.findPlug("sdDoIt").setBool(False)
    else:
        print("Deleting an X3D Route")

        

def setX3DProcTreeTrue():
    cmds.optionVar(iv=('x3dIsProcTree', 1))
#	optionVar -iv x3dIsProcTree 1;


def setX3DProcTreeFalse():
    cmds.optionVar(iv=('x3dIsProcTree', 0))
#	optionVar -iv x3dIsProcTree 0;



print("RKUtils is loaded")

# TODO: Since a MEL utility script will be required for AE Templates, everythin here would be more easily be implemented in MEL 
# Especiallly since I can just copy everything over from the old RawKee MEL scripts. I will most likely remove this Python Script.

# Creating the MEL Command for setting the File Options for X3D Import/Export
class RKX3DOptions(aom.MPxCommand):
    kPluginCmdName = "rkX3DOptions"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKX3DOptions()
        
    def doIt(self, args):
        printDefRKOptVars()



# Creating the MEL Command for the RawKee's function to activate export function
class RKCmdTest(aom.MPxCommand):
    kPluginCmdName = "rkCmdTest"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKCmdTest()
        
    def doIt(self, args):
        print("RK Command Test Complete")

# Function that prints the Maya global variables required by RawKee
# TODO: Grab RawKee OptionVars, and print them out.
def printDefRKOptVars():
    print("X3D File Options")

