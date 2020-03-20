#!/opt/stack/bin/python3 -E
#
# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@
#

import json
import socket
import sys

from stack_site import *

msg = None
if len(sys.argv) > 1:
    msg = sys.argv[1:]

if not msg:
    sys.exit(-1)

sys.path.append("/tmp")

health = {"channel": "health", "message": " ".join(msg)}

tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tx.sendto(json.dumps(health).encode(), (attributes["Kickstart_PrivateAddress"], 5000))
tx.close()
