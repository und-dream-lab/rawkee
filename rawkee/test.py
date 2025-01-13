#import maya.app.general.resourceBrowser as resourceBrowser
#resBrowser = resourceBrowser.resourceBrowser()
#path = resBrowser.run()

from nodejs import npx

npx.call(['http-server'])