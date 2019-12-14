# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
from stack.kvm import VM
from stack.kvm import VmException

class Plugin(stack.commands.Plugin):
	"""
	Plugin for syncing the definition of removal
	of virtual machines
	"""

	def provides(self):
		return 'hypervisor'

	def add_vm(self, host, debug, hypervisor, privkey):
		"""
		Add a host to a hypervisor
		Returns any hypervisor errors encountered
		"""

		add_errors = []
		if debug:
			self.owner.notify(f'Generating vm config file for {host}')

			# Get the libvirt config
			# the bare parameter gets removes the SUX tags
		vm_config = self.owner.call('report.vm', [host, 'bare=y'])
		try:
			conn = stack.kvm.VM(hypervisor, privkey)
			conn.add_domain(vm_config[0]['col-1'])
		except VmException as error:
			add_errors.append(str(error))
		return add_errors

	def remove_vm(self, host, debug, hypervisor, privkey):
		"""
		Remove a given host from a hypervisor
		Returns any hypervisor errors encountered
		"""

		remove_errors = []
		try:
			conn = stack.kvm.VM(hypervisor, privkey)
			conn.remove_domain(host)
		except VmException as error:
			remove_errors.append(str(error))
		return remove_errors

	def run(self, args):
		vm_hosts, host_disks, debug, privkey, sync_ssh, force, autostart = args
		hypervisor_errors = []
		self.owner.notify('Sync VM Definitions')
		for host, values in vm_hosts.items():
			delete_vm = self.owner.str2bool(values['pending deletion'])
			status = values['status']
			kvm_name = values['hypervisor']
			if (status != 'on' or force):

				# Virtual machines are removed then added again
				# with a new config file as libvirt lacks
				# the ability to do this otherwise
				if status != 'undefined':
					hypervisor_errors.append('\n'.join(self.remove_vm(host, debug, kvm_name, privkey)))

				# If a virtual machine is pending for deletion
				# don't add it again
				if not delete_vm:
					if status == 'undefined':
						self.owner.notify(f'Adding VM {host} to {kvm_name}')
					hypervisor_errors.append('\n'.join(self.add_vm(host, debug, kvm_name, privkey)))
			else:
				self.owner.notify(f'Skipping VM {host} on hypervisor {kvm_name}, vm is on')
		return hypervisor_errors
