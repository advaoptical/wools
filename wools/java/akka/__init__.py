from alpakka import WOOLS
from .akka_wool import AkkaWool

WOOL = AkkaWool('Akka', __package__, parent=WOOLS['java'])
WOOLS.register(WOOL)
