############################################################################
#  This File is part of Batch Texture and Render Blender Addon             #
#                                                                          #
############################################################################

import bpy, bmesh

from math import pi, tan
from mathutils import Vector

import fnmatch, os
import mimetypes

mimetypes.init()


# Get coordinates of vertices
def coords(objName, space='GLOBAL'):
    # Store reference to the bpy.data.objects datablock
    obj = bpy.data.objects[objName]

    # Store reference to bpy.data.objects[].meshes datablock
    if obj.mode == 'EDIT':
        v = bmesh.from_edit_mesh(obj.data).verts
    elif obj.mode == 'OBJECT':
        v = obj.data.vertices

    if space == 'GLOBAL':
        # Return T * L as list of tuples
        return [(obj.matrix_world * v.co).to_tuple() for v in v]
    elif space == 'LOCAL':
        # Return L as list of tuples
        return [v.co.to_tuple() for v in v]


# Point a light or camera at a location specified by "target"
def point_at(ob, target):
    ob_loc = ob.location
    dir_vec = target - ob.location
    ob.rotation_euler = dir_vec.to_track_quat('-Z', 'Y').to_euler()


# Return the aggregate bounding box of all selected meshes in a scene
def selected_bounding_box():
    # Get names of all meshes
    mesh_names = [v.name for v in bpy.context.selected_objects if v.type == 'MESH']

    # Save an initial value
    # Save as list for single-entry modification
    co = coords(mesh_names[0])[0]
    bb_max = [co[0], co[1], co[2]]
    bb_min = [co[0], co[1], co[2]]

    # Test and store maxima and mimima
    for i in range(0, len(mesh_names)):
        co = coords(mesh_names[i])
        for j in range(0, len(co)):
            for k in range(0, 3):
                if co[j][k] > bb_max[k]:
                    bb_max[k] = co[j][k]
                if co[j][k] < bb_min[k]:
                    bb_min[k] = co[j][k]

    # Convert to tuples
    bb_max = (bb_max[0], bb_max[1], bb_max[2])
    bb_min = (bb_min[0], bb_min[1], bb_min[2])
    return [bb_min, bb_max]


def applyTexture(texture, smartUVProject):
    try:
        textureImage = bpy.data.images.load(texture)
    except:
        raise NameError("Cannot load image %s" % texture)
    # Create image texture
    cTex = bpy.data.textures.new('BatchTex', type='IMAGE')
    cTex.image = textureImage

    bpy.ops.object.mode_set(mode='EDIT')

    # Create material
    mat = bpy.data.materials.new('TexMat')
    while (len(bpy.context.scene.objects.active.data.materials)):
        bpy.context.scene.objects.active.data.materials.pop()
    # Create a new material (link/slot) for the object
    bpy.context.scene.objects.active.data.materials.append(mat)

    # Add texture slot for color texture
    mtex = mat.texture_slots.add()

    mtex.texture = cTex

    # Tone down color map, turn on and tone up normal mapping
    mtex.use_map_normal = True
    mtex.normal_factor = .5

    mtex.texture_coords = 'UV'

    bpy.ops.object.material_slot_assign()

    ### Begin configuring UV coordinates ###
    bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
    bm.faces.ensure_lookup_table()

    bpy.ops.mesh.select_all(action='SELECT')

    # Unwrap to instantiate uv layer
    if (smartUVProject):
        bpy.ops.uv.smart_project()
    else:
        bpy.ops.uv.unwrap()

    bpy.ops.object.mode_set(mode='OBJECT')

    uvMap = bpy.context.scene.objects.active.data.uv_layers[0]

    pivot = Vector((0, 0))
    scale = Vector((4, 4))

    ScaleUV(uvMap, scale, pivot)


def getObjectByType(type):
    for object in bpy.data.objects:
        if object.type == type:
            return object


# orient to selected
def orientCameraLamp(transparent):
    # Get bounding box (meshes only) of selected objects
    bbox = selected_bounding_box()

    # Calculate median of bounding box
    bbox_med = ((bbox[0][0] + bbox[1][0]) / 2,
                (bbox[0][1] + bbox[1][1]) / 2,
                (bbox[0][2] + bbox[1][2]) / 2)

    # Calculate size of bounding box
    bbox_size = ((bbox[1][0] - bbox[0][0]),
                 (bbox[1][1] - bbox[0][1]),
                 (bbox[1][2] - bbox[0][2]))

    # get camera object
    camera = getObjectByType('CAMERA')

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    override = {'window': bpy.context.window
                        , 'screen': bpy.context.window.screen
                        , 'scene': bpy.context.scene
                        , 'area': area, 'region': region}
                    bpy.ops.view3d.view_selected(override)
                    bpy.ops.view3d.camera_to_view(override)
                    bpy.ops.view3d.camera_to_view_selected()
                    bpy.ops.view3d.camera_to_view_selected()
                    bpy.ops.view3d.camera_to_view_selected()
                    bpy.ops.view3d.camera_to_view_selected()
                    bpy.ops.view3d.camera_to_view_selected()
                    bpy.ops.view3d.camera_to_view_selected()

    lamp = getObjectByType('LAMP')
    lamp.name = "Lamp"
    lamp_y_location = camera.location[1]
    lamp_z_location = camera.location[2]
    if (not transparent):
        lamp_y_location += bbox_size[1] / 4
        lamp_z_location += bbox_size[2] / 4
    lamp.location = (camera.location[0], lamp_y_location, lamp_z_location)

    lamp.data.shadow_method = 'RAY_SHADOW'
    lamp.data.shadow_ray_samples = 2
    lamp.data.shadow_color = (.6, .6, .6)
    lamp.data.shadow_soft_size = .9

    point_at(lamp, Vector(bbox_med))


def render(renderFile, transparent):
    orientCameraLamp(transparent)
    if (not os.path.exists(os.path.dirname(renderFile))):
        os.makedirs(os.path.dirname(renderFile))
    bpy.data.scenes['Scene'].render.filepath = renderFile
    # Render
    bpy.ops.render.render(write_still=True)


# Scale a 2D vector v, considering a scale s and a pivot point p
def Scale2D(v, s, p):
    return (p[0] + s[0] * (v[0] - p[0]), p[1] + s[1] * (v[1] - p[1]))


# Scale a UV map iterating over its coordinates to a given scale and with a pivot point
def ScaleUV(uvMap, scale, pivot):
    for uvIndex in range(len(uvMap.data)):
        uvMap.data[uvIndex].uv = Scale2D(uvMap.data[uvIndex].uv, scale, pivot)


# viewpoint front
def viewPointFront():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    override = {'window': bpy.context.window
                        , 'screen': bpy.context.window.screen
                        , 'scene': bpy.context.scene
                        , 'area': area, 'region': region}
                    bpy.ops.view3d.viewnumpad(override, type='FRONT')


def render_texture_batch(batch):
    renderTextureBatch(batch.objFolder, batch.texture, batch.renderFolder, batch.cameraViews,
                       batch.renderWidth, batch.renderHeight, batch.renderFormat, batch.transparent,
                       batch.singleTexture,
                       batch.smartUVProject, batch.orthographicCamera, batch.cameraAngleStart, batch.renderBefore,
                       batch)

#this D:\pyblender\views\_avatar_textures\_avatat_textures_147792-OTYK8C-199after_270.jpg'
def renderTextureBatch(objFolder, texture, renderFolder, cameraViews,
                       renderWidth, renderHeight, renderFormat, transparent, singleTexture,
                       smartUVProject, orthographicCamera, cameraAngleStart, renderBefore, batch=None):
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&" + objFolder)
    #shall i stop ?yeah it is running it takes some time to start ok...over ??
    if (transparent):
        bpy.context.scene.render.alpha_mode = 'TRANSPARENT'
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'
    else:
        bpy.context.scene.render.alpha_mode = 'SKY'

    bpy.context.scene.render.use_file_extension = True
    bpy.context.scene.render.image_settings.file_format = renderFormat
    bpy.context.scene.render.image_settings.quality = 100
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.use_overwrite = True

    cameraViews = int(cameraViews)
    rotation = 2 * pi / cameraViews
    # better we will run with 1 model and 1 texture yeah ok wait
    #now there one modeal and two textures
    # ok.. stop and run

    # Set image resolution in pixels
    # Output will be half the pixelage set here

    bpy.context.scene.render.resolution_x = renderWidth
    bpy.context.scene.render.resolution_y = renderHeight

    textures = []

    if (os.path.isfile(texture)):
        mimetype = mimetypes.guess_type(texture)
        if (mimetype[0] and mimetype[0].startswith('image')):
            textures.append(texture)
        textureFolder = os.path.dirname(texture)
    else:
        textureFolder = texture

    # collect all textures
    for textureDir, dirs, textureFiles in os.walk(textureFolder):
        for textureFile in textureFiles:
            textureFile = os.path.join(textureDir, textureFile)
            mimetype = mimetypes.guess_type(textureFile)
            if (mimetype[0] and mimetype[0].startswith('image')
                    and not os.path.abspath(textureFile) == os.path.abspath(texture)):
                textures.append(textureFile)

    if (len(bpy.data.objects) != 0):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        for mesh in bpy.data.meshes:
            bpy.data.meshes.remove(mesh)

    # Add camera and lamp to scene
    bpy.ops.object.camera_add(location=(0, 0, 0), rotation=(0, 0, 0))
    bpy.ops.object.lamp_add(type='POINT')
    # get camera object
    camera = getObjectByType('CAMERA')
    if (orthographicCamera):
        camera.data.type = 'ORTHO'
    bpy.context.scene.camera = camera

    if (not transparent):
        # Add a background plane
        planeRenderTextureBatch = 'Render Texture Batch Background Object'
        bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0), radius=10)
        bgPlane = getObjectByType('MESH')
        bgPlane.name = planeRenderTextureBatch
        bgPlane.data.name = bgPlane.name
        bpy.ops.transform.rotate(value=0 * pi / 180, axis=(0, 0, 1))

    itemsProcessed = 0
    renderingsProcessed = 0

    objFilenamePattern = '*.obj'

    # folder to ignore
    ignoreFolderNamePattern = '*ignore*'

    for objDir, dirs, objectFiles in os.walk(objFolder):
        if (not fnmatch.fnmatch(objDir, ignoreFolderNamePattern)):
            for objFilename in fnmatch.filter(objectFiles, objFilenamePattern):

                # item name
                itemName = os.path.splitext(os.path.basename(objFilename))[0]
                print("&&&&&&&&&&&&&&&&&&&&&&&&&&" + itemName)
                # this print working ??yeah i will run and show.in avater textures we have images right image name should be
                print(objFilename)

                # select and remove all meshes from scene,
                # except background
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_by_type(type='MESH')
                for object in bpy.context.selected_objects:
                    if ('planeRenderTextureBatch' in locals() and object.name == planeRenderTextureBatch):
                        object.select = False
                    else:
                        bpy.data.meshes.remove(object.data)
                        object.select = True
                bpy.ops.object.delete(use_global=False)

                objFilePath = os.path.join(objDir, objFilename)

                bpy.ops.import_scene.obj(filepath=objFilePath, global_clamp_size=1)

                if (not transparent):
                    bgPlane.location.z = selected_bounding_box()[0][2]

                bpy.ops.transform.rotate(value=(cameraAngleStart * pi / 180), axis=(0, 0, 1))

                viewPointFront()

                if (renderBefore):
                    for cameraView in range(cameraViews):
                        cameraDegree = round((rotation * 180 / pi) * cameraView + cameraAngleStart)

                        # Set render path
                        objFileRelPath = os.path.relpath(objFilePath, objFolder)
                        textureparts = texture.split("/")
                        print(textureparts[len(textureparts) - 1])
                        print(texture.split("/"))
                        renderFile = os.path.join(renderFolder, os.path.dirname(objFileRelPath),
                                                  itemName + '_' + textureparts[
                                                      len(textureparts) - 1] + 'before' + '_' + str(cameraDegree))
                        print(renderFile)
                        render(renderFile, transparent)

                        renderingsProcessed += 1
                        if (batch):
                            batch.renderingsProcessed = renderingsProcessed
                        else:
                            print("renderingsProcessed: " + str(renderingsProcessed))

                        bpy.ops.transform.rotate(value=rotation, axis=(0, 0, 1))

                if (len(textures)):
                    for object in bpy.context.selected_objects:
                        if object.type == 'MESH' and object.name.lower().find('no-texture'.lower()) != 0:
                            bpy.context.scene.objects.active = object
                        else:
                            object.select = False

                    if (singleTexture):
                        if (len(bpy.context.selected_objects) > 1):
                            bpy.ops.object.join()

                    textureIndex = 0
                    for object in bpy.context.selected_objects:
                        if object.type == 'MESH' and object.name.lower().find('no-texture'.lower()) != 0:
                            bpy.context.scene.objects.active = object
                            objectName = object.name
                            if (singleTexture):
                                texture = textures[0]
                                applyTexture(texture, smartUVProject);
                                for object in bpy.context.selected_objects:
                                    if (object.type == 'MESH'):
                                        object.select = True
                                        bpy.context.scene.objects.active = object
                                    else:
                                        object.select = False

                                for cameraView in range(cameraViews):
                                    cameraDegree = round((rotation * 180 / pi) * cameraView + cameraAngleStart)

                                    # Set render path
                                    objFileRelPath = os.path.relpath(objFilePath, objFolder)
                                    textureparts = texture.split("/")
                                    print(objFileRelPath)
                                    #print(textureparts[len(textureparts) - 1])
                                    #print(texture.split("/"))
                                    renderFile = os.path.join(renderFolder, os.path.dirname(objFileRelPath), itemName + '_' + textureparts[len(textureparts) - 1].split('.')[0] + 'after' + '_' + str(cameraDegree))
                                    render(renderFile, transparent)
                                    print(renderFile)

                                    renderingsProcessed += 1
                                    if (batch):
                                        batch.renderingsProcessed = renderingsProcessed
                                    else:
                                        print("renderingsProcessed: " + str(renderingsProcessed))

                                    bpy.ops.transform.rotate(value=rotation, axis=(0, 0, 1))
                            else:
                                for txt in textures:
                                    texture=txt
                                    applyTexture(texture, smartUVProject)
                                    for object in bpy.context.selected_objects:
                                        if (object.type == 'MESH'):
                                            object.select = True
                                            bpy.context.scene.objects.active = object
                                        else:
                                            object.select = False

                                    for cameraView in range(cameraViews):
                                        cameraDegree = round((rotation * 180 / pi) * cameraView + cameraAngleStart)

                                        # Set render path
                                        objFileRelPath = os.path.relpath(objFilePath, objFolder)
                                        print(objFileRelPath)
                                        print("&&&&&&&&"+texture)
                                        textureparts = texture.split("/")
                                        filename = textureparts[-1].split("\\")
                                        directory = filename[0]
                                        file = filename[1]
                                        #print("&&&&&&&&" + textureparts)
                                        #print(textureparts[len(textureparts) - 1])
                                        #print(texture.split("/"))
                                        #this needs to be changed i am missing the iteamname variable in file name

                                        renderFile = os.path.join(renderFolder, os.path.dirname(objFileRelPath),str(itemName) + '_' + directory,  str(itemName) + '_' + file.split('.')[0] + 'after' + '_' + str(
                                                                      cameraDegree))
                                        print(renderFile)
                                        # this should be avatar_textures\file right ?yeah
                                        render(renderFile, transparent)
#once see render function
                                        renderingsProcessed += 1
                                        if (batch):
                                            batch.renderingsProcessed = renderingsProcessed
                                        else:
                                            print("renderingsProcessed: " + str(renderingsProcessed))

                                        bpy.ops.transform.rotate(value=rotation, axis=(0, 0, 1))


                                # texture = next((texture for texture in textures if ##  textures[textureIndex % len(textures)])

                            # textureIndex += 1

                itemsProcessed += 1
                if (batch):
                    batch.itemsProcessed = itemsProcessed
                else:
                    print("itemsProcessed: " + str(itemsProcessed))
    return