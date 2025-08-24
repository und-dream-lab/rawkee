import sys

class CommonSurfaceShader():
    def __init__(self):                                     # X3D 3.0 Material Node             # X3D 4.0 Material Node
        
        self.DEF                          = ''
        self.USE                          = ''
        
        self.alphaFactor                  = 1.0             # transparency     0.0              # transparency            0.0           # transparency = 1 - alphaFactor;
        self.alphaTexture                 = None            # -----------NA------------         # -----------NA------------
        self.alphaTextureChannelMask      = 'a'
        self.alphaTextureCoordinatesId    = 0
        self.alphaTextureId               = -1
        
        self.ambientFactor                = (0.2, 0.2, 0.2) # ambientIntensity 0.2              # ambientIntensity        0.2
        self.ambientTexture               = None            # -----------NA------------         # ambientTexture          None
        self.ambientTextureChannelMask    = 'rgb'
        self.ambientTextureCoordinatesId  = 0               # -----------NA------------         # ambientTextureMapping   ''
        self.ambientTextureId             = -1
        
        self.binormalTextureCoordinatesId = -1
        
        self.diffuseDisplacementTexture   = None
        
        self.diffuseFactor                = (0.8, 0.8, 0.8) # diffuseColor     0.8 0.8 0.8      # diffuseColor            0.8 0.8 0.8
        self.diffuseTexture               = None            # -----------NA------------         # diffuseTexture          None
        self.diffuseTextureChannelMask    = 'rgb'
        self.diffuseTextureCoordinatesId  = 0               # -----------NA------------         # diffuseTextureMapping   ''
        self.diffuseTextureId             = -1
        
        self.displacementAxis             = 'y'
        self.displacementFactor           = 255.0
        self.displacementTexture          = None
        self.displacementTextureCoordinatesId = 0
        self.displacementTextureId        = 0
        
        self.emissiveFactor               = (0.0, 0.0, 0.0) # emissiveColor    0.0 0.0 0.0      # emissiveColor           0.0 0.0 0.0
        self.emissiveTexture              = None            # -----------NA------------         # emissiveTexture         None
        self.emissiveTextureChannelMask   = 'rgb'
        self.emissiveTextureCoordinatesId = 0               # -----------NA------------         # emissiveTextureMapping  ''
        self.emissiveTextureId            = -1
        
        self.environmentFactor            = (1.0, 1.0, 1.0)
        self.environmentTexture           = None
        self.environmentTextureChannelMask = 'rgb'
        self.environmentTextureCoordinatesId = 0
        self.environmentTextureId         = -1
        
        self.fresnelBlend                 = 0
        
        self.invertAlphaTexture           = False
        
        self.language                     = ''
        
        self.metadata                     = None            # metadata         None             # metadata                None
        
        self.normalBias                   = (-1.0, -1.0, -1.0)
        self.normalFormat                 = 'UNORM'
        self.normalScale                  = (2.0, 2.0, 2.0) # -----------NA------------         # normalScale             1.0
        self.normalSpace                  = 'TANGENT'
        self.normalTexture                = None            # -----------NA------------         # normalTexture           None
        self.normalTextureChannelMask     = 'rgb'
        self.normalTextureCoordinatesId   = 0               # -----------NA------------         # normalTextureMapping    ''
#            normalTextureCoordinatesId
        self.normalTextureId              = -1
        
        self.reflectionFactor             = (0.0, 0.0, 0.0)
        self.reflectionTexture            = None
        self.reflectionTextureChannelMask = 'rgb'
        self.reflectionTextureCoordinatesId = 0
        self.reflectionTextureId          = -1
        
        self.relativeIndexOfRefraction    = 1
        
        # -----------NA------------                         # -----------NA------------         # occlusionStrength       1.0
        # -----------NA------------                         # -----------NA------------         # occlusionTexture        None
        # -----------NA------------                         # -----------NA------------         # occulsionTextureMapping ''
        
        self.shininessFactor              = 0.2             # shininess        0.2              # shininess               0.2
        self.shininessTexture             = None            # -----------NA------------         # shininessTexture        None
        self.shininessTextureChannelMask  = 'a'
        self.shininessTextureCoordinatesId = 0               # -----------NA------------         # shininessTextureMapping ''
        self.shininessTextureId           = -1
        
        self.specularFactor               = (0.0, 0.0, 0.0) # specularColor    0.0 0.0 0.0      # specularColor           0.0 0.0 0.0
        self.specularTexture              = None            # -----------NA------------         # specularTexture         None
        self.specularTextureChannelMask   = 'rgb'
        self.specularTextureCoordinatesId = 0               # -----------NA------------         # specularTextureMapping  ''
#            specularTextureCoordinatesId
        self.specularTextureId            = -1
        
        self.tangentTextureCoordinatesId  = -1
        
        self.transmissionFactor           = (0.0, 0.0, 0.0)
        self.transmissionTexture          = None
        self.transmissionTextureChannelMask = 'rgb'
        self.transmissionTextureCoordinatesId = 0
        self.transmissionTextureId        = -1
        

#Only for code development
if __name__ == "__main__":
    cssNode = CommonSurfaceShader()
    print(vars(cssNode))

        