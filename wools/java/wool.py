from wools.java.java_wool import JavaWool
from alpakka import WOOLS

WOOL = JavaWool('Java', __package__, WOOLS.default)
WOOLS.register(WOOL)

PARENT = WOOL.parent
