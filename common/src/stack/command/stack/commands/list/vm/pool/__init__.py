# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@
#

import stack.commands
from stack.kvm import Hypervisor, VmException
from stack.exception import ParamError

class Command(stack.commands.list.vm.Command):
	"""
	List the storage pool information on a hypervisor

	<arg optional='1' type='string' name='host' repeat='1'>
	The name of a virtual machine host.
	</arg>

	<param type='string' name='hypervisor'>
	Only display hosts on a specific hypervisor.
	</param>

	<example cmd='list vm storage virtual-backend-0-0'>
	List virtual-backend-0-0 storage information.
	</example>

	<example cmd='list vm storage hypervisor=hypervisor-0-1'>
	List all disks belonging to virtual machines hosted on
	hypervisor-0-1
	</example>
	"""

	def run(self, param, args):
		hypervisor, pool=self.fillParams([
			('hypervisor', ''),
			('pool', '')
		])

		# Get all valid virtual machine hosts
		hosts = self.valid_vm_args(args)
		hypervisor_hosts = []

		if hypervisor and not self.is_hypervisor(hypervisor):
			raise ParamError(self, 'hypervisor', f'{hypervisor} not a valid hypervisor')

		self.beginOutput()
		header = [
					'Hypervisor',
					'Name',
					'Location',
					'Size'
		]

		conn = Hypervisor(hypervisor)
		pool_info = hypervisor.pool_info(filter_pool=pool)

				self.addOutput(owner = vm_name, vals = disk_vals)
		self.endOutput(header=header, trimOwner=False)
