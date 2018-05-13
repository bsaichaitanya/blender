# render_texture_batch
Texture and render Wavefronts (obj files) in batch, using Blender

## texturing
- Texture used is based on user choice, and name of Wavefront objects and textures available in pool
    - For single texturing, texture used is the one selected by user
    - For multiple texturing, texture names matching Wavefront object's name are used
        - An object whose name begins with 'left_sleeve', for example, is textured with texture image file whose basename is left_sleeve
            - For example, object named back-any-other-suffix is textured with back.jpg or back.png
        - When multiple texturing, textures are pooled from directory selected by user
        - If there is no texture image matching name of Wavefront, the batch chooses texture from available pool of textures
        - Matching object names with textures available is done in case insensitive manner
- Wavefronts with name starting with 'no-texture' are not textured
    - For example, Wavefront object named no-texture-arms is left alone
    - This check is case insensitive. That is, no-texture is treated same as NO-teXture