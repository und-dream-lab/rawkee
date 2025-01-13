import sys
import maya.cmds as cmds
import maya.mel as mel

from maya import OpenMaya as omui
from PySide6 import QtWidgets
from shiboken6         import wrapInstance

mainWindowPtr = omui.MQtUtil.mainWindow()
object = wrapInstance(int(mainWindowPtr), QtWidgets.QMainWindow)

menus = cmds.window('MayaWindow', query=True, ma=True)

mlen = len(menus)

if mlen > 0:
    value = cmds.menu(menus[0], query=True, parent=True)
#    pval = "MayaWindow|m_menubar_MayaWindow|" + menus[0] 
#    cmds.setParent(pval)
#    cmds.menuItem(label='CHEESE')
    print(value)
    print(mlen)
else:
    print("Value is 0")
print("Something")

#cmds.menu( label='Stuff6', p='MayaWindow')
#cmds.menuItem(label='cheese')
#cmds.menuItem(image=':menu_options.png', optionBox=True)
#cmds.menuItem(divider=True, dividerLabel='File - Import/Export' )
#cmds.menuItem(label='Export X3D Files', command='maya.cmds.rkX3DExport()')
#cmds.menuItem(image=':menu_options.png', optionBox=True)

#menus = cmds.window(mel.eval('$temp1=$gMainWindow'), q=True, ma=True)
#lm = len(menus)
#cmds.setParent(menus[lm-2])

#    menu_items_and_their_commands[menu] = {}
#    for item in cmds.menu(menu, q=True, ia=True) or []:
#        menu_items_and_their_commands[menu][item] = cmds.menuItem(item, q=True, c=True)