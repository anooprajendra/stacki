# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.org
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack
import stack.commands
from collections import OrderedDict
import json


class Command(stack.commands.dump.command):
	"""
	Dump the contents of the stacki database as json.

	This command dumps specifically cart data.  For each cart,
	list its name.

	<example cmd='dump cart'>
	Dump json data for carts in the stacki database
	</example>

	<related>load</related>
	"""

	def run(self, params, args):

		self.set_scope('software')

		dump = []
		for row in self.call('list.cart'):
			dump.append(OrderedDict(name = row['name']))

		self.addText(json.dumps(OrderedDict(version  = stack.version,
						    software = {'cart' : dump}),
					indent=8))
