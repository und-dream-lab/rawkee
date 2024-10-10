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

// File: x3dSound.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dSound
//-----------------------------------------------
	const MTypeId x3dSound::typeId( 0x00108F66 );
	const MString x3dSound::typeName( "x3dSound" );

	MObject x3dSound::direction;
	MObject x3dSound::intensity;
	MObject x3dSound::location;
	MObject x3dSound::maxBack;
	MObject x3dSound::maxFront;
	MObject x3dSound::minBack;
	MObject x3dSound::minFront;
	MObject x3dSound::priority;
	MObject x3dSound::spatialize;


	MStatus x3dSound::initialize()
	{
		MStatus stat;
		MFnNumericAttribute numFn;
		direction = numFn.create("direction", "dir", MFnNumericData::k3Double, 0);
		numFn.setObject(direction);
		numFn.setKeyable(true);

		intensity = numFn.create("intensity", "intense", MFnNumericData::kFloat, 1);
		numFn.setObject(intensity);
		numFn.setMin(0.0);
		numFn.setMax(1.0);
		numFn.setKeyable(true);

		location = numFn.create("location", "loc", MFnNumericData::k3Double, 0);
		numFn.setObject(location);
		numFn.setKeyable(true);

		maxBack = numFn.create("maxBack", "maxB", MFnNumericData::kFloat, 10);
		numFn.setObject(maxBack);
		numFn.setMin(0.0);
		numFn.setKeyable(true);

		maxFront = numFn.create("maxFront", "maxF", MFnNumericData::kFloat, 10);
		numFn.setObject(maxFront);
		numFn.setMin(0.0);
		numFn.setKeyable(true);

		minBack = numFn.create("minBack", "minB", MFnNumericData::kFloat, 1);
		numFn.setObject(minBack);
		numFn.setMin(0.0);
		numFn.setKeyable(true);

		minFront = numFn.create("minFront", "minF", MFnNumericData::kFloat, 1);
		numFn.setObject(minFront);
		numFn.setMin(0.0);
		numFn.setKeyable(true);

		priority = numFn.create("priority", "prior", MFnNumericData::kFloat, 0);
		numFn.setObject(priority);
		numFn.setMin(0.0);
		numFn.setMax(1.0);
		numFn.setKeyable(true);

		spatialize = numFn.create("spatialize", "spat", MFnNumericData::kBoolean, true);
		
		addAttribute( direction );
		addAttribute( intensity );
		addAttribute( location );
		addAttribute( maxBack );
		addAttribute( maxFront );
		addAttribute( minBack );
		addAttribute( minFront );
		addAttribute( priority );
		addAttribute( spatialize );

		return MS::kSuccess;
	}

	bool x3dSound::getEllipsePoints(MPointArray &pts, MString location, MString front, MString back) const
	{
		MStatus stat;
		MObject thisNode = thisMObject();
		MFnDependencyNode depNode (thisNode);
		

		pts.clear();
		pts.setSizeIncrement( 1 );

		double loc[3];


		MPlug locPlug = depNode.findPlug(location);
		MPlug l1Plug = locPlug.child(0);
		l1Plug.getValue(loc[0]);
		
		MPlug l2Plug = locPlug.child(1);
		l2Plug.getValue(loc[1]);

		MPlug l3Plug = locPlug.child(2);
		l3Plug.getValue(loc[2]);

		MPlug maxFront = depNode.findPlug(front);
		MPlug maxBack = depNode.findPlug(back);

		double maf = 0;
		double mab = 0;
		double mif = 0;
		double mib = 0;

		maxFront.getValue(maf);
		maxBack.getValue(mab);

		double maLen = maf+mab;
		double maFoci = maf-mab;
		double maHalf = maLen/2;
		double maRadius = (sqrt((maLen*maLen) - (maFoci*maFoci)))/2;

		double maRadSqr = maRadius * maRadius;
		double maHalfSqr = maHalf * maHalf;

		double zOne = (maHalf * 0.5);
		double tOne = (zOne * zOne) * maRadSqr;
		double xOne = sqrt(maRadSqr - (tOne/maHalfSqr));

		double zTwo = (maHalf * 0.8);
		double tTwo = (zTwo * zTwo) * maRadSqr;
		double xTwo = sqrt(maRadSqr - (tTwo/maHalfSqr));

		MPoint pt0;
		pt0.x = loc[0];
		pt0.y = loc[1];
		pt0.z = loc[2];
		pts.append(pt0);

		double arrowTip = 0.1 * maLen;
		MPoint pt1;
		pt1.x = loc[0];
		pt1.y = loc[1];
		pt1.z = loc[2]+arrowTip;
		pts.append(pt1);

		double arrowBarb = arrowTip - (arrowTip * 0.25);
		MPoint pt2;
		pt2.x = loc[0];
		pt2.y = loc[1]+ arrowTip - arrowBarb;
		pt2.z = loc[2]+ arrowBarb;
		pts.append(pt2);

		//Outer rings
		MPoint pt3;
		pt3.x = loc[0];
		pt3.y = loc[1];
		pt3.z = loc[2] - mab;
		pts.append(pt3);

		MPoint pt3a;
		pt3a.x = loc[0] + xTwo;
		pt3a.y = loc[1];
		pt3a.z = loc[2] - mab + (maHalf * 0.2);
		pts.append(pt3a);

		MPoint pt3b;
		pt3b.x = loc[0] + xOne;
		pt3b.y = loc[1];
		pt3b.z = loc[2] - mab + (maHalf * 0.5);
		pts.append(pt3b);

		MPoint pt4;
		pt4.x = loc[0] + maRadius;
		pt4.y = loc[1];
		pt4.z = loc[2] - mab + maHalf;
		pts.append(pt4);

		MPoint pt4a;
		pt4a.x = loc[0] + xOne;
		pt4a.y = loc[1];
		pt4a.z = loc[2] - mab + maHalf + (maHalf * 0.5);
		pts.append(pt4a);

		MPoint pt4b;
		pt4b.x = loc[0] + xTwo;
		pt4b.y = loc[1];
		pt4b.z = loc[2] - mab + maHalf + (maHalf * 0.8);
		pts.append(pt4b);

		MPoint pt5;
		pt5.x = loc[0];
		pt5.y = loc[1];
		pt5.z = loc[2] - mab + maLen;
		pts.append(pt5);

		MPoint pt5a;
		pt5a.x = loc[0] - xTwo;
		pt5a.y = loc[1];
		pt5a.z = loc[2] - mab + maHalf + (maHalf * 0.8);
		pts.append(pt5a);

		MPoint pt5b;
		pt5b.x = loc[0] - xOne;
		pt5b.y = loc[1];
		pt5b.z = loc[2] - mab + maHalf + (maHalf * 0.5);
		pts.append(pt5b);

		MPoint pt6;
		pt6.x = loc[0] - maRadius;
		pt6.y = loc[1];
		pt6.z = loc[2] - mab + maHalf;
		pts.append(pt6);

		MPoint pt6a;
		pt6a.x = loc[0] - xOne;
		pt6a.y = loc[1];
		pt6a.z = loc[2] - mab + (maHalf * 0.5);
		pts.append(pt6a);

		MPoint pt6b;
		pt6b.x = loc[0] - xTwo;
		pt6b.y = loc[1];
		pt6b.z = loc[2] - mab + (maHalf * 0.2);
		pts.append(pt6b);

		//Outer top ring
		MPoint pt7;
		pt7.x = loc[0];
		pt7.y = loc[1] + xTwo;
		pt7.z = loc[2] - mab + (maHalf * 0.2);
		pts.append(pt7);

		MPoint pt8;
		pt8.x = loc[0];
		pt8.y = loc[1] + xOne;
		pt8.z = loc[2] - mab + (maHalf * 0.5);
		pts.append(pt8);

		MPoint pt9;
		pt9.x = loc[0];
		pt9.y = loc[1] + maRadius;
		pt9.z = loc[2] - mab + maHalf;
		pts.append(pt9);

		MPoint pt10;
		pt10.x = loc[0];
		pt10.y = loc[1] + xOne;
		pt10.z = loc[2] - mab + maHalf + (maHalf * 0.5);
		pts.append(pt10);

		MPoint pt11;
		pt11.x = loc[0];
		pt11.y = loc[1] + xTwo;
		pt11.z = loc[2] - mab + maHalf + (maHalf * 0.8);
		pts.append(pt11);

		MPoint pt12;
		pt12.x = loc[0];
		pt12.y = loc[1] - xTwo;
		pt12.z = loc[2] - mab + maHalf + (maHalf * 0.8);
		pts.append(pt12);

		MPoint pt13;
		pt13.x = loc[0];
		pt13.y = loc[1] - xOne;
		pt13.z = loc[2] - mab + maHalf + (maHalf * 0.5);
		pts.append(pt13);

		MPoint pt14;
		pt14.x = loc[0];
		pt14.y = loc[1] - maRadius;
		pt14.z = loc[2] - mab + maHalf;
		pts.append(pt14);

		MPoint pt15;
		pt15.x = loc[0];
		pt15.y = loc[1] - xOne;
		pt15.z = loc[2] - mab + (maHalf * 0.5);
		pts.append(pt15);

		MPoint pt16;
		pt16.x = loc[0];
		pt16.y = loc[1] - xTwo;
		pt16.z = loc[2] - mab + (maHalf * 0.2);
		pts.append(pt16);

		return true;
	}

	void x3dSound::draw(M3dView &view, const MDagPath &path, M3dView::DisplayStyle style, M3dView::DisplayStatus status)
	{
		
		view.beginGL();
		glPushAttrib(GL_CURRENT_BIT);
		MPointArray pts;
		MPointArray pts2;
		getEllipsePoints( pts, "location", "maxFront", "maxBack" );
		getEllipsePoints( pts2, "location", "minFront", "minBack" );

		double dir[3];
		MObject thisNode = thisMObject();
		MFnDependencyNode depNode (thisNode);

		MPlug sPlug = depNode.findPlug("direction");
		MPlug scPlug = sPlug.child(0);
		scPlug.getValue(dir[0]);
		scPlug = sPlug.child(1);
		scPlug.getValue(dir[1]);
		scPlug = sPlug.child(2);
		scPlug.getValue(dir[2]);

		glRotated(180, 0, 1, 0);
		glRotated((dir[2] * -1), 0, 0, 1);
		glRotated(dir[1], 0, 1, 0);
		glRotated((dir[0] * -1), 1, 0, 0);

		//arrow
			glBegin(GL_LINE_STRIP);
				glVertex3f( float(pts[0].x), float(pts[0].y), float(pts[0].z));
				glVertex3f( float(pts[1].x), float(pts[1].y), float(pts[1].z));
				glVertex3f( float(pts[2].x), float(pts[2].y), float(pts[2].z));
			glEnd();
		//max
			glBegin(GL_LINE_STRIP);
				glVertex3f( float(pts[3].x), float(pts[3].y), float(pts[3].z));
				glVertex3f( float(pts[4].x), float(pts[4].y), float(pts[4].z));
				glVertex3f( float(pts[5].x), float(pts[5].y), float(pts[5].z));
				glVertex3f( float(pts[6].x), float(pts[6].y), float(pts[6].z));
				glVertex3f( float(pts[7].x), float(pts[7].y), float(pts[7].z));
				glVertex3f( float(pts[8].x), float(pts[8].y), float(pts[8].z));
				glVertex3f( float(pts[9].x), float(pts[9].y), float(pts[9].z));
				glVertex3f( float(pts[10].x), float(pts[10].y), float(pts[10].z));
				glVertex3f( float(pts[11].x), float(pts[11].y), float(pts[11].z));
				glVertex3f( float(pts[12].x), float(pts[12].y), float(pts[12].z));
				glVertex3f( float(pts[13].x), float(pts[13].y), float(pts[13].z));
				glVertex3f( float(pts[14].x), float(pts[14].y), float(pts[14].z));
				glVertex3f( float(pts[3].x), float(pts[3].y), float(pts[3].z));

				glVertex3f( float(pts[15].x), float(pts[15].y), float(pts[15].z));
				glVertex3f( float(pts[16].x), float(pts[16].y), float(pts[16].z));
				glVertex3f( float(pts[17].x), float(pts[17].y), float(pts[17].z));
				glVertex3f( float(pts[18].x), float(pts[18].y), float(pts[18].z));
				glVertex3f( float(pts[19].x), float(pts[19].y), float(pts[19].z));
				glVertex3f( float(pts[9].x), float(pts[9].y), float(pts[9].z));
				glVertex3f( float(pts[20].x), float(pts[20].y), float(pts[20].z));
				glVertex3f( float(pts[21].x), float(pts[21].y), float(pts[21].z));
				glVertex3f( float(pts[22].x), float(pts[22].y), float(pts[22].z));
				glVertex3f( float(pts[23].x), float(pts[23].y), float(pts[23].z));
				glVertex3f( float(pts[24].x), float(pts[24].y), float(pts[24].z));
				glVertex3f( float(pts[3].x), float(pts[3].y), float(pts[3].z));
			glEnd();
		//min
			glBegin(GL_LINE_STRIP);
				glVertex3f( float(pts2[3].x), float(pts2[3].y), float(pts2[3].z));
				glVertex3f( float(pts2[4].x), float(pts2[4].y), float(pts2[4].z));
				glVertex3f( float(pts2[5].x), float(pts2[5].y), float(pts2[5].z));
				glVertex3f( float(pts2[6].x), float(pts2[6].y), float(pts2[6].z));
				glVertex3f( float(pts2[7].x), float(pts2[7].y), float(pts2[7].z));
				glVertex3f( float(pts2[8].x), float(pts2[8].y), float(pts2[8].z));
				glVertex3f( float(pts2[9].x), float(pts2[9].y), float(pts2[9].z));
				glVertex3f( float(pts2[10].x), float(pts2[10].y), float(pts2[10].z));
				glVertex3f( float(pts2[11].x), float(pts2[11].y), float(pts2[11].z));
				glVertex3f( float(pts2[12].x), float(pts2[12].y), float(pts2[12].z));
				glVertex3f( float(pts2[13].x), float(pts2[13].y), float(pts2[13].z));
				glVertex3f( float(pts2[14].x), float(pts2[14].y), float(pts2[14].z));
				glVertex3f( float(pts2[3].x), float(pts2[3].y), float(pts2[3].z));

				glVertex3f( float(pts2[15].x), float(pts2[15].y), float(pts2[15].z));
				glVertex3f( float(pts2[16].x), float(pts2[16].y), float(pts2[16].z));
				glVertex3f( float(pts2[17].x), float(pts2[17].y), float(pts2[17].z));
				glVertex3f( float(pts2[18].x), float(pts2[18].y), float(pts2[18].z));
				glVertex3f( float(pts2[19].x), float(pts2[19].y), float(pts2[19].z));
				glVertex3f( float(pts2[9].x), float(pts2[9].y), float(pts2[9].z));
				glVertex3f( float(pts2[20].x), float(pts2[20].y), float(pts2[20].z));
				glVertex3f( float(pts2[21].x), float(pts2[21].y), float(pts2[21].z));
				glVertex3f( float(pts2[22].x), float(pts2[22].y), float(pts2[22].z));
				glVertex3f( float(pts2[23].x), float(pts2[23].y), float(pts2[23].z));
				glVertex3f( float(pts2[24].x), float(pts2[24].y), float(pts2[24].z));
				glVertex3f( float(pts2[3].x), float(pts2[3].y), float(pts2[3].z));
			glEnd();
		glPopAttrib();
		view.endGL();
	}

	bool x3dSound::isBounded() const
	{
		return true;
	}

	MBoundingBox x3dSound::boundingBox() const
	{
		MPointArray pts;
		getEllipsePoints( pts, "location", "maxFront", "maxBack" );

		MBoundingBox bbox;

		for(unsigned int i=0; i<pts.length(); i++)
		{
			bbox.expand(pts[i]);
		}
		return bbox;
	}

	void *x3dSound::creator()
	{
		return new x3dSound();
	}
