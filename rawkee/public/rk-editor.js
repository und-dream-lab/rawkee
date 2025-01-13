function rkOnload()
{
    alert("Get Ready!");
    rkCanvas = document.getElementById("rkCanvas");
    rkString = "<?xml version='1.0' encoding='UTF-8'?><!DOCTYPE X3D PUBLIC 'ISO//Web3D//DTD X3D 4.0//EN' 'https://www.web3d.org/specifications/x3d-4.0.dtd'><X3D profile='Full' version='4.0' xmlns:xsd='http://www.w3.org/2001/XMLSchema-instance' xsd:noNamespaceSchemaLocation='https://www.web3d.org/specifications/x3d-4.0.xsd'><Scene><Shape><Sphere DEF='Fun'></Sphere></Shape><Transform DEF='Garb' translation='3.0 4.5 3.0'><Transform rotation='0.3 4.3 30.21 0.0' translation='3.0 0.0 0.0'></Transform></Transform></Scene></X3D>";
    rkCanvas.innerHTML = rkString;
}