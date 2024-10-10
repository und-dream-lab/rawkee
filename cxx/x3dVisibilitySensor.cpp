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

// File: x3dVisibilitySensor.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dVisibilitySensor
//-----------------------------------------------
	const MTypeId x3dVisibilitySensor::typeId( 0x00108F7C );
	const MString x3dVisibilitySensor::typeName( "x3dVisibilitySensor" );

	MObject x3dVisibilitySensor::enabled;
	MObject x3dVisibilitySensor::visCenter;
	MObject x3dVisibilitySensor::visSize;

//	const double M_2PI = M_PI * 2.0;

	bool x3dVisibilitySensor::getBoxPoints(MPointArray &pts) const
	{
		MStatus stat;
		MObject thisNode = thisMObject();
		MFnDependencyNode depNode (thisNode);
		

		pts.clear();
		pts.setSizeIncrement( 1 );

		float sf[3];
		float cf[3];

		MPlug sPlug = depNode.findPlug("visSize");
		MPlug scPlug = sPlug.child(0);
		scPlug.getValue(sf[0]);
		scPlug = sPlug.child(1);
		scPlug.getValue(sf[1]);
		scPlug = sPlug.child(2);
		scPlug.getValue(sf[2]);

		sPlug = depNode.findPlug("visCenter");
		scPlug = sPlug.child(0);
		scPlug.getValue(cf[0]);
		scPlug = sPlug.child(1);
		scPlug.getValue(cf[1]);
		scPlug = sPlug.child(2);
		scPlug.getValue(cf[2]);

		float xv = sf[0]/2;
		float yv = sf[1]/2;
		float zv = sf[2]/2;

		MPoint pt0;
		pt0.x = xv+cf[0];
		pt0.y = yv+cf[1];
		pt0.z = zv+cf[2];
		pts.append(pt0);

		MPoint pt1;
		pt1.x = (xv*-1) + cf[0];
		pt1.y = yv+cf[1];
		pt1.z = zv+cf[2];
		pts.append(pt1);

		MPoint pt2;
		pt2.x = (xv*-1) + cf[0];
		pt2.y = (yv*-1) + cf[1];
		pt2.z = zv+cf[2];
		pts.append(pt2);

		MPoint pt3;
		pt3.x = xv+cf[0];
		pt3.y = (yv*-1) + cf[1];
		pt3.z = zv+cf[2];
		pts.append(pt3);

		MPoint pt4;
		pt4.x = xv+cf[0];
		pt4.y = (yv*-1) + cf[1];
		pt4.z = (zv*-1) + cf[2];
		pts.append(pt4);

		MPoint pt5;
		pt5.x = xv+cf[0];
		pt5.y = yv+cf[1];
		pt5.z = (zv*-1) + cf[2];
		pts.append(pt5);

		MPoint pt6;
		pt6.x = (xv*-1) + cf[0];
		pt6.y = yv+cf[1];
		pt6.z = (zv*-1) + cf[2];
		pts.append(pt6);

		MPoint pt7;
		pt7.x = (xv*-1) + cf[0];
		pt7.y = (yv*-1) + cf[1];
		pt7.z = (zv*-1) + cf[2];
		pts.append(pt7);

		MPoint pt8;
		pt8.x = cf[0];
		pt8.y = yv + cf[1];
		pt8.z = zv + cf[2];
		pts.append(pt8);

		return true;
	}

	void x3dVisibilitySensor::draw(M3dView &view, const MDagPath &path, M3dView::DisplayStyle style, M3dView::DisplayStatus status)
	{
		view.beginGL();
		glPushAttrib(GL_CURRENT_BIT);
		MPointArray pts;
		getBoxPoints( pts );
		glBegin(GL_LINE_STRIP);

		//Face 1
		glVertex3f( float(pts[1].x), float(pts[1].y), float(pts[1].z));
		glVertex3f( float(pts[2].x), float(pts[2].y), float(pts[2].z));
		glVertex3f( float(pts[3].x), float(pts[3].y), float(pts[3].z));
		glVertex3f( float(pts[1].x), float(pts[1].y), float(pts[1].z));
		glVertex3f( float(pts[0].x), float(pts[0].y), float(pts[0].z));
		glVertex3f( float(pts[2].x), float(pts[2].y), float(pts[2].z));
		glVertex3f( float(pts[0].x), float(pts[0].y), float(pts[0].z));
		glVertex3f( float(pts[3].x), float(pts[3].y), float(pts[3].z));

		//Face2
		glVertex3f( float(pts[4].x), float(pts[4].y), float(pts[4].z));
		glVertex3f( float(pts[5].x), float(pts[5].y), float(pts[5].z));
		glVertex3f( float(pts[0].x), float(pts[0].y), float(pts[0].z));
		glVertex3f( float(pts[5].x), float(pts[5].y), float(pts[5].z));
		glVertex3f( float(pts[4].x), float(pts[4].y), float(pts[4].z));

		//Face3
		glVertex3f( float(pts[7].x), float(pts[7].y), float(pts[7].z));
		glVertex3f( float(pts[5].x), float(pts[5].y), float(pts[5].z));
		glVertex3f( float(pts[6].x), float(pts[6].y), float(pts[6].z));
		glVertex3f( float(pts[4].x), float(pts[4].y), float(pts[4].z));
		glVertex3f( float(pts[5].x), float(pts[5].y), float(pts[5].z));
		glVertex3f( float(pts[6].x), float(pts[6].y), float(pts[6].z));
		glVertex3f( float(pts[7].x), float(pts[7].y), float(pts[7].z));

		//Face4
		glVertex3f( float(pts[2].x), float(pts[2].y), float(pts[2].z));
		glVertex3f( float(pts[1].x), float(pts[1].y), float(pts[1].z));
		glVertex3f( float(pts[6].x), float(pts[6].y), float(pts[6].z));

		//The V
		glVertex3f( float(pts[8].x), float(pts[8].y), float(pts[8].z));
		glVertex3f( float(pts[5].x), float(pts[5].y), float(pts[5].z));

		glEnd();

		glPopAttrib();
		view.endGL();
	}

	bool x3dVisibilitySensor::isBounded() const
	{
		return true;
	}

	MBoundingBox x3dVisibilitySensor::boundingBox() const
	{
		MPointArray pts;
		getBoxPoints( pts );

		MBoundingBox bbox;

		for(unsigned int i=0; i<pts.length(); i++)
		{
			bbox.expand(pts[i]);
		}
		return bbox;
	}

	MStatus x3dVisibilitySensor::initialize()
	{
		MStatus stat;
		MFnNumericAttribute numFn;
		enabled = numFn.create("enabled", "enab", MFnNumericData::kBoolean, true);
		addAttribute( enabled );

		visCenter = numFn.create("visCenter", "vcntr", MFnNumericData::k3Float, 0);
		numFn.setObject(visCenter);
		numFn.setKeyable(true);
		addAttribute( visCenter );

		visSize = numFn.create("visSize", "vsiz", MFnNumericData::k3Float, 1);
		numFn.setObject(visSize);
		numFn.setKeyable(true);
		addAttribute( visSize );
		return MS::kSuccess;
	}

	
	void *x3dVisibilitySensor::creator()
	{
		return new x3dVisibilitySensor();
	}
