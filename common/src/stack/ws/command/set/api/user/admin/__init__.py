#
# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@
#

import os
import sys

import stack.commands
import stack.django_env
from django.contrib.auth.models import Group, User
from stack.exception import *


class Command(stack.commands.Command, stack.commands.HostArgumentProcessor):
    """
	Set or unset admin privileges of a user.
	<arg name="Username" type="string">
	Username of user for which to set / unset
	the admin privileges.
	</arg>
	<param name="admin" type="string">
	Set or unset admin privileges.
	</param>
	"""

    def run(self, params, args):
        # Get Username
        if len(args) != 1:
            raise ArgRequired(self, "username")
        username = args[0]
        (admin,) = self.fillParams([("admin", "True"),])
        try:
            u = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(self, "User %s does not exist" % username)

        admin = self.str2bool(admin)
        u.is_superuser = admin
        u.save()
