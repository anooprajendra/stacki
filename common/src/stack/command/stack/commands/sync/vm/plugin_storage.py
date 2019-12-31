# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
from stack.kvm import Hypervisor
from stack.kvm import VmException
from stack.argument_processors.vm import VmArgumentProcessor
from stack.util import _exec
from pathlib import Path

class Plugin(stack.commands.Plugin, VmArgumentProcessor):

	def provides(self):
		return 'storage'

	def requires(self):
		return ['hypervisor']

	def precedes(self):
		return ['config']

	def pack_ssh_key(self, hypervisor, disk, location, image):
		"""
		Returns a list with an error messages encountered
		when packing the frontend's ssh key into a VM image
		"""

		copy_key = _exec(f'scp /root/.ssh/id_rsa.pub {hypervisor}:/tmp/authorized_keys', shlexsplit=True)
		if copy_key.returncode != 0:
			return [copy_key.stderr]
		pack_image = _exec(
			f'ssh {hypervisor} "image_packer.py --files=/tmp/authorized_keys --image_locations=/root/.ssh/ {location}/{image}"',
			shlexsplit=True
		)
		if pack_image.returncode != 0:
			return [pack_image.stderr]
		remove_key = _exec(f'ssh {hypervisor} "rm /tmp/authorized_keys"', shlexsplit=True)
		if remove_key.returncode != 0:
			return [pack_image.stderr]
		return []

	def add_disk(self, hypervisor, disk, sync_ssh, debug):
		"""
		Add a given disk to a hypervisor
		Returns any errors that occurred.
		"""

		disk_type = disk['Type']
		image_loc = Path(disk['Location'])
		add_errors = []

		# Create a disk at the specified location
		if disk_type == 'disk':
			pool = image_loc.name
			try:
				conn = stack.kvm.Hypervisor(hypervisor)
				add_pool = conn.add_pool(image_loc.name, image_loc)
				if not add_pool and debug:
					self.owner.notify(f'Pool {pool} already created, skipping')
				vol_name = disk['Image Name']
				if debug:
					self.owner.notify(f'Create storage volume {vol_name} with size {disk["Size"]}')

				# add the disk to the hypervisor
				conn.add_volume(vol_name, image_loc, pool, disk['Size'])
			except VmException as error:
				add_errors.append(str(error))

		# copy disk images over if
		# they aren't already present
		# Then uncompress images if they
		# are in a tar or gzip archive
		elif disk_type == 'image':
			image_name = Path(disk['Image Name']).name

			# Transfer the archive if the image is in one
			# otherwise transfer the image itself
			if disk['Image Archive']:
				copy_file = disk['Image Archive']
			else:
				copy_file = disk['Image Name']
			try:
				conn = stack.kvm.Hypervisor(hypervisor)
				if debug:
					self.owner.notify(f'Transferring file {copy_file}')

				# Copy the image
				conn.copy_image(copy_file, image_loc, image_name)
			except VmException as error:
				add_errors.append(str(error))

			# Add the frontend's ssh key, assume the image contains an OS
			if sync_ssh:
				if debug:
					self.owner.notify(f'Adding frontend ssh key to {image_name}')
				pack_ssh_errors = self.pack_ssh_key(hypervisor, disk, image_loc, image_name)
				if pack_ssh_errors and debug:
					add_errors.append(f'Failed to pack frontend ssh key: {pack_ssh_errors}')
		return add_errors

	def remove_disk(self, hypervisor, disk, debug):
		"""
		Remove the given disk volume or image from the
		hypervisor host
		"""

		disk_type = disk['Type']
		image_loc = Path(disk['Location'])
		remove_errors = []

		if disk_type == 'disk':
			vol_name = disk['Image Name']
			try:
				conn = stack.kvm.Hypervisor(hypervisor)
				if debug:
					self.owner.notify(f'Removing disk {vol_name}')

				# Remove a volume from it's pool
				# which is determined by the last
				# part of the path of the disk location
				conn.remove_volume(image_loc.name, vol_name)
			except VmException as error:
				remove_errors.append(str(error))

		# Remove an image file on the hypervisor
		elif disk_type == 'image':
			image_name = Path(disk['Image Name']).name
			try:
				conn = stack.kvm.Hypervisor(hypervisor)
				if debug:
					self.owner.notify(f'Removing image {image_name}')
				conn.remove_image(f'{image_loc}/{image_name}')
			except VmException as error:
				remove_errors.append(str(error))
		return remove_errors

	def run(self, args):
		hosts, host_disks, debug, sync_ssh, force, hypervisor = args
		config_errors = []
		self.owner.notify('Sync VM Storage')
		for host, disks in host_disks.items():
			hypervisor = hosts[host]['hypervisor']
			for disk in disks:

				# Remove any disks assigned to a vm marked for deletion
				if self.owner.str2bool(disk['Pending Deletion']):
					remove_output = self.remove_disk(hypervisor, disk, debug)
					config_errors.extend(remove_output)

				# Otherwise try to add it
				else:
					add_output = self.add_disk(hypervisor, disk, sync_ssh, debug)
					config_errors.extend(add_output)
		return config_errors
