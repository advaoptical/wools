from alpakka import WOOLS
from .jersey_wool import JerseyWool

WOOL = JerseyWool('Jersey', __name__, parent=WOOLS['java'])
WOOLS.register(WOOL)
