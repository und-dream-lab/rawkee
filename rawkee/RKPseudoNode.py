import sys

class CommonSurfaceShader():
    def __init__(self):                                     # X3D 3.0 Material Node             # X3D 4.0 Material Node
        
        self.DEF                          = ''
        self.USE                          = ''
        self._RK__containerField          = ''
        self.alphaFactor                  = 1.0             # transparency     0.0              # transparency            0.0           # transparency = 1 - alphaFactor;
        self.alphaTexture                 = None            # -----------NA------------         # -----------NA------------
        self.ambientFactor                = (0.2, 0.2, 0.2) # ambientIntensity 0.2              # ambientIntensity        0.2
        self.ambientTexture               = None            # -----------NA------------         # ambientTexture          None
        self.ambientTextureCoordinateId   = 0               # -----------NA------------         # ambientTextureMapping   ''
        self.diffuseFactor                = (0.8, 0.8, 0.8) # diffuseColor     0.8 0.8 0.8      # diffuseColor            0.8 0.8 0.8
        self.diffuseTexture               = None            # -----------NA------------         # diffuseTexture          None
        self.diffuseTextureCoordinateId   = 0               # -----------NA------------         # diffuseTextureMapping   ''
        self.emissiveFactor               = (0.0, 0.0, 0.0) # emissiveColor    0.0 0.0 0.0      # emissiveColor           0.0 0.0 0.0
        self.emissiveTexture              = None            # -----------NA------------         # emissiveTexture         None
        self.emissiveTextureCoordinateId  = 0               # -----------NA------------         # emissiveTextureMapping  ''
        self.metadata                     = None            # metadata         None             # metadata                None
        self.normalScale                  = (2.0, 2.0, 2.0) # -----------NA------------         # normalScale             1.0
        self.normalTexture                = None            # -----------NA------------         # normalTexture           None
        self.normalTextureCoordinateId    = 0               # -----------NA------------         # normalTextureMapping    ''
        # -----------NA------------                         # -----------NA------------         # occlusionStrength       1.0
        # -----------NA------------                         # -----------NA------------         # occlusionTexture        None
        # -----------NA------------                         # -----------NA------------         # occulsionTextureMapping ''
        self.shininessFactor              = 0.2             # shininess        0.2              # shininess               0.2
        self.shininessTexture             = None            # -----------NA------------         # shininessTexture        None
        self.shininessTextureCoordianteId = 0               # -----------NA------------         # shininessTextureMapping ''
        self.specularFactor               = (0.0, 0.0, 0.0) # specularColor    0.0 0.0 0.0      # specularColor           0.0 0.0 0.0
        self.specularTexture              = None            # -----------NA------------         # specularTexture         None
        self.specularTextureCoordianteId  = 0               # -----------NA------------         # specualrTextureMapping  ''
        

#Only for code development
if __name__ == "__main__":
    cssNode = CommonSurfaceShader()
    print(vars(cssNode))

        