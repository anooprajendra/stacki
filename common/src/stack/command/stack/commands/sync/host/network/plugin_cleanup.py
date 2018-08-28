# @copyright@
# Copyright (c) 2006 - 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@
#

import os
import re
import stack.commands

class Plugin(stack.commands.Plugin):

	def provides(self):
		return 'cleanup'

	def isStacki(self, filename):
		retval = False

		f = open(filename, 'r')
		for line in f.readlines():
			if '# AUTHENTIC STACKI' in line:
				retval = True
				break	
		f.close()

		return retval

	def run(self, hosts):
		frontend = self.db.getHostname('localhost')

		#
		# only run this on the frontend
		#
		if frontend not in hosts:
			return

		#
		# open all the ifcfg-* files and remove the ones that were not written by Stacki
		#
		ifcfg = re.compile('ifcfg-*')
		for fname in os.listdir('/etc/sysconfig/network'):
			if fname != 'ifcfg-lo' and ifcfg.match(fname):
				filename = '/etc/sysconfig/network/%s' % fname
				if not self.isStacki(filename):
					os.remove(filename)
