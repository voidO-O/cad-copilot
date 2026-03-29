from cad_builder import create_cylinder, create_sphere, translate, boolean_cut, boolean_fuse, boolean_common


TOOLS = {
    "cylinder": create_cylinder,
    "sphere": create_sphere,
    "translate": translate,
    "cut": boolean_cut,
    "union": boolean_fuse,
    "fuse": boolean_fuse,
    "common": boolean_common,
}