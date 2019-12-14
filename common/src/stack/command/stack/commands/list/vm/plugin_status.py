# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
import stack.kvm
from stack.kvm import VmException
from stack.argument_processors.vm import VmArgumentProcessor

class Plugin(stack.commands.Plugin, VmArgumentProcessor):

	def provides(self):
		return 'status'

	def requires(self):
		return ['basic']

	def run(self, args):
		hosts, privkey, no_status = args
		vm_status = dict.fromkeys(hosts, '')
		for vm in hosts:
			vm_status[vm] = []
		keys = ['status']
		hypervisor_status = {}

		# Skip this plugin if no_status is set
		if no_status:
			return {'keys': [], 'values': {} }

		for host in hosts:
			conn = None

			# Get the hypervisor hostname
			host_hypervisor = self.get_hypervisor_by_name(host)
			try:
				conn = stack.kvm.VM(host_hypervisor, privkey)

				# returns a dict of all vm's saying if they are on or off
				guest_status = conn.guests()
				if host in guest_status:
					vm_status[host].append(guest_status[host])
				else:
					vm_status[host].append('undefined')
				conn.close()

			# If an exception was raised, set the status
			# to connection failed
			except VmException as error:
				if conn:
					conn.close()
				vm_status[host].append('Connection failed to hypervisor')
		return { 'keys' : keys, 'values': vm_status }
