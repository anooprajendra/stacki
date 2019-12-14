from stack.exception import CommandError
import copy

class VmArgumentProcessor():
	"""
	Mixin class to collect various functions for getting
	virtual machine values
	"""

	def vm_by_name(self, vm_name):
		"""
		Return a virtual machine's info
		by its hostname. All required info must be
		present for a return value to be present
		(hypervisor id, host id, memory, and cpu )
		"""

		result = self.db.select(
			"""
			* FROM virtual_machines vm
			INNER JOIN nodes ON vm.node_id = nodes.id
			WHERE nodes.name = %s AND COALESCE(vm.id, vm.hypervisor_id, vm.node_id, vm.memory_size, vm.cpu_cores)
			IS NOT NULL
			""", (vm_name)
		)
		return result

	def vm_id_by_name(self, vm_name):
		"""
		Get the id in the virtual machine's table
		by the vm hostname
		"""

		result = self.db.select(
			"""
			virtual_machines.id FROM virtual_machines
			INNER JOIN nodes ON virtual_machines.node_id = nodes.id
			WHERE nodes.name = %s
			""", (vm_name)
		)
		return list(*result)[0]

	def valid_vm(self, vm_name):
		"""
		Determine if the given input host is a valid virtual machine
		"""

		# If vm_by_name returns a non empty value for the given input,
		# it is a valid input as all required values are present in the
		# database table
		if not self.vm_by_name(vm_name):
			return False
		else:
			return True

	def valid_vm_args(self, args):
		"""
		Returns a list of valid virtual machines to the caller
		Raises a CommandError if one or more hosts are not
		valid virtual machines
		"""

		hosts = self.getHostnames(args)

		# Use valid_vm to determine if the vm is
		# defined
		vm_hosts = self.getHostnames(args,
			host_filter = lambda self, host: self.valid_vm(host)
		)
		vm_hosts = list(vm_hosts)

		# Need to check if args is empty or not
		# as getHostnames will return all hosts if args
		# is empty and in that case we skip the check
		if args and vm_hosts != hosts:
			raise CommandError(self, f'One or more hosts are not a valid virtual machine')
		return vm_hosts

	def get_hypervisor_by_name(self, vm_name):
		"""
		Get the hostname of a vm's hypervisor via
		the vm hostname
		"""

		vm_id = self.vm_id_by_name(vm_name)
		result = self.db.select(
			"""
			nodes.name FROM nodes INNER JOIN virtual_machines
			ON nodes.id = virtual_machines.hypervisor_id AND
			virtual_machines.id = %s
			""", (vm_id, )
		)
		return list(*result)[0]

	def is_hypervisor(self, hypervisor):
		"""
		Determine if the input host is a valid hypervisor
		via it's appliance.
		"""

		appliance = self.getHostAttr(hypervisor, 'appliance')
		if appliance == 'vms' or appliance == 'hypervisor':
			return True
		else:
			return False

	def hypervisor_id_by_name(self, hypervisor):
		"""
		Get the hypervisor id in the nodes table via
		its hostname
		"""

		return self.db.select(
			"""
			nodes.id FROM nodes WHERE nodes.name = %s
			""", (hypervisor, )
		)

	def vm_info(self, hosts, hypervisor = '', no_status = ''):
		"""
		Get the output of 'list vm' arranged by hostname
		Can be sorted optionally by hypervisor or exclude
		current vm status for speeding up execution time
		"""

		# Copy the hosts arg to append extra
		# parameters
		args = copy.copy(hosts)
		args.append(f'hypervisor={hypervisor}')
		args.append(f'no-status={no_status}')
		try:
			vm_hosts = self.call('list.vm', args)
		except CommandError:
			return {}
		vm_by_hostname = {}

		# Arrange as a dict sorted by hostname
		for vm in vm_hosts:
			vm_name = vm['virtual machine']
			vm_attr = vm.pop('virtual machine', None)
			vm_by_hostname[vm_name] = vm

		return vm_by_hostname

	def vm_disks(self, hosts):
		"""
		Get the output of 'list vm storage' arranged
		by vm host name
		"""

		try:
			vm_hosts = self.call('list.vm.storage', hosts)
		except CommandError:
			return {}

		vm_by_hostname = {}

		for vm in vm_hosts:
			vm_name = vm['Virtual Machine']
			vm_attr = vm.pop('Virtual Machine', None)
			vm_by_hostname.setdefault(vm_name, []).append(vm)

		return vm_by_hostname

	def vm_disk_names(self, host, disk_type = '', disk_attr = 'Name'):
		"""
		Return a flat list of one vm disk attr for all given hosts
		Defaults to the disk name, can optionally be
		a different value and only for a certain disk type
		(disk, image, or mountpoint)
		"""

		disk_names = []
		if disk_type and disk_type not in ['disk', 'image', 'mountpoint']:
			return disk_names
		host_disks = self.call('list.vm.storage', host)
		for disk in host_disks:
			if disk_type and disk['Type'] != disk_type:
				continue
			else:
				disk_names.append(disk[disk_attr])
		return disk_names

	def get_all_disks(self, hosts):
		"""
		Return a dict of vm disk info ordered by hostname
		"""

		disks = dict.fromkeys(hosts, [])
		for host in hosts:
			host_id = self.vm_id_by_name(host)
			for row in self.db.select(
				"""
				disk_name, disk_type, disk_size, disk_location, disk_delete,
				image_file_name, image_archive_name, mount_disk from virtual_machine_disks
				WHERE virtual_machine_id = %s
				""", (host_id, )
			):
				disks[host].append(row)

		return disks

	def delete_pending_disk(self, host, disk_name):
		"""
		For a given host and disk name, delete it
		from the database if it's been marked for
		deletion prior via remove vm storage command
		"""

		vm_id = self.vm_id_by_name(host)
		return self.db.execute(
			"""
			DELETE FROM virtual_machine_disks WHERE
			virtual_machine_disks.virtual_machine_id = %s AND
			virtual_machine_disks.disk_delete = 1 AND
			virtual_machine_disks.disk_name = %s
			""", (vm_id, disk_name)
		)

	def delete_pending_vm(self, host):
		"""
		For a given virtual machine,
		Delete it from the database if
		its been marked for deletion prior
		via remove vm command
		"""

		vm_id = self.vm_id_by_name(host)
		return self.db.execute(
			"""
			DELETE FROM virtual_machines WHERE
			virtual_machines.id = %s AND
			virtual_machines.vm_delete = 1
			""", (vm_id, )
		)
