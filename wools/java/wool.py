from alpakka import register_wool


WOOL = register_wool('Java', __package__, data_type_patterns={
    (r"u?int\d*", "int"),
    (r"string", "String"),
    (r"boolean", "boolean"),
    (r"decimal64", "double"),
    (r"binary", "byte[]"),
    (r"empty", "Object"),
}, options=['prefix', 'beans-only', 'interface-levels'])

PARENT = WOOL.parent
