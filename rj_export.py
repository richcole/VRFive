import bpy
import bmesh
import json

# This module is designed for exporting meshes so that they can be
# imported into unity. It adds the concept of an attachment face for
# building. Faces can be marked as having attachment types, the idea being
# that each attachment face can attach to face of a compatible type.

# Code to write out the data

def to_list(xs):
    return list(map(lambda x: x, xs))

def point_array(p):
  return (p.x, p.z, -p.y)

def point_json(p):
  return { "p": point_array(p) }

def point_json_from_lst(lst):
  return { "p": to_list(lst) }

def vertex_json(v):
    p = v.co
    n = v.normal
    return {
      "point": point_json(v.co),
      "normal": point_json(v.normal),
      "groups": v.groups
    }

def group_names(groups):
  return list(map(lambda group: group.group, groups))

def vertices_json(vertices):
  return list(map(lambda v: { "p": point_array(v.co), "groups": group_names(v.groups)}, vertices))

def face_json(face):
    return {
      "index": face.index,
      "materialIndex": face.material_index,
      "normal": point_json(face.normal),
      "vertexIndexes": to_list(face.vertices)
    }

def faces_json(faces):
    return list(map(lambda face: face_json(face), faces))

def uv_texture_face_json(uv_texture_face):
    return { "uvList": list(map(lambda uv: point_json_from_lst(uv), uv_texture_face.uv)) }

def uv_texture_layer_json(uv_texture_layer):
    return {
        "name": uv_texture_layer.name,
        "faces": list(map(lambda face: uv_texture_face_json(face), uv_texture_layer.data))
    }

def uv_texture_layers_json(uv_texture_layers):
    return list(map(lambda uv_texture_layer: uv_texture_layer_json(uv_texture_layer), uv_texture_layers))

def materials_json(materials):
    return list(map(lambda material: { "name": material.name }, materials))

def face_attachment(mesh, face_index, attachment_type):
    face = mesh.polygons[face_index]
    return { "position": point_array(face.center), "normal": point_array(face.normal), "attachment_type": attachment_type}

def mesh_attachment_faces(mesh, attachment_faces):
    return list(map(lambda face: face_attachment(mesh, face.index, face.attachment_type), attachment_faces))

def mesh_json(mesh, orig_mesh):
    return {
        "vertices": vertices_json(mesh.vertices),
        "faces": faces_json(mesh.tessfaces),
        "uvLayers": uv_texture_layers_json(mesh.tessface_uv_textures),
        "materials": materials_json(mesh.materials),
        "attachments": mesh_attachment_faces(orig_mesh, orig_mesh.attachment_faces)
    }

def obj_json(scene, obj):
    mesh = obj.to_mesh(scene, True, 'RENDER')
    ret = {
        "name": obj.name,
        "mesh": mesh_json(mesh, obj.data),
        "groups": list(map(lambda group: {"index": group.index, "name": group.name}, obj.vertex_groups))
    }
    bpy.data.meshes.remove(mesh)
    return ret

def export_rj():
    path = 'e:/Unity Projects/Space Station One/Assets/Shapes/'
    for scene in bpy.data.scenes:
        for obj in scene.objects:
            if obj.type == 'MESH':
                output_filename = path + obj.name + ".rj"
                print("Writing %s" % output_filename)
                with open(output_filename, "w") as outp:
                    val = obj_json(scene, obj)
                    outp.write(json.dumps(val, sort_keys=True, indent=4, separators=(',', ': ')))

def get_selected_faces():
  ob = bpy.context.edit_object
  ob.update_from_editmode()
  return list(map(lambda face: face.index, filter(lambda face: face.select, ob.data.polygons)))

def set_attachment_faces(attachment_type):
    af = bpy.context.active_object.data.attachment_faces
    for index in get_selected_faces():
        updated_attachment = False
        for attachment in af:
            if attachment.index == index:
                updated_attachment = True
                attachment.attachment_type = attachment_type
        if not updated_attachment:
            attachment = af.add()
            attachment.index = index
            attachment.attachment_type = attachment_type

class AttachmentIndex(bpy.types.PropertyGroup):
  index = bpy.props.IntProperty(name="index")
  attachment_type = bpy.props.StringProperty(name="attachment_type")

class SetAttachmentFacePanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_set_attachment_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Tools"
    bl_context = "mesh_edit"
    bl_label = "Set Attachment Face"

    attachment_map  = dict()
    attachment_type = "default"

    def draw(self, context):
        mesh = context.object.data
        af = mesh.attachment_faces
        col = self.layout.column(align = True)
        col.prop(mesh, "attachment_type", text="Attachment Type")
        col.operator("mesh.set_attachment_face", text="Set Attachment Type")
        col.operator("mesh.rj_export_operator", text="Export RJ")

class SetAttachmentFaceOperator(bpy.types.Operator):
    bl_idname = "mesh.set_attachment_face"
    bl_label = "Set Attachment Face"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        mesh = context.object.data
        attachment_type = mesh.attachment_type
        print("Setting attachment type to %s" % attachment_type)
        set_attachment_faces(attachment_type)
        return {"FINISHED"}

class RJExportOperator(bpy.types.Operator):
    bl_idname = "mesh.rj_export_operator"
    bl_label = "RJ Export Operator"

    def invoke(self, context, event):
        export_rj()
        return {"FINISHED"}

bl_info = {
  "name": "RJ Export",
  "category": "Object"
}

def register():
    bpy.utils.register_class(AttachmentIndex)
    bpy.utils.register_class(SetAttachmentFaceOperator)
    bpy.utils.register_class(RJExportOperator)
    bpy.utils.register_class(SetAttachmentFacePanel)
    bpy.types.Mesh.attachment_faces = bpy.props.CollectionProperty(name="AttachmentFaces", type=AttachmentIndex)
    bpy.types.Mesh.attachment_type = bpy.props.StringProperty(name="attachment_type")
    print("Register RJ Export")

def unregister():
    bpy.utils.unregister_class(AttachmentIndex)
    bpy.utils.unregister_class(SetAttachmentFacePanel)
    bpy.utils.unregister_class(SetAttachmentFaceOperator)
    bpy.utils.unregister_class(RJExportOperator)
    print("Unregister RJ Export")

if __name__ == "__main__":
    register()
