import sys
import os
import x3d
from x3d import *
from typing import Final


encx: Final[int] = 0
encv: Final[int] = 1
encj: Final[int] = 2
ench: Final[int] = 3


class RKSceneTraversal():
    def __init__(self):
        print("RKSceneTraversal")
        
        self.tabs = 0
        self.iofile = None
        self.enc = encx
        
    def startExport(self, x3dDoc, iofile, encoding):
        self.iofile = iofile
        if   encoding == "x3d":
            self.enc = encx
        elif encoding == "x3dv":
            self.enc = encv
        elif encoding == "x3dj":
            self.enc = encj
        elif encoding == "html":
            self.enc = ench
            
        self.writeHeader()
        for node in x3dDoc.Scene.children:
            self.processNode(node, False)
        self.writeFooter()

    def processNode(self, node, isMulti):
        nType   = type(node).__name__

        sFieldsList = []
        mFieldsList  = []
        
        sNodeList  = []
        mNodeList   = []
        
        nDict = vars(node)
        for key, value in nDict.items():
            keyp = key.split('_')
            if   keyp[1] == "X3DNode":
                if   keyp[3] == "DEF" and value != "":
                    sFieldsList.append("DEF")
                    
                elif keyp[3] == "USE" and value != "":
                    sFieldsList.append("USE")
                    
                elif keyp[3] == "metadata" and value != None:
                    sNodeList.append("metadata")
                    
            elif keyp[1] == "RK":
                if   keyp[3] == "containerField" and value != "":
                    sFieldsList.append("_RK__containerField")
                    
                elif keyp[3] == "mapping" and value != "":
                    sFieldsList.append("_RK__mapping")
                
            elif keyp[1] == nType:
                if  isinstance(value, list):
                    if len(value) > 0:
                        if isinstance(value[0], x3d.Node):
                            mNodeList.append(keyp[3])
                        else:
                            mFieldsList.append(keyp[3])
                            
                else:
                    if isinstance(value, x3d.Node):
                        sNodeList.append(keyp[3])
                    else:
                        sFieldsList.append(keyp[3])

        ########################################################
        # Fix for x3d.py misordering of "joints" and "skeleton" 
        # fields in its HAnimHumanoid node implementation.
        ########################################################
        if nType == "HAnimHumanoid":
            jIdx = -1
            sIdx = -1
            
            for idx in range(len(mNodeList)):
                if   mNodeList[idx] == "joints":
                    jIdx = idx
                elif mNodeList[idx] == "skeleton":
                    sIdx = idx
                
                if sIdx != -1 and jIdx != -1:
                    mNodeList[jIdx] = "skeleton"
                    mNodeList[sIdx] = "joints"
                    
        self.processSortedNode(nType, node, sFieldsList, mFieldsList, sNodeList, mNodeList, isMulti)


        
    def processSortedNode(self, nType, node, sFieldList, mFieldList, sNodeList, mNodeList, isMulti):
        
        if sFieldList[0] == "USE":
            processUsed(nType, node)
        else:
            if   self.enc == encx:
                self.processNodeAsXML(nType, node, sFieldList, mFieldList, sNodeList, mNodeList)
            elif self.enc == encv:
                self.processNodeAsVRML(nType, node, sFieldList, mFieldList, sNodeList, mNodeList, isMulti)
            elif self.enc == encj:
                self.processNodeAsJSON(nType, node, sFieldList, mFieldList, sNodeList, mNodeList, isMulti)
            elif self.enc == ench:
                self.processNodeAsXML(nType, node, sFieldList, mFieldList, sNodeList, mNodeList)


    
    def processUsed(self, nType, node):
        mainline = ""
        if   self.enc == encx:
            mainline = "<" + nType + " USE='" + node.USE + "'"
            cf = getattr(node, "_RK__containerField")
            if cf != None:
                mainline += "containerField='" + cf + "'"
            mainline += "/>"
            
        elif self.enc == encv:
            mainline = "USE " + node.USE
            
        elif self.enc == encj:
            #{ "NodeType":
            #    {
            #      "@USE": "NodeName"
            #    }
            #}
            mainline = '{"' + nType + '":{"@USE":"' + node.USE + '"}}'
            
        elif self.enc == ench:
            mainline = "<" + nType + " USE='" + node.USE + "'"
            cf = getattr(node, "_RK__containerField")
            if cf != None:
                mainline += "containerField='" + cf + "'"
            mainline += "/>"
            
        self.writeLine(mainline)



    def processNodeAsVRML(self, nType, node, sFieldList, mFieldList, sNodeList, mNodeList, isMulti):
        mainline = ""
        
        if isMulti == True:
            self.writeLine(     "DEF " + node.DEF + " " + nType + " {")
        else:
            self.writeRemaining("DEF " + node.DEF + " " + nType + " {")
        self.itabs()
        
        # TODO: sFieldList
        
        # TODO: mFieldList
        
        # TODO: sNodeList
        
        # TODO: mNodeList
        
        self.dtabs()
        self.writeLine("}")



    def processNodeAsJSON(self, nType, node, sFieldList, mFieldList, sNodeList, mNodeList, isMulti):
        pass



    def processNodeAsXML( self, nType, node, sFieldList, mFieldList, sNodeList, mNodeList):
        cap = "/>"
        mainline = "<" + nType
        for field in sFieldList:
            tField = field
            if   field == "_RK__mapping":
                tField =  "mapping"
            elif field == "_RK__containerField":
                tField =  "containerField"
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
            self.processNode(fNode, False)
            
        for field in mNodeList:
            fList = getattr(node, field)
            for fNode in fList:
                self.processNode(fNode, True)
                
        self.dtabs()
        if len(sNodeList) > 0 or len(mNodeList) > 0:
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
            self.writeLine("<?xml version='1.0' encoding='UTF-8'?>")
            self.writeLine("<!DOCTYPE X3D PUBLIC 'ISO//Web3D//DTD X3D 4.0//EN' 'https://www.web3d.org/specifications/x3d-4.0.dtd'>")
            self.writeLine("<X3D profile='Full' version='4.0' xmlns:xsd='http://www.w3.org/2001/XMLSchema-instance' xsd:noNamespaceSchemaLocation='https://www.web3d.org/specifications/x3d-4.0.xsd'>")
            self.itabs()
            self.writeLine("<Scene>")
            self.itabs()
                    
        elif self.enc == encv:
            self.writeLine('#VRML V4.0 utf8')
            self.writeLine('#X3D-to-ClassicVRML serialization autogenerated by X3DPSAIL x3d.py')
            self.writeLine('#Exported from RawKee X3D Exporter for Maya - Python Edition')
            self.writeLine('PROFILE Full')
            
        elif self.enc == encj:
            self.writeLine('{')
            self.itabs()
            self.writeLine('"X3D":,')
            self.writeLine('{')
            self.itabs()
            self.writeLine('"encoding":"UTF-8",')
            self.writeLine('"$id":"https://www.web3d.org/specifications/x3d-4.0-JSONSchema.json",')
            self.writeLine('"$schema":"https://json-schema.org/draft/2020-12/schema",')
            self.writeLine('"@version":"4.0",')
            self.writeLine('"@profile":"Full",')
            self.writeLine('"Scene":')
            self.writeLine('{')
            self.itabs()
            
        elif self.enc == ench:
            self.writeLine("<html>")
            self.itabs()
            self.writeLine("<head>")
            self.itabs()
            self.writeLine("<meta charset='utf-8'>")
            self.writeLine("<script src='x3dom-1.8.3/x3dom-full.js'></script>")
            self.writeLine("<link rel='stylesheet' href='x3dom-1.8.3/x3dom.css'>")
            self.dtabs()
            self.writeLine("</head>")
            self.writeLine("<body>")
            self.itabs()
            self.writeLine("<div style='width: 600px; height: 600px;'>")
            self.itabs()
            self.writeLine("<?xml version='1.0' encoding='UTF-8'?>")
            self.writeLine("<!DOCTYPE X3D PUBLIC 'ISO//Web3D//DTD X3D 4.0//EN' 'https://www.web3d.org/specifications/x3d-4.0.dtd'>")
            self.writeLine("<X3D profile='Full' version='4.0' xmlns:xsd='http://www.w3.org/2001/XMLSchema-instance' xsd:noNamespaceSchemaLocation='https://www.web3d.org/specifications/x3d-4.0.xsd'>")
            self.itabs()
            self.writeLine("<Scene>")
            self.itabs()

    def writeFooter(self):
        if   self.enc == encx:
            self.dtabs()
            self.writeLine("</Scene>")
            self.dtabs()
            self.writeLine("</X3D>")
                    
        elif self.enc == encv:
            self.writeLine('#End of File')
            
        elif self.enc == encj:
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
            self.writeLine("</body>")
            self.dtabs()
            self.writeLine("</html>")

                

    def itabs(self):
        self.tabs += 1
        
    def dtabs(self):
        if self.tabs > 0:
            self.tabs -= 1