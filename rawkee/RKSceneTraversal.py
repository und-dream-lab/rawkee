import sys
import os
import rawkee.x3d
from rawkee.x3d import *
from rawkee.RKPseudoNode import *
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
            
        compNode = self.createNodeFromString(nType)
        pastMeta = False
        nDict = vars(node)
        chkVal = self.isNonX3D(nType)
        
        if chkVal == True:
            for key, value in nDict.items():
                if key == "DEF" and value != '':
                    sFieldsList.append("DEF")
                elif key == "USE" and value != '':
                    sFieldsList.append("USE")
                elif isinstance(value, list):
                    if getattr(compNode,key) != value:#len(value) > 0:
                        if isinstance(value[0], (str, float, int, tuple, bool, type(None) ) ):
                            if value[0] != None:
                                mFieldsList.append(key)
                        else:
                            mNodeList.append(key)
                elif getattr(compNode,key) != value:
                    if isinstance(value, (str, float, int, tuple, bool, type(None) ) ):
                        #if value != None:
                        sFieldsList.append(key)
                    else:
                        #if getattr(compNode,keyp[3]) != value:
                        sNodeList.append(key)
                        
        else:
            for key, value in nDict.items():
                keyp = key.split('_')
                if   keyp[1] == "X3DNode":
                    if   keyp[3] == "DEF" and node.DEF != None:
                        sFieldsList.append("DEF")
                        
                    elif keyp[3] == "USE" and node.USE != None:
                        sFieldsList.append("USE")
                        
                    elif keyp[3] == "metadata":
                        pastMeta = True
                        if compNode.metadata != node.metadata: #value != None:
                            sNodeList.append("metadata")
                        
                elif keyp[1] == "RK":
                    if   keyp[3] == "containerField" and value != "":
                        sFieldsList.append("_RK__containerField")
                        
                elif keyp[1] == nType:
                    if pastMeta == False:
                        continue
                    
                    # For some reason the '_Normal__vector' attribute doesn't show up as an instance of a list, eventhough it should.
                    # So I added a one-off check for the vector attribute.
                    if  isinstance(value, list) or (keyp[1] == "Normal" and keyp[3] == "vector"):
                        if getattr(compNode,keyp[3]) != value:#len(value) > 0:
                            if isinstance(value[0], (str, float, int, tuple, bool, type(None) ) ):
                                if value[0] != None:
                                    mFieldsList.append(keyp[3])
                                    print('M Field: ' + keyp[3])
                            else:
                                mNodeList.append(keyp[3])

                    else:
                        if getattr(compNode,keyp[3]) != value:
                            if isinstance(value, (str, float, int, tuple, bool, type(None) ) ):
                                #if value != None:
                                sFieldsList.append(keyp[3])
                                print('S Field: ' + keyp[3])
                            else:
                                #if getattr(compNode,keyp[3]) != value:
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
                    
                    hasDEF = False
                    if compNode.skelelton != node.skeleton:
                        for rj in getattr(node, "skeleton"):
                            if type(rj).__name__ == "HAnimJoint" and (rj.DEF != '' or rj.DEF != None):
                                hasDEF = True

                    if sIdx > -1 and jIdx > -1 and sIdx > jIdx and hasDEF == True:
                        mNodeList[jIdx] = "skeleton"
                        mNodeList[sIdx] = "joints"
            
        compNode = None
                    
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
                self.processNodeAsHTML( nType, node, True,  sFieldList, mFieldList, sNodeList, mNodeList)


    
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
#            if   tField == "_RK__mapping":
#                tField  =  "mapping"
#            elif tField == "_RK__containerField":
            if tField == "_RK__containerField":
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
        
        sflLen = len(sFieldList) # sflLen
        mflLen = len(mFieldList) # mflLen
        snlLen = len(sNodeList)  # snlLen
        mnlLen = len(mNodeList)  # mnlLen
        for fIdx in range(sflLen):
            
            
            tField = sFieldList[fIdx]

            if tField == "_RK__containerField":
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
            
            # Since _RK__containerField/containerField is not used inside the node brackets, we use the fIdx < (sflLen - n) where 'n' needs to be a 2 instead of a 1 since
            # we are not printing out containerField here. In VRML export, this check is not needed because the field values do not have a terminator, and the X3D and HTML
            # 'n' is set to 1 as the exports have the containerField withing the XML tag.
            if fIdx < (sflLen - 2) or mflLen > 0 or snlLen > 0 or mnlLen > 0:
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
#            if   field == "_RK__mapping":
#                tField =  "mapping"
#            elif field == "_RK__containerField":
            if field == "_RK__containerField":
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
                


    def processNodeAsHTML( self, nType, node, showCF, sFieldList, mFieldList, sNodeList, mNodeList):
        cap = ">"
        mainline = "<" + nType
        for field in sFieldList:
            tField = field
#            if   field == "_RK__mapping":
#                tField =  "mapping"
#            elif field == "_RK__containerField":
            if field == "_RK__containerField":
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
            self.writeLine("<link rel='stylesheet' href='x3dom-1.8.3/x3dom.css'></link>")
            self.dtabs()
            self.writeLine("</head>")
            self.writeLine("<body>")
            self.itabs()
            self.writeLine("<div style='width: 600px; height: 600px;'>")
            self.itabs()
#            self.writeLine("<?xml version='1.0' encoding='UTF-8'?>")
#            self.writeLine("<!DOCTYPE X3D PUBLIC 'ISO//Web3D//DTD X3D 4.0//EN' 'https://www.web3d.org/specifications/x3d-4.0.dtd'>")
#            self.writeLine("<X3D profile='Full' version='4.0' xmlns:xsd='http://www.w3.org/2001/XMLSchema-instance' xsd:noNamespaceSchemaLocation='https://www.web3d.org/specifications/x3d-4.0.xsd'>")
            self.writeLine("<X3D>")
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
            
    def createNodeFromString(self, x3dType):
        x3dNodeMapping = {
            ####################################### A
            'AcousticProperties':AcousticProperties,
            'Analyser':Analyser,
            'Anchor':Anchor,
            'Appearance':Appearance,
            'Arc2D':Arc2D,
            'ArcClose2D':ArcClose2D,
            'AudioClip':AudioClip,
            'AudioDestination':AudioDestination,
            ####################################### B
            'Background':Background,
            'BallJoint':BallJoint,
            'Billboard':Billboard,
            'BiquadFilter':BiquadFilter,
            'BlendedVolumeStyle':BlendedVolumeStyle,
            'BooleanFilter':BooleanFilter,
            'BooleanSequencer':BooleanSequencer,
            'BooleanToggle':BooleanToggle,
            'BooleanTrigger':BooleanTrigger,
            'BoundaryEnhancementVolumeStyle':BoundaryEnhancementVolumeStyle,
            'BoundedPhysicsModel':BoundedPhysicsModel,
            'Box':Box,
            'BufferAudioSource':BufferAudioSource,
            ####################################### C
            'CADAssembly':CADAssembly,
            'CADFace':CADFace,
            'CADLayer':CADLayer,
            'CADPart':CADPart,
            'CartoonVolumeStyle':CartoonVolumeStyle,
            'ChannelMerger':ChannelMerger,
            'ChannelSelector':ChannelSelector,
            'ChannelSplitter':ChannelSplitter,
            'Circle2D':Circle2D,
            'ClipPlane':ClipPlane,
            'CollidableOffset':CollidableOffset,
            'CollidableShape':CollidableShape,
            'Collision':Collision,
            'CollisionCollection':CollisionCollection,
            'CollisionSensor':CollisionSensor,
            'CollisionSpace':CollisionSpace,
            'Color':Color,
            'ColorChaser':ColorChaser,
            'ColorDamper':ColorDamper,
            'ColorInterpolator':ColorInterpolator,
            'ColorRGBA':ColorRGBA,
            'CommonSurfaceShader':CommonSurfaceShader,#             From rawkee.RKPseudoNode, not x3d.py
            'ComposedCubeMapTexture':ComposedCubeMapTexture,
            'ComposedShader':ComposedShader,
            'ComposedTexture3D':ComposedTexture3D,
            'ComposedVolumeStyle':ComposedVolumeStyle,
            'Cone':Cone,
            'ConeEmitter':ConeEmitter,
            'Contact':Contact,
            'Contour2D':Contour2D,
            'ContourPolyline2D':ContourPolyline2D,
            'Convolver':Convolver,
            'Coordinate':Coordinate,
            'CoordinateChaser':CoordinateChaser,
            'CoordinateDamper':CoordinateDamper,
            'CoordinateDouble':CoordinateDouble,
            'CoordinateInterpolator':CoordinateInterpolator,
            'CoordinateInterpolator2D':CoordinateInterpolator2D,
            'Cylinder':Cylinder,
            'CylinderSensor':CylinderSensor,
            ####################################### D
            'Delay':Delay,
            'DirectionalLight':DirectionalLight,
            'DISEntityManager':DISEntityManager,
            'DISEntityTypeMapping':DISEntityTypeMapping,
            'Disk2D':Disk2D,
            'DoubleAxisHingeJoint':DoubleAxisHingeJoint,
            'DynamicsCompressor':DynamicsCompressor,
            ####################################### E
            'EaseInEaseOut':EaseInEaseOut,
            'EdgeEnhancementVolumeStyle':EdgeEnhancementVolumeStyle,
            'ElevationGrid':ElevationGrid,
            'EspduTransform':EspduTransform,
            'ExplosionEmitter':ExplosionEmitter,
            'Extrusion':Extrusion,
            ####################################### F
            'FillProperties':FillProperties,
            'FloatVertexAttribute':FloatVertexAttribute,
            'Fog':Fog,
            'FogCoordinate':FogCoordinate,
            'FontStyle':FontStyle,
            'ForcePhysicsModel':ForcePhysicsModel,
            ####################################### G
            'Gain':Gain,
            'GeneratedCubeMapTexture':GeneratedCubeMapTexture,
            'GeoCoordinate':GeoCoordinate,
            'GeoElevationGrid':GeoElevationGrid,
            'GeoLocation':GeoLocation,
            'GeoLOD':GeoLOD,
            'GeoMetadata':GeoMetadata,
            'GeoOrigin':GeoOrigin,
            'GeoPositionInterpolator':GeoPositionInterpolator,
            'GeoProximitySensor':GeoProximitySensor,
            'GeoTouchSensor':GeoTouchSensor,
            'GeoTransform':GeoTransform,
            'GeoViewpoint':GeoViewpoint,
            'Group':Group,
            ####################################### H
            'HAnimDisplacer':HAnimDisplacer,
            'HAnimHumanoid':HAnimHumanoid,
            'HAnimJoint':HAnimJoint,
            'HAnimMotion':HAnimMotion,
            'HAnimSegment':HAnimSegment,
            'HAnimSite':HAnimSite,
            ####################################### I
            'ImageCubeMapTexture':ImageCubeMapTexture,
            'ImageTexture':ImageTexture,
            'ImageTexture3D':ImageTexture3D,
            'IndexedFaceSet':IndexedFaceSet,
            'IndexedLineSet':IndexedLineSet,
            'IndexedQuadSet':IndexedQuadSet,
            'IndexedTriangleFanSet':IndexedTriangleFanSet,
            'IndexedTriangleSet':IndexedTriangleSet,
            'IndexedTriangleStripSet':IndexedTriangleStripSet,
            'Inline':Inline,
            'IntegerSequencer':IntegerSequencer,
            'IntegerTrigger':IntegerTrigger,
            'IsoSurfaceVolumeData':IsoSurfaceVolumeData,
            ####################################### K
            'KeySensor':KeySensor,
            ####################################### L
            'Layer':Layer,
            'LayerSet':LayerSet,
            'Layout':Layout,
            'LayoutGroup':LayoutGroup,
            'LayoutLayer':LayoutLayer,
            'LinePickSensor':LinePickSensor,
            'LineProperties':LineProperties,
            'LineSet':LineSet,
            'ListenerPointSource':ListenerPointSource,
            'LoadSensor':LoadSensor,
            'LocalFog':LocalFog,
            'LOD':LOD,
            ####################################### M
            'Material':Material,
            'Matrix3VertexAttribute':Matrix3VertexAttribute,
            'Matrix4VertexAttribute':Matrix4VertexAttribute,
            'MetadataBoolean':MetadataBoolean,
            'MetadataDouble':MetadataDouble,
            'MetadataFloat':MetadataFloat,
            'MetadataInteger':MetadataInteger,
            'MetadataSet':MetadataSet,
            'MetadataString':MetadataString,
            'MicrophoneSource':MicrophoneSource,
            'MotorJoint':MotorJoint,
            'MovieTexture':MovieTexture,
            'MultiTexture':MultiTexture,
            'MultiTextureCoordinate':MultiTextureCoordinate,
            'MultiTextureTransform':MultiTextureTransform,
            ####################################### N
            'NavigationInfo':NavigationInfo,
            'Normal':Normal,
            'NormalInterpolator':NormalInterpolator,
            'NurbsCurve':NurbsCurve,
            'NurbsCurve2D':NurbsCurve2D,
            'NurbsOrientationInterpolator':NurbsOrientationInterpolator,
            'NurbsPatchSurface':NurbsPatchSurface,
            'NurbsPositionInterpolator':NurbsPositionInterpolator,
            'NurbsSet':NurbsSet,
            'NurbsSurfaceInterpolator':NurbsSurfaceInterpolator,
            'NurbsSweptSurface':NurbsSweptSurface,
            'NurbsSwungSurface':NurbsSwungSurface,
            'NurbsTextureCoordinate':NurbsTextureCoordinate,
            'NurbsTrimmedSurface':NurbsTrimmedSurface,
            ####################################### O
            'OpacityMapVolumeStyle':OpacityMapVolumeStyle,
            'OrientationChaser':OrientationChaser,
            'OrientationDamper':OrientationDamper,
            'OrientationInterpolator':OrientationInterpolator,
            'OrthoViewpoint':OrthoViewpoint,
            'OscillatorSource':OscillatorSource,
            ####################################### P
            'PackagedShader':PackagedShader,
            'ParticleSystem':ParticleSystem,
            'PeriodicWave':PeriodicWave,
            'PhysicalMaterial':PhysicalMaterial,
            'PickableGroup':PickableGroup,
            'PixelTexture':PixelTexture,
            'PixelTexture3D':PixelTexture3D,
            'PlaneSensor':PlaneSensor,
            'PointEmitter':PointEmitter,
            'PointLight':PointLight,
            'PointPickSensor':PointPickSensor,
            'PointProperties':PointProperties,
            'PointSet':PointSet,
            'Polyline2D':Polyline2D,
            'PolylineEmitter':PolylineEmitter,
            'Polypoint2D':Polypoint2D,
            'PositionChaser':PositionChaser,
            'PositionChaser2D':PositionChaser2D,
            'PositionDamper':PositionDamper,
            'PositionDamper2D':PositionDamper2D,
            'PositionInterpolator':PositionInterpolator,
            'PositionInterpolator2D':PositionInterpolator2D,
            'PrimitivePickSensor':PrimitivePickSensor,
            'ProgramShader':ProgramShader,
            'ProjectionVolumeStyle':ProjectionVolumeStyle,
            'ProximitySensor':ProximitySensor,
            ####################################### Q
            'QuadSet':QuadSet,
            ####################################### R
            'ReceiverPdu':ReceiverPdu,
            'Rectangle2D':Rectangle2D,
            'RigidBody':RigidBody,
            'RigidBodyCollection':RigidBodyCollection,
            ####################################### S
            'ScalarChaser':ScalarChaser,
            'ScalarDamper':ScalarDamper,
            'ScalarInterpolator':ScalarInterpolator,
            'ScreenFontStyle':ScreenFontStyle,
            'ScreenGroup':ScreenGroup,
            'Script':Script,
            'SegmentedVolumeData':SegmentedVolumeData,
            'ShadedVolumeStyle':ShadedVolumeStyle,
            'ShaderPart':ShaderPart,
            'ShaderProgram':ShaderProgram,
            'Shape':Shape,
            'SignalPdu':SignalPdu,
            'SilhouetteEnhancementVolumeStyle':SilhouetteEnhancementVolumeStyle,
            'SingleAxisHingeJoint':SingleAxisHingeJoint,
            'SliderJoint':SliderJoint,
            'Sound':Sound,
            'SpatialSound':SpatialSound,
            'Sphere':Sphere,
            'SphereSensor':SphereSensor,
            'SplinePositionInterpolator':SplinePositionInterpolator,
            'SplinePositionInterpolator2D':SplinePositionInterpolator2D,
            'SplineScalarInterpolator':SplineScalarInterpolator,
            'SpotLight':SpotLight,
            'StaticGroup':StaticGroup,
            'StreamAudioDestination':StreamAudioDestination,
            'StreamAudioSource':StreamAudioSource,
            'StringSensor':StringSensor,
            'SurfaceEmitter':SurfaceEmitter,
            'Switch':Switch,
            ####################################### T
            'TexCoordChaser2D':TexCoordChaser2D,
            'TexCoordDamper2D':TexCoordDamper2D,
            'Text':Text,
            'TextureBackground':TextureBackground,
            'TextureCoordinate':TextureCoordinate,
            'TextureCoordinate3D':TextureCoordinate3D,
            'TextureCoordinate4D':TextureCoordinate4D,
            'TextureCoordinateGenerator':TextureCoordinateGenerator,
            'TextureProjector':TextureProjector,
            'TextureProjectorParallel':TextureProjectorParallel,
            'TextureProperties':TextureProperties,
            'TextureTransform':TextureTransform,
            'TextureTransform3D':TextureTransform3D,
            'TextureTransformMatrix3D':TextureTransformMatrix3D,
            'TimeSensor':TimeSensor,
            'TimeTrigger':TimeTrigger,
            'ToneMappedVolumeStyle':ToneMappedVolumeStyle,
            'TouchSensor':TouchSensor,
            'Transform':Transform,
            'TransformSensor':TransformSensor,
            'TransmitterPdu':TransmitterPdu,
            'TriangleFanSet':TriangleFanSet,
            'TriangleSet':TriangleSet,
            'TriangleSet2D':TriangleSet2D,
            'TriangleStripSet':TriangleStripSet,
            'TwoSidedMaterial':TwoSidedMaterial,
            ####################################### U
            'UniversalJoint':UniversalJoint,
            'UnlitMaterial':UnlitMaterial,
            ####################################### V
            'Viewpoint':Viewpoint,
            'ViewpointGroup':ViewpointGroup,
            'Viewport':Viewport,
            'VisibilitySensor':VisibilitySensor,
            'VolumeData':VolumeData,
            'VolumeEmitter':VolumeEmitter,
            'VolumePickSensor':VolumePickSensor,
            ####################################### W
            'WaveShaper':WaveShaper,
            'WindPhysicsModel':WindPhysicsModel,
            'WorldInfo':WorldInfo
        }
        
        return x3dNodeMapping[x3dType]()

    def isNonX3D(self, x3dType):
        if x3dType == "CommonSurfaceShader": #             From rawkee.RKPseudoNode, not x3d.py
#            print("Inside isNonX3D (NOT X3D):" + x3dType)
            return True
#        else:
#            print("Inside isNonX3D (IS X3D):" + x3dType)
        
        return False
