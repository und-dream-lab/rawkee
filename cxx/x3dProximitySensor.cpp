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

// File: x3dProximitySensor.cpp
//
//
// Authors:	Aaron Bergstrom
//         	Computer Visualization Manger
//         	NDSU Archaeology Technologies Laboratory
//         	http://atl.ndsu.edu/
//

#include <rawkee/impl.h>

//-----------------------------------------------
//x3dProximitySensor
//-----------------------------------------------
	const MTypeId x3dProximitySensor::typeId( 0x00108FEF );
	const MString x3dProximitySensor::typeName( "x3dProximitySensor" );

	MObject x3dProximitySensor::enabled;
	MObject x3dProximitySensor::proxCenter;
	MObject x3dProximitySensor::proxSize;

//	const double M_2PI = M_PI * 2.0;

	bool x3dProximitySensor::getBoxPoints(MPointArray &pts) const
	{
		MStatus stat;
		MObject thisNode = thisMObject();
		MFnDependencyNode depNode (thisNode);
		

		pts.clear();
		pts.setSizeIncrement( 1 );

		double sf[3];
		double cf[3];

		MPlug sPlug = depNode.findPlug("proxSize");
		MPlug scPlug = sPlug.child(0);
		scPlug.getValue(sf[0]);
		scPlug = sPlug.child(1);
		scPlug.getValue(sf[1]);
		scPlug = sPlug.child(2);
		scPlug.getValue(sf[2]);

		sPlug = depNode.findPlug("proxCenter");
		scPlug = sPlug.child(0);
		scPlug.getValue(cf[0]);
		scPlug = sPlug.child(1);
		scPlug.getValue(cf[1]);
		scPlug = sPlug.child(2);
		scPlug.getValue(cf[2]);

		double xv = sf[0]/2;
		double yv = sf[1]/2;
		double zv = sf[2]/2;

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

		return true;
	}

	void x3dProximitySensor::draw(M3dView &view, const MDagPath &path, M3dView::DisplayStyle style, M3dView::DisplayStatus status)
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

		glEnd();

		glPopAttrib();
		view.endGL();
	}

	bool x3dProximitySensor::isBounded() const
	{
		return true;
	}

	MBoundingBox x3dProximitySensor::boundingBox() const
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

	MStatus x3dProximitySensor::initialize()
	{
		MStatus stat;
		MFnNumericAttribute numFn;
		enabled = numFn.create("enabled", "enab", MFnNumericData::kBoolean, true);
		addAttribute( enabled );

		proxCenter = numFn.create("proxCenter", "pcntr", MFnNumericData::k3Double, 0);
		numFn.setObject(proxCenter);
		numFn.setKeyable(true);
		addAttribute( proxCenter );

		proxSize = numFn.create("proxSize", "psiz", MFnNumericData::k3Double, 1);
		numFn.setObject(proxSize);
		numFn.setKeyable(true);
		addAttribute( proxSize );

		return MS::kSuccess;
	}

	
	void *x3dProximitySensor::creator()
	{
		return new x3dProximitySensor();
	}
