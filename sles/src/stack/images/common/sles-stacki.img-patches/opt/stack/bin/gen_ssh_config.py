#!/opt/stack/bin/python3

import os
import stat
import subprocess
import sys

import stack_site

sys.path.append("/tmp")

# Write Authorized Keys File for
# passwordless login from the frontend
f = open("/authorized_keys", "w")
f.write("%s\n" % stack_site.authorized_key)
f.close()
os.chmod("/authorized_keys", stat.S_IRUSR)

# Write the Host ECDSA Key. Required for
# the SSH Server to start
f = open("/etc/ssh/ssh_host_ecdsa_key", "w")
f.write("%s\n" % stack_site.host_key)
f.close()
os.chmod("/etc/ssh/ssh_host_ecdsa_key", stat.S_IRUSR)

pts = "/dev/pts"
if not os.path.isdir(pts):
    os.makedirs(pts)

f = open("/etc/mtab", "r")
found_pts = False
for i in f.readlines():
    if i.startswith("devpts"):
        found_pts = True
        break

if not found_pts:
    subprocess.run(["mount", "-t", "devpts", "devpts", pts])
