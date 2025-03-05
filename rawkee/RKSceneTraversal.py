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
                self.processNode(node, tMulti, True)
            else:
                self.processNode(node, tMulti, False)
        self.writeFooter()

    def processNode(self, node, isMulti, addComma):
        nType   = type(node).__name__

        sFieldsList = []
        mFieldsList  = []
        
        sNodeList  = []
        mNodeList   = []
        
        pastMeta = False
        
        print(nType)
        print(node)
        nDict = vars(node)
        for key, value in nDict.items():
            keyp = key.split('_')
            if   keyp[1] == "X3DNode":
                if   keyp[3] == "DEF" and value != None:
                    sFieldsList.append("DEF")
                    
                elif keyp[3] == "USE" and value != None:
                    sFieldsList.append("USE")
                    
                elif keyp[3] == "metadata":
                    pastMeta = True
                    if value != None:
                        sNodeList.append("metadata")
                    
            elif keyp[1] == "RK":
                if   keyp[3] == "containerField" and value != "":
                    sFieldsList.append("_RK__containerField")
                    
                elif keyp[3] == "mapping" and value != "":
                    sFieldsList.append("_RK__mapping")
                
            elif keyp[1] == nType:
                if pastMeta == False:
                    continue
                    
                if  isinstance(value, list):
                    if len(value) > 0:
                        if isinstance(value[0], (str, float, int, tuple, bool, type(None) ) ):
                            if value[0] != None:
                                mFieldsList.append(keyp[3])
                        else:
                            mNodeList.append(keyp[3])

                else:
                    if isinstance(value, (str, float, int, tuple, bool, type(None) ) ):
                        if value != None:
                            sFieldsList.append(keyp[3])
                    else:
                        sNodeList.append(keyp[3])

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
                    
        self.processSortedNode(nType, node, sFieldsList, mFieldsList, sNodeList, mNodeList, isMulti, addComma)


        
    def processSortedNode(self, nType, node, sFieldList, mFieldList, sNodeList, mNodeList, isMulti, addComma):
        
        if sFieldList[0] == "USE":
            processUsed(nType, node, isMulti, addComma)
        else:
            if   self.enc == encx:
                self.processNodeAsXML( nType, node, True,  sFieldList, mFieldList, sNodeList, mNodeList)
            elif self.enc == encv:
                self.processNodeAsVRML(nType, node, False, sFieldList, mFieldList, sNodeList, mNodeList, isMulti)
            elif self.enc == encj:
                self.processNodeAsJSON(nType, node, False, sFieldList, mFieldList, sNodeList, mNodeList, isMulti, addComma)
            elif self.enc == ench:
                self.processNodeAsXML( nType, node, True,  sFieldList, mFieldList, sNodeList, mNodeList)


    
    def processUsed(self, nType, node, isMulti, addComma):
        mainline = ""
        if   self.enc == encx:
            mainline = "<" + nType + " USE='" + node.USE + "'"
            cf = getattr(node, "_RK__containerField")
            if cf != None:
                mainline += "containerField='" + cf + "'"
            mainline += "/>"
            
        elif self.enc == encv:
            mainline = "USE " + node.USE
            if isMulti == False:
                self.writeRemaining(mainline)
                return
            
        elif self.enc == encj:
            #{ "NodeType":
            #    {
            #      "@USE": "NodeName"
            #    }
            #}
            mainline = '{"' + nType + '":{"@USE":"' + node.USE + '"}}'
            if addComma == True:
                mainline += ","
            if isMulti == False:
                self.writeRemaining(mainline)
                return
            
        elif self.enc == ench:
            mainline = "<" + nType + " USE='" + node.USE + "'"
            cf = getattr(node, "_RK__containerField")
            if cf != None:
                mainline += "containerField='" + cf + "'"
            mainline += "/>"
            
        self.writeLine(mainline)



    def processNodeAsVRML(self, nType, node, showCF, sFieldList, mFieldList, sNodeList, mNodeList, isMulti):
        mainline = ""
        
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
            if   tField == "_RK__mapping":
                tField  =  "mapping"
            elif tField == "_RK__containerField":
                tField  =  "containerField"
                ####################################################
                # 'containerField' does not get used in VRML export,
                # so skip this iteration of the loop.
                ####################################################
                if showCF == False:
                    continue
                
            elif tField == "DEF":
                # Don't write out DEF as a node field
                continue
                
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



    def processNodeAsJSON(self, nType, node, showCF, sFieldList, mFieldList, sNodeList, mNodeList, isMulti, addComma):
        mainline = ''
        if isMulti == True:
            self.writeLine(     '{ "' + nType + '":')
        else:
            self.writeRemaining('{ "' + nType + '":')
        self.itabs()
        self.writeLine('{')
        self.itabs()
        
        sflLen = len(sFieldList)
        mflLen = len(mFieldList)
        snlLen = len(sNodeList)
        mnlLen = len(mNodeList)
        for fIdx in range(sflLen):
            tField = sFieldList[fIdx]
            if   tField == "_RK__mapping":
                tField  =  "mapping"
            elif tField == "_RK__containerField":
                tField  =  "containerField"
                ####################################################
                # 'containerField' does not get used in JSON export,
                # so skip this iteration of the loop.
                ####################################################
                if showCF == False:
                    continue
                
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
            self.writeLine(']')
        
        self.dtabs()
        self.writeLine('}')
        self.dtabs()
        #self.writePrefix('}')
        if addComma == True:
            self.writeLine('},')
        else:
            self.writeLine('}')



    def processNodeAsXML( self, nType, node, showCF, sFieldList, mFieldList, sNodeList, mNodeList):
        cap = "/>"
        mainline = "<" + nType
        for field in sFieldList:
            tField = field
            if   field == "_RK__mapping":
                tField =  "mapping"
            elif field == "_RK__containerField":
                tField =  "containerField"
                
                # It may not be adventageous to always add the containerField
                if showCF == False:
                    continue
                
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
            self.processNode(fNode, False, False)
            
        for field in mNodeList:
            fList = getattr(node, field)
            for fNode in fList:
                self.processNode(fNode, True, False)
                
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
            self.writeLine('')
            self.writeLine('PROFILE Full')
            self.writeLine('')
            self.writeLine('META "generator" "RawKee X3D Exporter for Maya 2025+ [Python Edition], https://github.com/und-dream-lab/rawkee/"')
            self.writeLine('')
            
        elif self.enc == encj:
            self.writeLine('{')
            self.itabs()
            self.writeLine('"X3D": {')
            self.itabs()
            self.writeLine('"encoding":"UTF-8",')
            self.writeLine('"@profile": "Full",')
            self.writeLine('"@version": "4.0",')
            self.writeLine('"@xsd:noNamespaceSchemaLocation": "https://www.web3d.org/specifications/x3d-4.0.xsd",')
            self.writeLine('"JSON schema": "https://www.web3d.org/specifications/x3d-4.0-JSONSchema.json",')
            self.writeLine('"head": {')
            self.itabs()
            self.writeLine('"meta": [')
            self.itabs()
            self.writeLine('{')
            self.itabs()
            self.writeLine('"@name": "generator",')
            self.writeLine('"@content": "RawKee X3D Exporter for Maya 2025+ [Python Edition], https://github.com/und-dream-lab/rawkee/"')
            self.dtabs()
            self.writeLine('}')
            self.dtabs()
            self.writeLine(']')
            self.dtabs()
            self.writeLine('},')
            self.writeLine('"Scene": {')
            self.itabs()
            self.writeLine('"-children": [')
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
            self.writeLine("</body>")
            self.dtabs()
            self.writeLine("</html>")

    def itabs(self):
        self.tabs += 1
        
    def dtabs(self):
        if self.tabs > 0:
            self.tabs -= 1