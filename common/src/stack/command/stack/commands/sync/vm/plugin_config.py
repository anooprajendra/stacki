# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
from stack.kvm import VM
from stack.kvm import VmException
from stack.util import _exec
from stack.argument_processors.vm import VmArgumentProcessor

class Plugin(stack.commands.Plugin, VmArgumentProcessor):
	"""
	Plugin that syncs the database
	values with the current state
	of each virtual machine and
	its storage
	"""

	def provides(self):
		return 'config'

	# Run plugins that handle the non
	# configuration work first
	def requires(self):
		return ['hypervisor', 'storage']

	def run(self, args):
		vm_hosts, host_disks, debug, privkey, sync_ssh, force, autostart = args
		config_errors = []
		self.owner.notify('Sync VM Config')

		# Check if the each disk that has been marked
		# for deletion is no longer on the hypervisor
		# then delete it from the database
		for host, disks in host_disks.items():
			for disk in disks:
				delete_disk = self.owner.str2bool(disk['Pending Deletion'])
				hypervisor = vm_hosts[host]['hypervisor']
				disk_name = disk['Name']

				# Just remove mounted storage as there
				# isn't any files to delete
				if disk['Type'] == 'mountpoint':
					if delete_disk:
						self.delete_pending_disk(host, disk_name)
					continue
				disk_loc = f'{disk["Location"]}/{disk["Image Name"]}'

				# ls has a nonzero returncode if the file isn't found
				# meaning it can be deleted from the database
				disk_on_hypervisor = _exec(f'ssh {hypervisor} "ls {disk_loc}"', shlexsplit=True)
				if delete_disk and (force or disk_on_hypervisor.returncode != 0):
					self.delete_pending_disk(host, disk_name)

		# Start any virtual machines that have been defined
		# if the autostart parameter isn't set to False
		for host, values in vm_hosts.items():
			delete_vm = self.owner.str2bool(values['pending deletion'])
			hypervisor = values['hypervisor']
			try:
				conn = VM(hypervisor, privkey)
				guest_list = conn.guests()
				if host in guest_list and guest_list[host] == 'off':
					if autostart:
						self.owner.notify(f'Starting {host} on {hypervisor}')
						conn.start_domain(host)

					# Always set the vm to start on boot
					conn.autostart(host, True)

				# Remove any virtual machines pending for deletion
				# from the database
				if (force or host not in guest_list) and delete_vm:
					self.delete_pending_vm(host)
					self.owner.notify(f'Removing VM {host}')
			except VmException as error:
				if force and delete_vm:
					self.delete_pending_vm(host)
					config_errors.append(f'Removing VM {host} with force enabled but encountered: {str(error)}')
		return config_errors
