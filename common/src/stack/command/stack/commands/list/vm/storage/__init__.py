# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@
#

import stack.commands
from stack.exception import ParamError

class Command(stack.commands.list.vm.Command):
	"""
	List virtual machine storage information.

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
		privkey, hypervisor = self.fillParams([
			('private_key', '/root/.ssh/id_rsa'),
			('hypervisor', '')
		])

		# Get all valid virtual machine hosts
		vm_hosts = self.valid_vm_args(args)
		vm_disks = {}
		if hypervisor and not self.is_hypervisor(hypervisor):
			raise ParamError(self, 'hypervisor', f'{hypervisor} not a valid hypervisor')
		self.beginOutput()

		# Remove any hosts not belonging to the hypervisor param
		# if it's set
		for vm in vm_hosts:
			vm_hypervisor = self.get_hypervisor_by_name(vm)
			if hypervisor and vm_hypervisor != hypervisor:
				continue
			vm_disks[vm] = {}

		header = ['Virtual Machine', 'Name', 'Type', 'Location', 'Size', 'Image Name', 'Image Archive', 'Mountpoint', 'Pending Deletion']

		# Gather information from nodes and virtual machines table as well
		# to get the hostnames for the virtual machine
		for row in self.db.select(
			"""
			nodes.name, vmd.id, disk_name, disk_type, disk_location, disk_size, image_file_name, image_archive_name,
			mount_disk, vmd.disk_delete FROM virtual_machine_disks vmd INNER JOIN virtual_machines vm
			ON vmd.virtual_machine_id = vm.id INNER JOIN nodes ON vm.node_id = nodes.id
			"""):
				if row[0] in vm_disks:
					vm_disks[row[0]][row[1]] = list(row[2:-1])

					# Turn disk deletion value into a bool
					# for display
					vm_disks[row[0]][row[1]].append(bool(row[-1]))
		self.beginOutput()
		for vm_name, disks in vm_disks.items():
			for disk_id, disk_vals in disks.items():
				self.addOutput(owner = vm_name, vals = disk_vals)
		self.endOutput(header=header, trimOwner=False)
