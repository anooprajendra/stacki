# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands

class Plugin(stack.commands.Plugin):

	def provides(self):
		return 'basic'

	def run(self, args):
		hosts, privkey, no_status = args
		vm_info = dict.fromkeys(hosts, '')
		for vm in hosts:
			vm_info[vm] = []
		keys = ['hypervisor', 'memory', 'cpu', 'pending deletion']
		for row in self.db.select(
			"""
			nodes.name, (SELECT name FROM nodes WHERE nodes.id = vm.hypervisor_id)
			AS hypervisor, vm.memory_size, vm.cpu_cores, vm.vm_delete FROM nodes INNER JOIN virtual_machines vm
			ON nodes.id = vm.node_id
			"""):
				if row[0] in vm_info:
					vm_info[row[0]].extend(row[1:-1])

					# Turn the integer value stored in the database to a
					# boolean for display
					vm_info[row[0]].append(bool(row[-1]))
		return { 'keys' : keys, 'values': vm_info }
