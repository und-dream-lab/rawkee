import sys
import os
from rawkee.rkx3d import *
from typing import Final


encx: Final[int] = 0 # X3D  XML     Encoding (*.x3d )
encv: Final[int] = 1 # X3D  Classic Encoding (*.x3dv)
encj: Final[int] = 2 # X3D  JSON    Encoding (*.x3dj)
ench: Final[int] = 3 # X3D  HTML5   Encoding (*.html)
encw: Final[int] = 4 # VRML 97      Encoding (*.wrl )


class RKSceneTraversal():
    def __init__(self):
        print("RKSceneTraversal")
        
        self.tabs = 0
        self.iofile = None
        self.enc = encx

        self.profileType = "Core"
        self.x3dVersion  = "4.1"
        self.profDict    = {}
        self.compDict    = {}
        self.metatags    = []
        
        # 36
        self.full           = {'Core':2,                'Time':2,                   'Networking':4,             'Grouping':3,
                            'Rendering':5,              'Shape':4,                  'Geometry3D':4,             'Geometry2D':2,
                            'Text':1,                   'Sound':3,                  'Lighting':3,               'Texturing':4,
                            'Interpolation':5,          'PointingDeviceSensor':1,   'KeyDeviceSensor':2,
                            'EnvironmentalSensor':3,    'Navigation':3,             'EnvironmentalEffects':4,   'Geospatial':2,
                            'HAnim':3,                  'NURBS':4,                  'DIS':2,                    'Scripting':1,
                            'EventUtilities':1,         'Shaders':1,                'CADGeometry':2,            'Texturing3D':2,
                            'CubeMapTexturing':3,       'Layering':1,               'Layout':2,                 'RigidBodyPhysics':2,
                            'Picking':3,                'Followers':1,              'ParticleSystems':3,        'VolumeRendering':4,
                            'TextureProjection':2}

        # 20
        self.immersive      = {'Core':2,                'Time':1,                   'Networking':3,             'Grouping':2,
                            'Rendering':3,              'Shape':2,                  'Geometry3D':4,             'Geometry2D':1,
                            'Text':1,                   'Sound':1,                  'Lighting':2,               'Texturing':3,
                            'Interpolation':2,          'PointingDeviceSensor':1,   'KeyDeviceSensor':2,
                            'EnvironmentalSensor':2,    'Navigation':2,             'EnvironmentalEffects':2,   'Scripting':1,
                            'EventUtilities':1}
        
        # 16
        self.interactive    = {'Core':1,                'Time':1,                   'Networking':2,             'Grouping':2,
                            'Rendering':3,              'Shape':1,                  'Geometry3D':3,             'Lighting':2,
                            'Texturing':2,              'Interpolation':2,          'PointingDeviceSensor':1,   'KeyDeviceSensor':1,
                            'EnvironmentalSensor':1,    'Navigation':1,             'EnvironmentalEffects':1,   'EventUtilities':1}

        # 14
        self.mp4Interactive = {'Core':1,                'Time':1,                   'Networking':2,             'Grouping':2,
                            'Rendering':1,              'Shape':1,                  'Geometry3D':2,             'Lighting':2,
                            'Texturing':1,              'Interpolation':2,          'PointingDeviceSensor':1,   
                            'EnvironmentalSensor':1,    'Navigation':1,             'EnvironmentalEffects':1}

        # 12
        self.interchange    = {'Core':1,                'Time':1,                   'Networking':1,             'Grouping':1,
                            'Rendering':3,              'Shape':1,                  'Geometry3D':2,             'Lighting':1,
                            'Texturing':2,              'Interpolation':2,          'Navigation':1,             'EnvironmentalEffects':1}
        
        # 10
        self.cadInterchange = {'Core':1,                'Networking':2,             'Grouping':1,               'Rendering':4,
                            'Shape':2,                  'Lighting':1,               'Texturing':2,              'Navigation':3,
                            'Shaders':1,                'CADGeometry':2}
                            
        self.profiles = {"Full":self.full, "Immersive":self.immersive, "Interactive":self.interactive, "MPG4Interactive":self.mp4Interactive, "Interchange":self.interchange, "CADInterchange":self.cadInterchange}

        
    def startExport(self, x3dDoc, iofile, encoding):
        self.iofile = iofile
        if   encoding == "x3d":
            self.enc = encx
        elif encoding == "x3dv":
            self.enc = encv
        elif encoding == "x3dj" or encoding == "json":
            self.enc = encj
        elif encoding == "html":
            self.enc = ench
            
        self.writeHeader()
        scLen = len(x3dDoc.Scene.children)
        for idx in range(scLen):
            node = x3dDoc.Scene.children[idx]
            
            tMulti = False
            if encoding == "x3dj" or encoding == "json":
                tMulti = True
            if idx < (scLen - 1):
                self.processNode(node, tMulti, True, cField="children")
            else:
                self.processNode(node, tMulti, False, cField="children")
        self.writeFooter()

        self.profileType = "Core"
        self.x3dVersion  = "4.1"
        self.profDict.clear()
        self.compDict.clear()
        self.metatags.clear()
        
        print("File Output has completed.")

    def processNode(self, node, isMulti, addComma, cField=""):
        nType   = type(node).__name__
        
        sFieldsList = []
        mFieldsList  = []
        
        sNodeList  = []
        mNodeList   = []

        #compNode = self.instantiateNodeFromString(nType)
        compNode = instantiateNodeFromString(nType)[0]
        pastMeta = False
        nDict = vars(node)

        for key, value in nDict.items():
            if key == "rkWeightsData":
                print("Debug: " + node.DEF + ", " + key)
            keyp = key.split('_')
            if   keyp[1] == "X3DNode":
                if   keyp[3] == "DEF" and node.DEF != None:
                    sFieldsList.append("DEF")
                    
                elif keyp[3] == "USE" and node.USE != None:
                    sFieldsList.append("USE")
                    
                elif keyp[3] == "metadata": #and pastMeta == False:
                    pastMeta = True
                    
            elif keyp[1] == "ROUTE":
                if   keyp[3] == "fromField" and value != "":
                    sFieldsList.append("fromField")
                    
                elif keyp[3] == "toField"   and value != "":
                    sFieldsList.append("toField")
                
                elif keyp[3] == "fromNode"  and value != "":
                    sFieldsList.append("fromNode")
                
                elif keyp[3] == "toNode"    and value != "":
                    sFieldsList.append("toNode")
            
            #elif keyp[1] == "field":
            #    if   keyp[3] == "name" and value != "":
            #        sFieldsList.append("name")
            #        
            #    elif keyp[3] == "type" and value != "":
            #        sFieldsList.append("type")
            #        
            #    elif keyp[3] == "accessType" and value != "":
            #        sFieldsList.append("accessType")
            #        
            #    elif keyp[3] == "value" and value != "":
            #        sFieldsList.append("value")
            #        
            #    elif keyp[3] == "children" and value != None:
            #        mNodeList.append("children")
                    
            if pastMeta == False:# and keyp[3] == nType:
                continue
                
            #if keyp[3] == "metadata":
            #    print(compNode)
                
            # For some reason the '_Normal__vector' attribute doesn't show up as an instance of a list, eventhough it should.
            # So I added a one-off check for the vector attribute.
            if  isinstance(value, list): #or (keyp[1] == "Normal" and keyp[3] == "vector"):
                if getattr(compNode,keyp[3]) != value:#len(value) > 0:
                    if isinstance(value[0], (str, float, int, tuple, bool, type(None) ) ):
                        if value[0] != None:
                            mFieldsList.append(keyp[3])
                            #print('M Field: ' + keyp[3])
                    else:
                        mNodeList.append(keyp[3])

            else:
                # This is a fix for lighting nodes that have the 'global_' field.
                if keyp[3] == "global":
                    keyp[3] = "global_"
                if getattr(compNode,keyp[3]) != value:
                    if isinstance(value, (str, float, int, tuple, bool, type(None) ) ):
                        #if value != None:
                        sFieldsList.append(keyp[3])
                        #print('S Field: ' + keyp[3])
                    else:
                        #if getattr(compNode,keyp[3]) != value:
                        sNodeList.append(keyp[3])

        compNode = None
        
        self.processSortedNode(node.NAME(), node, sFieldsList, mFieldsList, sNodeList, mNodeList, isMulti, addComma, cField)


    def processSortedNode(self, nType, node, sFieldList, mFieldList, sNodeList, mNodeList, isMulti, addComma, cField):
        
        if sFieldList[0] == "USE":
            self.processUsed(nType, node, isMulti, addComma, cField)
        else:
            if   self.enc == encx:
                self.processNodeAsXML(    nType, node, True,  sFieldList, mFieldList, sNodeList, mNodeList, cField)
            elif self.enc == ench:
                self.processNodeAsHTML(   nType, node, True,  sFieldList, mFieldList, sNodeList, mNodeList, cField)
            elif self.enc == encv:
                self.processNodeAsClassic(nType, node, False, sFieldList, mFieldList, sNodeList, mNodeList, isMulti)
            elif self.enc == encj:
                self.processNodeAsJSON(   nType, node, False, sFieldList, mFieldList, sNodeList, mNodeList, isMulti, addComma)


    def processUsed(self, nType, node, isMulti, addComma, cField):
        mainline = ""
        if   self.enc == encx:
            mainline = "<" + nType + " USE='" + node.USE + "'"
            if cField != "":
                mainline += " containerField='" + cField + "'"
            mainline += "/>"
            
        elif self.enc == encv:
            mainline = "USE " + node.USE
            if isMulti == False:
                self.writeRemaining(mainline)
                return
            
        elif self.enc == encj:
            mainline = '{"' + nType + '":{"@USE":"' + node.USE + '"}}'
            if addComma == True:
                mainline += ","
            if isMulti == False:
                self.writeRemaining(mainline)
                return
            
        elif self.enc == ench:
            mainline = "<" + nType + " USE='" + node.USE + "'"
            if cField != "":
                mainline += " containerField='" + cField + "'"
            mainline += "></" + nType + ">"
            
        self.writeLine(mainline)


    def processROUTEAsClassic(self, node, sFieldList):
        self.writeLine("ROUTE " + getattr(node, sFieldList[1]) + "." + getattr(node, sFieldList[0]) + " TO " + getattr(node, sFieldList[3]) + "." + getattr(node, sFieldList[2]))


    def processFieldAsClassic(self, node, sFieldList, mFieldList, isMulti):
        fieldText = "field " + node.type + " " + node.name
        if node.type == "SFNode":
            self.itabs()
            self.writePrefix("children")
            self.processNode(node.children[0], False, False)
            self.dtabs()
            
        elif node.type == "MFNode": # TODO Implement Later for Script, ExternProto, and Proto nodes
            pass
            
        else:
            fieldText = fieldText + " " + node.value
            if isMulti == True:
                self.writeLine(fieldText)
            else:
                self.writeRemaining(fieldText)
        
        
    # This is only setup to handle Shader custom fields
    # TODO Change update Function to handle fields for Script, ExternProto, and Proto nodes
    def processNodeAsClassic(self, nType, node, showCF, sFieldList, mFieldList, sNodeList, mNodeList, isMulti):
        mainline = ""
        
        if nType == "ROUTE":
            self.processROUTEAsClassic(node, sFieldList)
            return
            
        if nType == "field":
            self.processFieldAsClassic(node, sFieldList, mFieldList, isMulti)
            return
            
        if isMulti == True:
            self.writeLine(     "DEF " + node.DEF + " " + nType + " {")
        else:
            self.writeRemaining("DEF " + node.DEF + " " + nType + " {")

        self.itabs()
        
        sflLen = len(sFieldList)
        mflLen = len(mFieldList)
        snlLen = len(sNodeList)
        mnlLen = len(mNodeList)
        for fIdx in range(sflLen):
            tField = sFieldList[fIdx]

            if tField == "DEF":
                # Don't write out DEF as a node field
                continue
            # This is a fix for lighting nodes that have the 'global_' field.
            elif tField == "global_":
                tField = "global"
                
            value = getattr(node, sFieldList[fIdx])
            sValue = ""
            
            if isinstance(value, tuple):
                sValue = ' '.join([str(item) for item in value])
                sValue = sValue.strip()
                
            elif isinstance(value, bool):
                if value == True:
                    sValue = 'TRUE'
                else:
                    sValue = 'FALSE'
                    
            elif isinstance(value, str):
                sValue = '"' + value + '"'
                if value == "":
                    # if the string has nothing in it, then don't export this field
                    continue
                
            else:
                sValue = str(value)
                
            pVal = tField + ' ' + sValue
            
            self.writeLine(pVal)
            
        for idx in range(mflLen):
            field = mFieldList[idx]
            
            values = getattr(node, field)
            sValue = ""
            
            if isinstance(values[0], tuple):
                tvLen = len(values)
                for vIdx in range(tvLen):
                    tValue = ' '.join([str(item) for item in values[vIdx]])
                    tValue = tValue.strip()
                    sValue = sValue + tValue
                    if vIdx < (tvLen - 1):
                        sValue = sValue + ', '
                
            elif isinstance(values[0], bool):
                tvLen = len(values)
                for vIdx in range(tvLen):
                    if value[vIdx] == True:
                        sValue = sValue + 'TRUE'
                    else:
                        sValue = sValue + 'FALSE'
                    if vIdx < (tvLen - 1):
                        sValue = sValue + ', '
                
            elif isinstance(values[0], str):
                tvLen = len(values)
                for vIdx in range(tvLen):
                    sValue = sValue + '"' + values[vIdx] + '"'
                    if vIdx < (tvLen - 1):
                        sValue = sValue + ', '
                
            else:
                tvLen = len(values)
                for vIdx in range(tvLen):
                    sValue = sValue + str(values[vIdx])
                    if vIdx < (tvLen - 1):
                        sValue = sValue + ', '
        
            pVal = field + ' [ ' + sValue + ' ]'
            
            self.writeLine(pVal)
        
        for nIdx in range(snlLen):
            field = sNodeList[nIdx]
            tNode = getattr(node, field)
            sValue = field
            self.writePrefix(sValue)
            self.processNode(tNode, False, False)

        for nIdx in range(mnlLen):
            mField = mNodeList[nIdx]
            mList = getattr(node, mField)
            
            vValue = mField + ' ['
            self.writeLine(vValue)
            self.itabs()
                        
            vLen = len(mList)
            for vIdx in range(vLen):
                mNode = mList[vIdx]
                self.processNode(mNode, True, False)
            self.dtabs()
            self.writeLine(']')
        
        self.dtabs()
        self.writeLine("}")


    def processROUTEAsJSON(self, node, sFieldList, isMulti, addComma):# 
        if isMulti == True:
            self.writeLine(     '{ "ROUTE":')
        else:
            self.writeRemaining('{ "ROUTE":')
        self.itabs()
        self.writeLine('{')
        self.itabs()

        fromNode  = '"@' + sFieldList[1] + '": "' + getattr(node, sFieldList[1]) + '",'
        fromField = '"@' + sFieldList[0] + '": "' + getattr(node, sFieldList[0]) + '",'
        toNode    = '"@' + sFieldList[3] + '": "' + getattr(node, sFieldList[3]) + '",'
        toField   = '"@' + sFieldList[2] + '": "' + getattr(node, sFieldList[2]) + '"'
        self.writeLine(fromNode)
        self.writeLine(fromField)
        self.writeLine(toNode)
        self.writeLine(toField)

        self.dtabs()
        self.writeLine('}')
        self.dtabs()
        if addComma == True:
            self.writeLine('},')
        else:
            self.writeLine('}')


    # This is only setup to handle Shader custom fields
    # TODO Change update Function to handle fields for Script, ExternProto, and Proto nodes
    def processFieldAsJSON(self, node, sFieldList, mNodeList, isMulti, addComma):
        if isMulti == True:
            self.writeLine(     '{ "field":')
        else:
            self.writeRemaining('{ "field":')
        self.itabs()
        self.writeLine('{')
        self.itabs()
        fieldName  = '"@name": "' + node.name + '",'
        fieldType  = '"@type": "' + node.type + '",'
        fieldAType = '"@accessType": "' + node.accessType + '",'
        self.writeLine(fieldName)
        self.writeLine(fieldType)
        self.writeLine(fieldAType)
        if node.type == "SFNode":
            sValue = '"-children":'
            self.writePrefix(sValue)
            hasComma = False
            self.processNode(node.children[0], False, hasComma)
            
        elif node.type == "MFNode":
            pass # TODO Implement Later for Script, ExternProto, and Proto nodes
            
        else:
            fieldValue = '"@value": "' + node.value + '"'
            self.writeLine(fieldValue)
        self.dtabs()
        self.writeLine('}')
        self.dtabs()
        if addComma == True:
            self.writeLine('},')
        else:
            self.writeLine('}')
        
        
    def processNodeAsJSON(self, nType, node, showCF, sFieldList, mFieldList, sNodeList, mNodeList, isMulti, addComma):
        mainline = ''

        if nType == "ROUTE":
            self.processROUTEAsJSON(node, sFieldList, isMulti, addComma)
            return

        if nType == "field":
            self.processFieldAsJSON(node, sFieldList, mNodeList, isMulti, addComma)
            return

        if isMulti == True:
            self.writeLine(     '{ "' + nType + '":')
        else:
            self.writeRemaining('{ "' + nType + '":')
        self.itabs()
        self.writeLine('{')
        self.itabs()
        
        sflLen = len(sFieldList) # sflLen
        mflLen = len(mFieldList) # mflLen
        snlLen = len(sNodeList)  # snlLen
        mnlLen = len(mNodeList)  # mnlLen
        for fIdx in range(sflLen):
            tField = sFieldList[fIdx]

            # This is a fix for lighting nodes that have the 'global_' field.
            if tField == "global_":
                tField = "global"

                
            value = getattr(node, sFieldList[fIdx])
            sValue = ""
            
            if isinstance(value, tuple):
                sValue = ', '.join([str(item) for item in value])
                sValue = sValue.strip()
                sValue = '[ ' + sValue + ' ]'
                
            elif isinstance(value, bool):
                if value == True:
                    sValue = 'true'
                else:
                    sValue = 'false'
                    
            elif isinstance(value, str):
                sValue = '"' + value + '"'
                if value == "":
                    # if the string has nothing in it, then don't export this field
                    continue
                
            else:
                sValue = str(value)
                
            pVal = '"@' + tField + '": ' + sValue
            
            if fIdx < (sflLen - 1) or mflLen > 0 or snlLen > 0 or mnlLen > 0:
                pVal = pVal + ','

            self.writeLine(pVal)
            
        for idx in range(mflLen):
            field = mFieldList[idx]
            
            values = getattr(node, field)
            sValue = ""
            
            if isinstance(values[0], tuple):
                tvLen = len(values)
                for vIdx in range(tvLen):
                    tValue = ', '.join([str(item) for item in values[vIdx]])
                    tValue = tValue.strip()
                    
                    sValue = sValue + tValue
                    if vIdx < (tvLen - 1):
                        sValue = sValue + ', '
                
            elif isinstance(values[0], bool):
                tvLen = len(values)
                for vIdx in range(tvLen):
                    if values[vIdx] == True:
                        sValue = sValue + 'true'
                    else:
                        sValue = sValue + 'false'
                    if vIdx < (tvLen - 1):
                        sValue = sValue + ', '
                
            elif isinstance(values[0], str):
                tvLen = len(values)
                for vIdx in range(tvLen):
                    sValue = sValue + '"' + values[vIdx] + '"'
                    if vIdx < (tvLen - 1):
                        sValue = sValue + ', '
                
            else:
                tvLen = len(values)
                for vIdx in range(tvLen):
                    sValue = sValue + str(values[vIdx])
                    if vIdx < (tvLen - 1):
                        sValue = sValue + ', '
        
            pVal = '"@' + field + '": [ ' + sValue + ' ]'
            
            if idx < (mflLen - 1) or snlLen > 0 or mnlLen > 0:
                pVal = pVal + ','
                
            self.writeLine(pVal)
        
        for nIdx in range(snlLen):
            field = sNodeList[nIdx]
                
            tNode = getattr(node, field)
            
            sValue = '"-' + field + '":'
            
            self.writePrefix(sValue)
            
            hasComma = False
            if nIdx < (snlLen - 1) or mnlLen > 0:
                hasComma = True
                
            self.processNode(tNode, False, hasComma)

        for nIdx in range(mnlLen):
            mField = mNodeList[nIdx]
            mList = getattr(node, mField)
            
            vValue = '"-' + mField + '": ['
            self.writeLine(vValue)
            self.itabs()
                        
            vLen = len(mList)
            for vIdx in range(vLen):
                mNode = mList[vIdx]
                hasComma = False
                if vIdx < (vLen - 1):
                    hasComma = True
                    
                self.processNode(mNode, True, hasComma)
            self.dtabs()
            self.writePrefix(']')
            
            if nIdx < (mnlLen - 1):
                self.writeRemaining(',')
            else:
                self.writeRemaining('')
                
        
        self.dtabs()
        self.writeLine('}')
        self.dtabs()
        if addComma == True:
            self.writeLine('},')
        else:
            self.writeLine('}')


    def processROUTEAsXML(self, node, sFieldList):
        fromNode  = sFieldList[1] + "='" + getattr(node, sFieldList[1]) + "'"
        fromField = sFieldList[0] + "='" + getattr(node, sFieldList[0]) + "'"
        toNode    = sFieldList[3] + "='" + getattr(node, sFieldList[3]) + "'"
        toField   = sFieldList[2] + "='" + getattr(node, sFieldList[2]) + "'"

        mainline = "<ROUTE " + fromNode + " " + fromField + " " + toNode + " " + toField + "/>"
        self.writeLine(mainline)

        
    # This is only setup to handle Shader custom fields
    # TODO Change update Function to handle fields for Script, ExternProto, and Proto nodes
    def processFieldAsXML(self, node, sFieldList, mNodeList):
        fieldText = "<field name='" + node.name + "' type='" + node.type + "' accessType='" + node.accessType
        if fieldType == "SFNode":
            fieldText += " containderField='fields'>"
            self.writeLine(fieldText)
            self.itabs()
            self.processNode(node.children[0], False, False, cField="children")
            self.dtabs()
            self.writeLine("</field>")
            
        elif fieldType == "MFNode": # TODO Implement Later for Script, ExternProto, and Proto nodes
            #fieldText += ">"
            #self.writeLine(fieldText)
            #self.itabs()

            #for field in mNodeList:
            #    fList = getattr(node, field)
            #    for fNode in fList:
            #        self.processNode(fNode, True, False, cField=field)
            #self.dtabs()
            #self.writeLine("</field>")
            pass
            
        else:
            fieldText += " value='" + node.value + "' containderField='fields'/>"
            self.writeLine(fieldText)
        

    def processNodeAsXML( self, nType, node, showCF, sFieldList, mFieldList, sNodeList, mNodeList, cField):
        if nType == "ROUTE":
            self.processROUTEAsXML(node, sFieldList)
            return

        if nType == "field":
            self.processFieldAsXML(node, sFieldList, mNodeList)
            return

        cap = "/>"
        mainline = "<" + nType
        for field in sFieldList:
            tField = field

            # This is a fix for lighting nodes that have the 'global_' field.
            if tField == "global_":
                tField = "global"
                
            mainline = mainline + " " + tField + "='"
            
            value = getattr(node, field)
            sValue = ""
            
            if isinstance(value, tuple):
                sValue = " ".join([str(item) for item in value])
                sValue = sValue.strip()
                
            elif isinstance(value, bool):
                if value == True:
                    sValue = "true"
                else:
                    sValue = "false"
                    
            elif isinstance(value, str):
                sValue = value
                
            else:
                sValue = str(value)
            
            mainline = mainline + sValue + "'"
        
        # New Way of doing 'containerField' --- 8/23/2025
        if cField != "":
            mainline = mainline + " containerField='" + cField + "'"
        
        if len(sNodeList) > 0 or len(mNodeList) > 0:
            cap = ">"
        
        if len(mFieldList) == 0:
            mainline += cap
            
        self.writeLine(mainline)
        self.itabs()
        
        mflLen = len(mFieldList)
        for idx in range(mflLen):
            fieldLine = mFieldList[idx] + "='"
            values = getattr(node, mFieldList[idx])
            sValue = ""
            if   isinstance(values[0], tuple):
                tvLen = len(values)
                for vIdx in range(tvLen):
                    tValue = " ".join([str(item) for item in values[vIdx]])
                    tValue = tValue.strip()
                    sValue = sValue + tValue
                    if vIdx < (tvLen - 1):
                        sValue += ", "
                
            elif isinstance(values[0], bool):
                tvLen = len(values)
                for vIdx in range(tvLen):
                    tValue = "true"
                    if values[vIdx] == False:
                        tValue = "false"
                    sValue = sValue + tValue
                    if vIdx < (tvLen - 1):
                        sValue += ", "
                
            elif isinstance(values[0], str):
                tvLen = len(values)
                for vIdx in range(tvLen):
                    tValue = '"' + values[vIdx] + '"'
                    sValue = sValue + tValue
                    if vIdx < (tvLen - 1):
                        sValue += ", "
                
            else:
                tvLen = len(values)
                for vIdx in range(tvLen):
                    tValue = str(values[vIdx])
                    sValue = sValue + tValue
                    if vIdx < (tvLen - 1):
                        sValue += ", "

            fieldLine = fieldLine + sValue + "'"
            if idx == mflLen - 1:
                fieldLine += cap
            self.writeLine(fieldLine)
            
        for field in sNodeList:
            fNode = getattr(node, field)
            self.processNode(fNode, False, False, cField=field)
            
        for field in mNodeList:
            fList = getattr(node, field)
            for fNode in fList:
                self.processNode(fNode, True, False, cField=field)
                
        self.dtabs()
        if len(sNodeList) > 0 or len(mNodeList) > 0:
            self.writeLine("</" + nType + ">")
                

    def processROUTEAsHTML(self, node, sFieldList):
        fromNode  = sFieldList[1] + "='" + getattr(node, sFieldList[1]) + "'"
        fromField = sFieldList[0] + "='" + getattr(node, sFieldList[0]) + "'"
        toNode    = sFieldList[3] + "='" + getattr(node, sFieldList[3]) + "'"
        toField   = sFieldList[2] + "='" + getattr(node, sFieldList[2]) + "'"

        mainline = "<ROUTE " + fromNode + " " + fromField + " " + toNode + " " + toField + "></ROUTE>"
        self.writeLine(mainline)
        
        
    # This is only setup to handle Shader custom fields
    # TODO Change update Function to handle fields for Script, ExternProto, and Proto nodes
    def processFieldAsHTML(self, node, sFieldList, mNodeList):
        fieldText = "<field name='" + node.name + "' type='" + node.type + "' accessType='" + node.accessType
        if fieldType == "SFNode":
            fieldText += " containderField='fields'>"
            self.writeLine(fieldText)
            self.itabs()
            self.processNode(node.children[0], False, False, cField="children")
            self.dtabs()
            self.writeLine("</field>")
            
        elif fieldType == "MFNode": # TODO Implement Later for Script, ExternProto, and Proto nodes
            #fieldText += ">"
            #self.writeLine(fieldText)
            #self.itabs()

            #for field in mNodeList:
            #    fList = getattr(node, field)
            #    for fNode in fList:
            #        self.processNode(fNode, True, False, cField=field)
            #self.dtabs()
            #self.writeLine("</field>")
            pass
            
        else:
            fieldText += " value='" + node.value + "' containderField='fields'></field>"
            self.writeLine(fieldText)


    def processNodeAsHTML( self, nType, node, showCF, sFieldList, mFieldList, sNodeList, mNodeList, cField):
        if nType == "ROUTE":
            self.processROUTEAsHTML(node, sFieldList)
            return

        if nType == "field":
            self.processFieldAsHTML()
            return
            
        cap = ">"
        mainline = "<" + nType
        for field in sFieldList:
            tField = field
            
            # This is a fix for lighting nodes that have the 'global_' field.
            if tField == "global_":
                tField = "global"

            mainline = mainline + " " + tField + "='"
            
            value = getattr(node, field)
            sValue = ""
            
            if isinstance(value, tuple):
                sValue = " ".join([str(item) for item in value])
                sValue = sValue.strip()
                
            elif isinstance(value, bool):
                if value == True:
                    sValue = "true"
                else:
                    sValue = "false"
                    
            elif isinstance(value, str):
                sValue = value
                
            else:
                sValue = str(value)
            
            mainline = mainline + sValue + "'"
        
        # New Way of doing 'containerField' --- 8/23/2025
        if cField != "":
            mainline = mainline + " containerField='" + cField + "'"

        if len(mFieldList) == 0:
            mainline += cap
            
        self.writeLine(mainline)
        self.itabs()
        
        mflLen = len(mFieldList)
        for idx in range(mflLen):
            fieldLine = mFieldList[idx] + "='"
            values = getattr(node, mFieldList[idx])
            sValue = ""
            if   isinstance(values[0], tuple):
                tvLen = len(values)
                for vIdx in range(tvLen):
                    tValue = " ".join([str(item) for item in values[vIdx]])
                    tValue = tValue.strip()
                    sValue = sValue + tValue
                    if vIdx < (tvLen - 1):
                        sValue += ", "
                
            elif isinstance(values[0], bool):
                tvLen = len(values)
                for vIdx in range(tvLen):
                    tValue = "true"
                    if values[vIdx] == False:
                        tValue = "false"
                    sValue = sValue + tValue
                    if vIdx < (tvLen - 1):
                        sValue += ", "
                
            elif isinstance(values[0], str):
                tvLen = len(values)
                for vIdx in range(tvLen):
                    tValue = '"' + values[vIdx] + '"'
                    sValue = sValue + tValue
                    if vIdx < (tvLen - 1):
                        sValue += ", "
                
            else:
                tvLen = len(values)
                for vIdx in range(tvLen):
                    tValue = str(values[vIdx])
                    sValue = sValue + tValue
                    if vIdx < (tvLen - 1):
                        sValue += ", "

            fieldLine = fieldLine + sValue + "'"
            if idx == mflLen - 1:
                fieldLine += cap
            self.writeLine(fieldLine)
            
        for field in sNodeList:
            fNode = getattr(node, field)
            self.processNode(fNode, False, False, cField=field)
            
        for field in mNodeList:
            fList = getattr(node, field)
            for fNode in fList:
                self.processNode(fNode, True, False, cField=field)
                
        self.dtabs()
        self.writeLine("</" + nType + ">")
                

    def writePrefix(self, prefix):
        myline = ''
        
        for t in range(self.tabs):
            myline += '\t'
        myline += prefix
        myline += ' '
        
        self.iofile.write(myline)

    def writeRemaining(self, outline):
        self.iofile.write(outline + "\n")

    def writeLine(self, outline):
        myline = ''
        
        for t in range(self.tabs):
            myline += '\t'
        myline += outline
        myline += '\n'
        
        self.iofile.write(myline)
    
    def writeHeader(self):
        if   self.enc == encx:
            self.writeLine('<?xml version="1.0" encoding="UTF-8"?>')
            self.writeLine('<!DOCTYPE X3D PUBLIC "ISO//Web3D//DTD X3D ' + self.x3dVersion +'//EN" "https://www.web3d.org/specifications/x3d-' + self.x3dVersion +'.dtd">')
            self.writeLine("<X3D profile='" + self.profileType + "' version='" + self.x3dVersion +"' xmlns:xsd='http://www.w3.org/2001/XMLSchema-instance' xsd:noNamespaceSchemaLocation='https://www.web3d.org/specifications/x3d-" + self.x3dVersion + ".xsd'>")
            self.itabs()
            self.writeLine("<head>")
            self.itabs()
            for key, value in self.profDict:
                self.writeLine("<component name='" + key + "' level='" + str(value) + "'/>")
            for meta in self.metatags:
                self.writeLine("<meta name='" + meta["name"] + "' content='" + meta["content"] + "'/>")
            self.dtabs()
            self.writeLine("</head>")
            self.writeLine("<Scene>")
            self.itabs()
                    
        elif self.enc == encv:
            self.writeLine('#X3D ' + self.x3dVersion + ' utf8')
            self.writeLine('PROFILE ' + self.profileType)
            if len(self.profDict) > 0:
                self.writeLine('')
                for key, value in self.profDict:
                    self.writeLine('COMPONENT ' + key + ' : ' + str(value))
            if len(self.metatags) > 0:
                self.writeLine('')
                for meta in self.metatags:
                    self.writeLine('META "' + meta["name"] + '" "' + meta["content"] + '"')
            self.writeLine('')
            
        elif self.enc == encj:
            self.writeLine('{')
            self.itabs()
            self.writeLine('"X3D": {')
            self.itabs()
            self.writeLine('"encoding": "UTF-8",')
            self.writeLine('"@profile": "' + self.profileType + '",')
            self.writeLine('"@version": "' + self.x3dVersion + '",')
            self.writeLine('"@xsd:noNamespaceSchemaLocation": "https://www.web3d.org/specifications/x3d-' + self.x3dVersion + '.xsd",')
            self.writeLine('"JSON schema": "https://www.web3d.org/specifications/x3d-' + self.x3dVersion + '-JSONSchema.json",')
            
            pdLen = len(self.profDict)
            mtLen = len(self.metatags)
            
            if pdLen > 0 or mtLen > 0:
                self.writeLine('"head": {')
                self.itabs()
                if mtLen > 0:
                    self.writeLine('"meta": [')
                    self.itabs()
                    for m in range(mtLen):
                        meta = self.metatags[m]
                        self.writeLine('{')
                        self.itabs()
                        self.writeLine('"@name": "' + meta["name"] + '",')
                        self.writeLine('"@content": "' + meta["content"] + '"')
                        self.dtabs()
                        if m < mtLen - 1:
                            self.writeRemaining('},')
                        else:
                            self.writeRemaining('}')
                            
                    self.dtabs()    
                    if pdLen > 0:
                        self.writeRemaining('],')
                    else:
                        self.writeRemaining(']')
                        
                if pdLen > 0:
                    keys   = list(self.profDict.keys())
                    values = list(self.profDict.values())
                    self.writeLine('"component": [')
                    self.itabs()
                    for p in range(pdLen):
                        self.writeLine('{')
                        self.itabs()
                        self.writeLine('"@name": "' + keys[p] + '",')
                        self.writeLine('"@level": ' + str(values[p]))
                        self.dtabs()
                        if p < pdLen - 1:
                            self.writeRemaining('},')
                        else:
                            self.writeRemaining('}')
                    self.dtabs()
                    self.writeLine(']')
                    
                self.dtabs()
                self.writeLine('},')
            self.writeLine('"Scene": {')
            self.itabs()
            self.writeLine('"-children": [')
            self.itabs()
            
        elif self.enc == ench:
            self.writeLine("<!DOCTYPE html>")
            self.writeLine("<html>")
            self.itabs()
            self.writeLine("<head>")
            self.itabs()
            self.writeLine("<meta charset='utf-8'>")
            self.writeLine("<script type='text/javascript' src='https://www.x3dom.org/download/dev/x3dom-full.js'></script>")
            self.writeLine("<link rel='stylesheet' type='text/css' href='https://www.x3dom.org/download/x3dom.css'></link>")
            self.dtabs()
            self.writeLine("</head>")
            self.writeLine("<body style='background-color:gray;'>")
            self.itabs()
            self.writeLine("<div style='width: 600px; height: 600px;'>")
            self.itabs()
            self.writeLine("<X3D>")
            self.itabs()
            self.writeLine("<head>")
            self.itabs()
            for key, value in self.profDict:
                self.writeLine("<component name='" + key + "' level='" + str(value) + "'></component>")
            for meta in self.metatags:
                self.writeLine("<meta name='" + meta["name"] + "' content='" + meta["content"] + "'></meta>")
            self.dtabs()
            self.writeLine("</head>")
            self.writeLine("<Scene>")
            self.itabs()

    def writeFooter(self):
        if   self.enc == encx:
            self.dtabs()
            self.writeLine("</Scene>")
            self.dtabs()
            self.writeLine("</X3D>")
                    
        elif self.enc == encv:
            self.writeLine('')
            self.writeLine('#End of File')
            
        elif self.enc == encj:
            self.dtabs()
            self.writeLine(']')
            self.dtabs()
            self.writeLine('}')
            self.dtabs()
            self.writeLine('}')
            self.dtabs()
            self.writeLine('}')
            
        elif self.enc == ench:
            self.dtabs()
            self.writeLine("</Scene>")
            self.dtabs()
            self.writeLine("</X3D>")
            self.dtabs()
            self.writeLine("</div>")
            self.dtabs()
            self.writeLine("</body>")
            self.dtabs()
            self.writeLine("</html>")


    def itabs(self):
        self.tabs += 1


    def dtabs(self):
        if self.tabs > 0:
            self.tabs -= 1

            
    ###########################################################################
    # Replaces the RKSceneTraversal.createNodeFromString() function with this 
    # dynamic means of creating new objects.
    #
    # Doing so will allow the use of all X3D objects in the latest version of
    # x3d.py and RKPseudoNode without having to worry if this dictionary
    # gets updated.
    ###########################################################################
    #def instantiateNodeFromString(self, x3dType):
    #    try:
    #        ClassObj = globals()[x3dType]
    #        return ClassObj()
    #    except:
    #        return None
    
    
    
    def getRouteObject(self):
        return ROUTE()
        
    def getFieldObject(self):
        return field()
        
    
    # Component Evaulation
    def adjustProfileAndComponents(self, pcDict):
        
        for key in pcDict:
            pdVal = self.profDict.get(key, 0)
            pcVal = pcDict[key]
            
            if pcVal > pdVal:
                self.profDict[key] = pcVal

                
    def evaluateForCore(self):
        self.profileType = "Core"

        for key in self.profDict:
            self.compDict[key] = self.profDict[key]


    def evaluateForCADInterchange(self):
        cnt = self.countComponents(10, self.interchange)
                
        if cnt == 10:
            self.profileType = "CADInterchange"
        else:
            self.evaluateForCore()


    def evaluateForInterchange(self):
        cnt = self.countComponents(12, self.interchange)
                
        if cnt == 12:
            self.profileType = "Interchange"
        else:
            self.evaluateForCADInterchange()
        
        
    def evaluateForMP4Interactive(self):
        cnt = self.countComponents(14, self.mp4Interactive)
                
        if cnt == 14:
            self.profileType = "MPEG4Interactive"
        else:
            self.evaluateForInterchange()

        
    def evaluateForInteractive(self):
        cnt = self.countComponents(16, self.interactive)
                
        if cnt == 16:
            self.rkio.trv.profileType = "Interactive"
        else:
            self.evaluateForMP4Interactive()
        
        
    def evaluateForImmersive(self):
        cnt = self.countComponents(20, self.immersive)
                
        if cnt == 20:
            self.profileType = "Immersive"
        else:
            self.evaluateForInteractive()
        

    def evaluateForFull(self):
        cnt = self.countComponents(36, self.full)
                
        if cnt == 36:
            self.profileType = "Full"
        else:
            self.evaluateForImmersive()
            
            
    def countComponents(self, limit, profile):
        cnt = 0
        
        for key in profile:
            fVal = profile[key]
            kVal = self.profDict.get(key, 0)
            
            if kVal >= fVal:
                cnt += 1
                if kVal > fVal:
                    self.compDict[key] = kVal
            else:
                self.compDict.clear()
                break

        return cnt


    def setAdditionalComponents(self):
        cProf = self.profiles[self.profileType]
        keepDict = {}
        for key, value in self.profDict:
            cValue = cProf.get(key, 0)
            if cValue != value:
                keepDict[key] = cValue
                
        self.profDict = keepDict
