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

// File: sax3dWriter.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

/*
MString			sax3dWriter::documentUrl;
MString			sax3dWriter::versionEncoding;
MString			sax3dWriter::writeEncoding;
MString			sax3dWriter::x3dProfile;
MStringArray	sax3dWriter::x3dComponents;
MStringArray	sax3dWriter::x3dComments;
MString			sax3dWriter::nodeType;
MString			sax3dWriter::nodeName;
MStringArray	sax3dWriter::nodeFields;
MStringArray	sax3dWriter::nodeValues;
MString			sax3dWriter::fieldName;
MString			sax3dWriter::fieldValue1;
MString			sax3dWriter::fieldValue2;
MString			sax3dWriter::cField;
MString			sax3dWriter::cValue;
MStringArray	sax3dWriter::cData;
*/

unsigned int	sax3dWriter::tabNumber;
int				sax3dWriter::exEncoding;
bool			sax3dWriter::hasMultiple = false;
bool			sax3dWriter::firstNotWritten = false;

MString			sax3dWriter::msg;
MString			sax3dWriter::version;
MString			sax3dWriter::profileType;
MStringArray	sax3dWriter::comments;
MStringArray	sax3dWriter::commentNames;
MStringArray	sax3dWriter::additionalComps;
MStringArray	sax3dWriter::additionalCompsLevels;
MStringArray	sax3dWriter::haveBeenNodes;
MStringArray	sax3dWriter::ignoredNodes;



sax3dWriter::sax3dWriter()
{

}

sax3dWriter::~sax3dWriter()
{

}

///////////////////////////////
//NEW SECTION
///////////////////////////////
//-----------------------------------------
///Start - document write methods that should be completely independent of 
//the maya API
//
//The next 10 methods are fairly straight forward C++ code used to write
//X3D nodes to a file. Each of these methods will eventually be able
//to write code as either XML, VRML style script, or binary encodings.
//Currently, only the XML encoding is implemented, though there is a 
//place holder for the VRML style - what RawKee calls "Traditional Encoding".
//
//These 11 methods will soon become part of an external SaX3D class/factory.
//
//Should the exEncoding variable be null, set to X3DENC, or set to anything
//other than X3DBENC and VRML97ENC causes the export functions to default
//to XML export.
//------------------------------------------
void sax3dWriter::writeTabs()
{
//	switch(exEncoding)
//	{
//	default:
						//Writing out tabs
						unsigned int i;
						for(i=0;i<tabNumber;i++)
						{
							*newFile << "\t";
						}
//	}

}

void sax3dWriter::writeComponents()
{
	unsigned int compLen = additionalComps.length();
	unsigned int i;
	for(i=0; i< compLen; i++)
	{
		switch(exEncoding)
		{
			case X3DVENC:		*newFile << "COMPONENT " << additionalComps.operator [](i) << ":" << additionalCompsLevels.operator [](i) << "\n";
								break;

			case X3DENC:		writeTabs();
								*newFile << "<component name='" << additionalComps.operator [](i) << "' level='" << additionalCompsLevels.operator [](i) << "'/>\n";
								break;

			case X3DBENC:		writeTabs();
								*newFile << "<component name='" << additionalComps.operator [](i) << "' level='" << additionalCompsLevels.operator [](i) << "'/>\n";
								break;

			default:			break;
		}
	}
}

void sax3dWriter::startDocument()
{
	//method that grabs the optionVar export options

					tabNumber = 0;
	unsigned int	comLen = comments.length();
	unsigned int	i;
	//Setting up headings
	switch(exEncoding)
	{
	case X3DVENC:		*newFile << "#X3D V" << version << " utf8\n";
						profileDecl();
						writeComponents();

						//Write Comments Here
						for(i=0; i< comLen; i++)
						{
							*newFile << "META \"" << commentNames.operator [](i) << "\" \"" << comments.operator [](i) << "\"\n";
						}
						//End Comments

						*newFile << "\n";
						break;

	case VRML97ENC:		*newFile << "#VRML V2.0 utf8\n";

						//Write Comments Here
						for(i=0; i< comLen; i++)
						{
							*newFile << "#" << commentNames.operator [](i) << " - " << comments.operator [](i) << "\n";
						}
						//End Comments
						break;

	default:			*newFile << "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n";
//						*newFile << "<!DOCTYPE X3D PUBLIC \"ISO//Web3D//DTD X3D " << version << "//EN\" \"http://www.web3d.org/specifications/x3d-3.0.dtd\">\n";
						profileDecl();//profileDecl(type);//*newFile << "<X3D>\n";
						tabNumber = tabNumber + 1;

						writeTabs();
						*newFile << "<head>\n";

						//Write Componenets and Comments Here
						tabNumber = tabNumber + 1;
						writeComponents();

						for(i=0; i<comments.length(); i++)
						{
							writeTabs();
							*newFile << "<meta name='" << commentNames.operator [](i) << "' content='" << comments.operator [](i) << "'/>\n";
						}
						//End Comments

						tabNumber = tabNumber - 1;
						writeTabs();
						*newFile << "</head>\n";

						writeTabs();
						*newFile << "<Scene>\n";
						tabNumber = tabNumber + 1;
	}
}

void sax3dWriter::profileDecl()//MString type)
{
	switch(exEncoding)
	{
	case X3DVENC:		*newFile << "PROFILE " << profileType << "\n";
						break;

	case VRML97ENC:		*newFile << "\n";
						break;

	default:			*newFile << "<X3D version = '" << version << "' profile='" << profileType << "'>\n";

	}
}

void sax3dWriter::writeRoute(MString fromNode, MString fromField, MString toNode, MString toField)
{
	writeTabs();
	switch(exEncoding)
	{
	case X3DVENC:
		*newFile <<   "ROUTE "   <<   fromNode << "." << fromField   << " TO " <<   toNode << "." << toField << "\n";
		break;
	case VRML97ENC:
		*newFile <<   "ROUTE "   <<   fromNode << "." << fromField   << " TO " <<   toNode << "." << toField << "\n";
		break;
	default:
		*newFile <<   "<ROUTE fromNode='"   <<   fromNode   <<   "' fromField='"   <<   fromField   <<   "' toNode='"   <<   toNode   <<   "' toField='"   <<   toField   <<   "'/>\n";
		break;
	}
}
void sax3dWriter::startNode(MString x3dType, MString x3dName, MStringArray fields, MStringArray fieldValues, bool hasMore)
{
	bool ciHasBeen = checkIfHasBeen(x3dName);
	if(ciHasBeen == false) setAsHasBeen(x3dName);

	unsigned int fLength = fields.length();
	unsigned int j;
	writeTabs();

	//--------------------------------------
	//Writing out node
	//--------------------------------------
	switch(exEncoding)
	{
	case X3DVENC:		
						if(fLength>0 && hasMultiple != true)
						{
							if(fieldValues.operator [](fieldValues.length()-1).operator !=(""))
							{
								*newFile << fieldValues.operator [](fieldValues.length()-1) << " ";
							}
						}
						hasMultiple = false;
						*newFile << "DEF " << x3dName << " " << x3dType << " {\n";

						//Increase the number of tabs used
						tabNumber = tabNumber + 1;

						if(fLength>0)
						{
							for(j=0;j<fLength-1;j++)
							{
								startField(fields.operator[](j), fieldValues.operator[](j));
								fieldValue(fieldValues.operator[](j));
							}
						}

						if(!hasMore)
						{
							tabNumber = tabNumber-1;
							writeTabs();
							*newFile << "}#" << x3dType << " " << x3dName << "\n";
						}
						break;

	case VRML97ENC:		
						if(fLength>0 && hasMultiple != true)
						{
							if(fieldValues.operator [](fieldValues.length()-1).operator !=(""))
							{
								*newFile << fieldValues.operator [](fieldValues.length()-1) << " ";
							}
						}
						hasMultiple = false;
						*newFile << "DEF " << x3dName << " " << x3dType << " {\n";

						//Increase the number of tabs used
						tabNumber = tabNumber + 1;

						if(fLength>0)
						{
							for(j=0;j<fLength-1;j++)
							{
								startField(fields.operator[](j), fieldValues.operator[](j));
								fieldValue(fieldValues.operator[](j));
							}
						}

						if(!hasMore)
						{
							tabNumber = tabNumber-1;
							writeTabs();
							*newFile << "}\n";
						}
						break;

	default:			*newFile << "<" << x3dType;
						if(x3dName != MString(""))
						{
							*newFile << " DEF='" << x3dName << "'";
						}

						for(j=0;j<fLength;j++)
						{
							startField(fields.operator[](j), fieldValues.operator[](j));
							fieldValue(fieldValues.operator[](j));
						}
						if(hasMore)
						{
							*newFile << ">\n";
							//Increase the number of tabs used
							tabNumber = tabNumber + 1;
						}
						else
						{
							*newFile << "/>\n";
						}
						
	}

}

void sax3dWriter::addScriptNonNodeField(MString accessType, MString fieldType, MString fieldName, MString fieldValue)
{
	writeTabs();
	switch(exEncoding)
	{
		case X3DVENC:
			*newFile << accessType << " " << fieldType << " " << fieldName;
			if(accessType == "initializeOnly" || accessType == "inputOutput")
			{
				*newFile << " " << fieldValue << "\n";
			}
			else *newFile << "\n";
			break;
		case VRML97ENC:
			if(accessType == "outputOnly") accessType.set("eventOut");
			if(accessType == "inputOnly") accessType.set("eventIn");
			if(accessType == "initializeOnly") accessType.set("field"); 
			if(accessType != "inputOutput") 
			{
				*newFile << accessType << " " << fieldType << " " << fieldName;
				if(accessType == "field")
				{
					*newFile << fieldValue << "\n";
				}
				else *newFile << "\n";
			}
			break;
		default:
			break;
	}
}

void sax3dWriter::addScriptNodeField(MString accessType, MString fieldType, MString fieldName)
{
	if(exEncoding == X3DVENC || exEncoding == VRML97ENC) writeTabs();
	switch(exEncoding)
	{
		case X3DVENC:
			*newFile << accessType << " " << fieldType << " " << fieldName << " ";
			if(accessType == "inputOnly" || accessType == "outputOnly") *newFile << "\n";
			break;
		case VRML97ENC:
			if(accessType == "outputOnly") accessType.set("eventOut");
			if(accessType == "inputOnly") accessType.set("eventIn");
			if(accessType == "initializeOnly") accessType.set("field"); 
			if(accessType != "inputOutput") 
			{
				*newFile << accessType << " " << fieldType << " " << fieldName << " ";
				if(accessType == "eventIn" || accessType == "eventOut") *newFile << "\n";
			}
			break;
		default:
			break;
	}
}

void sax3dWriter::addScriptNodeFieldValue(MString value)
{
	MString nValue = processForLineReturns(value);
	if((exEncoding != X3DENC || exEncoding != X3DBENC)&& value.operator !=("")) *newFile << " " << nValue;
}

void sax3dWriter::endScriptNodeField()
{
}

void sax3dWriter::startField(MString x3dFName, MString x3dFValue)
{
	switch(exEncoding)
	{
		case X3DVENC:	
						if(x3dFValue != msEmpty)
						{
							writeTabs();
							*newFile << x3dFName << " ";
						}
						break;
		case VRML97ENC:		
						if(x3dFValue != msEmpty)
						{
							writeTabs();
							*newFile << x3dFName << " ";
						}
						break;
		default:
						if(x3dFValue != msEmpty) *newFile << " " << x3dFName;

	}
}

void sax3dWriter::fieldValue(MString x3dFValue)
{
	MString x3dFValueP = processForLineReturns(x3dFValue);
	switch(exEncoding)
	{
	case X3DVENC:
						if(x3dFValueP == msEmpty) return;
						*newFile << x3dFValueP << "\n";
						break;
	case VRML97ENC:		
						if(x3dFValueP == msEmpty) return;
						*newFile << x3dFValueP << "\n";
						break;

	default:			if(x3dFValueP == msEmpty) return;
						*newFile << "='" << x3dFValueP << "'";
/*
				        const char* characters = x3dFValueP.asChar();
				        int length = x3dFValueP.length();
				        *newFile << "='";
				        for(int i=0; i<length; i++)
						{
							switch(characters[i])
							{
								case '<': *newFile << "&lt;"; break;
								case '>': *newFile << "&gt;"; break;
								case '&': *newFile << "&amp;"; break;
								case '\'': *newFile << "&apos;"; break;
								case '\"': *newFile << "&quot;"; break;
								default: *newFile << characters[i]; break;
							}
						}
				        *newFile << "'";
						*/
	}
}

void sax3dWriter::endField()
{
//	switch(exEncoding)
//	{
//	default:			break;
//	}
}

void sax3dWriter::useDecl(MString x3dType, MString x3dName, MString cField, MString cValue)
{

	if(x3dType != msEmpty)
	{
		switch(exEncoding)
		{
		case X3DVENC:
			if(hasMultiple) writeTabs();
			hasMultiple = false;
			*newFile << "USE " << x3dName << "\n";
						break;

		case VRML97ENC:		
			if(hasMultiple) writeTabs();
			hasMultiple = false;
			*newFile << "USE " << x3dName << "\n";
						break;

		default:				
			writeTabs();
			*newFile << "<" << x3dType;
			*newFile << " USE='" << x3dName << "'";
			startField(cField, cValue);
			fieldValue(cValue);
			*newFile << "/>\n";
		}
	}
	else
	{

		msg.set("Ignoring ");
		msg.operator +=(x3dName);
		msg.operator +=(": Node does not exist!");
		cout << msg << endl;
		msg.set(" ");
		cout << msg << endl;
	}
}

void sax3dWriter::endNode(MString x3dType, MString x3dName)
{
	//Decrease the number of tabs used
	tabNumber = tabNumber - 1;

	writeTabs();

	switch(exEncoding)
	{
	case X3DVENC:
		*newFile << "} #" << x3dType;
		if(x3dName.operator !=(msEmpty))
		{
			*newFile << " " << x3dName << "\n";
		}
		else
		{
			*newFile << "\n";
		}
		break;

	case VRML97ENC:		
		*newFile << "} #" << x3dType;
		if(x3dName.operator !=(msEmpty))
		{
			*newFile << " " << x3dName << "\n";
		}
		else
		{
			*newFile << "\n";
		}
		break;

	default:
		*newFile << "</" << x3dType << ">";
		if(x3dName.operator !=(msEmpty))
		{
			*newFile << " <!-- end of " << x3dName << " -->\n";
		}
		else
		{
			*newFile << "\n";
		}
	}
}

void sax3dWriter::writeSBracket()
{
	if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
	{
		*newFile << "[" << "\n";
		tabNumber = tabNumber+1;
	}
}

void sax3dWriter::writeScriptSBracket()
{
	if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
	{
		*newFile << "[";
		tabNumber = tabNumber+1;
	}
}

void sax3dWriter::preWriteField(MString fieldName)
{
	if((exEncoding == X3DVENC || exEncoding == VRML97ENC) && hasMultiple == false)
	{
		if(fieldName.operator !=(""))
		{
			writeTabs();
			*newFile << fieldName << " ";
		}
	}
}
void sax3dWriter::writeEBracket()
{
	if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
	{
		tabNumber = tabNumber-1;
		writeTabs();
		*newFile << "]" << "\n";
	}
}

void sax3dWriter::writeScriptEBracket()
{
	if(exEncoding == X3DVENC || exEncoding == VRML97ENC)
	{
		*newFile << " ]" << "\n";
		tabNumber = tabNumber-1;
	}
}

void sax3dWriter::writeRawCode(MString rawCode)
{
	*newFile << rawCode;
}

void sax3dWriter::outputCData(MStringArray rawdata)
{
	switch(exEncoding)
	{
	case X3DVENC:
							break;

	case VRML97ENC:		
							break;

//	case X3DBENC:
//							break;

	default:				if(rawdata.length()>0)
							{
								writeTabs();
								*newFile << "<![CDATA[\n";
								tabNumber = tabNumber + 1;
								
								MStringArray newRawdata = tabRawData(rawdata);

								unsigned int rdLength = newRawdata.length();
								unsigned int i;

								for(i=0;i<rdLength;i++)
								{
									writeTabs();
									*newFile << newRawdata.operator [](i);
									*newFile << "\n";
								}

								tabNumber = tabNumber - 1;
								writeTabs();
								*newFile << "]]>\n";
							}
	}
}

MStringArray sax3dWriter::tabRawData(MStringArray rawdata)
{
	MStringArray newRawdata;
	unsigned int rdlen = rawdata.length();
	unsigned int i;
	for(i=0;i<rdlen;i++)
	{
		MString rd = rawdata.operator [](i);
		MStringArray rdret;
		rd.split('\r', rdret);

		MString rdnew("");
		unsigned int rdretlen = rdret.length();
		unsigned int j;
		for(j=0;j<rdretlen;j++)
		{
			rdret.operator [](j).operator +=("\n");
			rdnew.operator +=(rdret.operator [](j));
		}
		MStringArray rdtab;
		rdnew.split('\n',rdtab);
		MString rdtabnew("");

		unsigned int rdtablen = rdtab.length();
		unsigned int k;
		for(k=0;k<rdtablen;k++)
		{
			if(k<rdtablen-1)
			{
				rdtab.operator [](k).operator +=("\n");
				unsigned int l;
				for(l=0;l<tabNumber;l++)
				{
					rdtab.operator [](k).operator +=("\t");
				}
			}
			rdtabnew.operator +=(rdtab.operator [](k));
		}
		newRawdata.append(rdtabnew);
	}
	return newRawdata;
}

void sax3dWriter::endDocument()
{
	switch(exEncoding)
	{
	case X3DVENC:			*newFile << "#End of X3DV file\n";
							break;

	case VRML97ENC:			*newFile << "#End of VRML97 file\n";
							break;

	default:				*newFile << "\t" << "</Scene>\n";
							*newFile << "</X3D>\n";
	}
}
//End - independent document write methods
//******************************************************************
//******************************************************************

//This method checks the MStringArray that holds the names
//of nodes that have already been exported. It returns
//a value of true if a match for a node name is found
//in this array
bool sax3dWriter::checkIfHasBeen(MString nodeName)
{
	bool hasBeen = false;
	unsigned int hbLength = haveBeenNodes.length();
	unsigned int i = 0;

	while(i<hbLength && hasBeen == false)
	{
		if(nodeName == haveBeenNodes.operator [](i)) hasBeen = true;
		i = i + 1;
	}
	return hasBeen;
}

//Appends the name of a node to the MStringArray that
//holds the names of the nodes that have already been
//exported
void sax3dWriter::setAsHasBeen(MString nodeName)
{
	haveBeenNodes.append(nodeName);
}

void sax3dWriter::setIgnored(MString nodeName)
{
	ignoredNodes.append(nodeName);
}


bool sax3dWriter::checkIfIgnored(MString nodeName)
{
	bool hasBeen = false;
	unsigned int hbLength = ignoredNodes.length();
	unsigned int i = 0;

	while(i<hbLength && hasBeen == false)
	{
		if(nodeName == ignoredNodes.operator [](i)) hasBeen = true;
		i = i + 1;
	}
	return hasBeen;
}

void sax3dWriter::clearMemberLists()
{
	ignoredNodes.clear();
	haveBeenNodes.clear();
}

MString sax3dWriter::processForLineReturns(MString sData)
{
	MString newSData;
	MStringArray holdData;
	MStringArray remData;
	MString tabS("\t");
	MString retS("\n");
	sData.split('\r', remData);
	unsigned int m = remData.length();
	unsigned int n;

	MString myString (remData.operator [](0));
	for(n=1;n<m;n++)
	{
		myString.operator +=(remData.operator [](n));
	}
	myString.split('\n', holdData);

	tabNumber = tabNumber+1;
	newSData.set(holdData.operator [](0).asChar());
	unsigned int tabN = tabNumber;
	unsigned int i;
	for(i=1; i<holdData.length(); i++)
	{
		newSData.operator +=(retS);
		unsigned int j;
		for(j=0; j < tabN; j++) newSData.operator +=(tabS);
		newSData.operator +=(holdData.operator [](i));
	}
	tabNumber = tabNumber-1;
	return newSData;
}

MString sax3dWriter::processForTabs(MString sData)
{
	MString newSData;
	MStringArray holdData;
	MString tabS("\t");
	MString retS("\n");
	sData.split('\r', holdData);

	tabNumber = tabNumber+1;
	newSData.set(holdData.operator [](0).asChar());
	unsigned int tabN = tabNumber;
	unsigned int i;
	for(i=1; i<holdData.length(); i++)
	{
//		newSData.operator +=(retS);
		unsigned int j;
		for(j=0; j < tabN; j++) newSData.operator +=(tabS);
		newSData.operator +=(holdData.operator [](i));
	}
	tabNumber = tabNumber-1;
	return newSData;
}

void	sax3dWriter::setHasMultiple(bool value)
{
	hasMultiple = value;
}

void sax3dWriter::writeScriptFile(MString fName, MString contents, MString localPath)
{
	MString fullName = localPath;
	fullName.operator +=(fName);
	ofstream jsFile(fullName.asChar(), ios::out);

	ostream* jsStream = &jsFile;
	if (!jsStream)
	{
		cerr << "EcmaScript could not be written." << endl;
	}
	else
	{
		jsFile.setf(ios::unitbuf);	//Tells the stream to flush after
		*jsStream << contents << endl;
		jsFile.flush();
		jsFile.close();
	}
}

