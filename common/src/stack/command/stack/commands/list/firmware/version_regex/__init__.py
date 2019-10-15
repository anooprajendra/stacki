# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.org
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@
#
# @rocks@
# Copyright (c) 2000 - 2010 The Regents of the University of California
# All rights reserved. Rocks(r) v5.4 www.rocksclusters.org
# https://github.com/Teradata/stacki/blob/master/LICENSE-ROCKS.txt
# @rocks@

import stack.commands

class Command(stack.commands.list.firmware.command):
	"""
	Lists all firmware version regexes tracked by stacki.

	<example cmd="list firmware version_regex">
	Lists all firmware version regexes tracked in the stacki database.
	</example>
	"""

	def run(self, params, args):
		header = []
		values = []
		for provides, results in self.runPlugins():
			header.extend(results["keys"])
			values.extend(results["values"])

		self.beginOutput()
		for owner, vals in values:
			self.addOutput(owner = owner, vals = vals)
		self.endOutput(header = header)
