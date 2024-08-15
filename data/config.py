import os
import sys
from pathlib import Path

arb_rpc = "https://arbitrum.rpc.subquery.network/public"
wallet = '0x316a514eBBd588Fe36419748129e151DaC5326bb'

if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent.absolute()
else:
    ROOT_DIR = Path(__file__).parent.parent.absolute()

ABIS_DIR = os.path.join(ROOT_DIR, 'data', 'abis')
