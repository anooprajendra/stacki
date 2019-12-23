# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@
#

import stack.commands
import random
import uuid
from pathlib import Path
from stack.exception import CommandError
from stack.argument_processors.vm import VmArgumentProcessor
from stack import api
from stack.util import _exec

class command(stack.commands.HostArgumentProcessor,
              stack.commands.report.command):
        pass

class Command(command, VmArgumentProcessor):
	"""
	Output a libvirt virtual machine config based on
	information stored in Stacki for a given host

	<arg type='string' name='host' repeat='1' optional='1'>
	The host/mutliple hosts to output a config of
	</arg>

	<param type='bool' name='bare'>
	Output the config file in non-SUX format for feeding
	directly to the hypervisor.
	</param>
	"""

	def getMAC(self):
		"""
		Generate a random mac address for
		virtual machine interfaces
		"""

		r = random.SystemRandom()
		m = "%06x" % r.getrandbits(24)

		return "52:54:00:%s:%s:%s" % (m[0:2], m[2:4], m[4:6])

	def getInterfaceByNetwork(self, host, network):
		"""
		Return the first network interface for a host on a specified network
		"""

		for interface in api.Call('list.host.interface', args=[host]):
			if interface['network'] == network and network != None:
				return interface['interface']

	def doStorage(self, host, disks):
		"""
		Generate the storage portion of the libvirt xml
		"""

		storagexml = []
		diskid = 0
		disks = sorted(disks, key=lambda d: d['Name'])
		for disk in disks:
			disk_delete = self.str2bool(disk['Pending Deletion'])
			if not disk['Name'] or disk_delete:
				continue
			pool = Path(disk['Location'])

			# Sata is needed for new volumes due to
			# default partition scheme expecting sda
			bus_type = 'sata'
			src_path = ''
			dev = 'file'
			src_type = 'file'
			devname = disk['Name']

			# Handle premade qcow or raw images
			if disk['Type'] == 'image':
				vol = Path(disk['Image Name'])
				frmt_type = vol.suffix.replace('.', '')
				bus_type = 'virtio'
				src_path = Path(f'{pool}/{vol.name}')

			# Handle block devices
			elif disk['Type'] == 'mountpoint':
				vol = disk['Mountpoint']
				frmt_type = 'raw'
				dev = 'block'
				src_type = 'dev'
				src_path = Path(vol)

			# Specify new volumes
			elif disk['Type'] == 'disk':

				# Change the bus type if the devname
				# is vdX
				if 'vd' in devname:
					bus_type = 'virtio'
				vol_name = disk['Image Name']
				frmt_type = 'qcow2'
				diskid += 1
				src_path = Path(f'{pool}/{vol_name}')

			# Output storage part of libvirt config
			storagexml.append(f'<disk device="disk" type="{dev}">')
			storagexml.append(f'<driver cache="none" type="{frmt_type}" name="qemu" io="native"/>')
			storagexml.append(f'<source {src_type}="{src_path}"/>')
			storagexml.append(f'<target dev="{devname}" bus="{bus_type}"/>')
			storagexml.append(f'<boot order="{self.bootorder}"/>')
			storagexml.append('</disk>')
			self.bootorder += 1
		return storagexml

	def doNetwork(self, host):
		"""
		Generate the network interface portion
		for a libvirt config
		"""

		netxml = []
		vm_host = self.get_hypervisor_by_name(host)

		for interface in api.Call('list.host.interface', [ host ]):
			interface_name = interface['interface']
			network = interface['network']
			network_pxe = False

			# Check if the hypervisor has a interface on the same network
			# as the virtual machine
			host_interface = self.getInterfaceByNetwork(vm_host, network)

			# Skip ipmi interfaces or if the hypervisor has no interface
			# on the network
			if interface_name == 'ipmi' or not host_interface:
				continue
			if network:

				# If the network isn't set for pxe, don't useit has a boot target in the bootorder
				network_pxe = self.str2bool(api.Call('list.network', args = [network])[0].get('pxe', False))

			mac_addr = interface['mac']

			# If no mac address is assinged to a VM's
			# interface, generate one
			if not mac_addr:
				mac_addr = self.getMAC()
				self.command('set.host.interface.mac', [host, f'interface={interface_name}', f'mac={mac_addr}'])

			# Output the libvirt xml for the interface
			netxml.append('<interface type="bridge">')
			netxml.append(f'<mac address="{mac_addr}"/>')
			netxml.append(f'<source bridge="{host_interface}"/>')
			netxml.append('<model type="virtio"/>')
			if network_pxe:
				netxml.append(f'<boot order="{self.bootorder}"/>')
				self.bootorder += 1
			netxml.append('</interface>')
		return netxml

	def buildGuestXML(self, name, info, disks):
		"""
		Generate the entire libvirt xml for the
		given host
		"""

		# Intalize the boot ordering of the vm
		self.bootorder = 1

		memsize = int(info['memory']) * 1024
		numcpus = info['cpu']

		guestxml = []
		guestxml.append('<domain type="kvm">')

		guestxml.append(f'<name>{name}</name>')
		guestxml.append(f'<uuid>{uuid.uuid4()}</uuid>')

		guestxml.append(f'<memory>{memsize}</memory>')
		guestxml.append(f'<vcpu>{numcpus}</vcpu>')

		guestxml.append('<os>')
		guestxml.append('<type arch="x86_64">hvm</type>')
		guestxml.append('</os>')

		guestxml.append('<features>')
		guestxml.append('<acpi/>')
		guestxml.append('<apic/>')
		guestxml.append('<vmport state="off"/>')
		guestxml.append('</features>')

		guestxml.append('<clock offset="utc">')
		guestxml.append('<timer name="rtc" tickpolicy="catchup"/>')
		guestxml.append('<timer name="pit" tickpolicy="delay"/>')
		guestxml.append('<timer name="hpet" present="no"/>')
		guestxml.append('</clock>')

		guestxml.append('<on_poweroff>destroy</on_poweroff>')
		guestxml.append('<on_reboot>restart</on_reboot>')
		guestxml.append('<on_crash>restart</on_crash>')

		guestxml.append('<pm>')
		guestxml.append('<suspend-to-mem enabled="no"/>')
		guestxml.append('<suspend-to-disk enabled="no"/>')
		guestxml.append('</pm>')

		guestxml.append('<devices>')
		guestxml.append('<emulator>/usr/bin/qemu-kvm</emulator>')

		guestxml = guestxml + self.doNetwork(name)
		guestxml = guestxml + self.doStorage(name, disks)

		guestxml.append('<serial type="pty">')
		guestxml.append('<target port="0"/>')
		guestxml.append('</serial>')

		guestxml.append('<serial type="pty">')
		guestxml.append('<target port="1"/>')
		guestxml.append('</serial>')

		guestxml.append('<input bus="ps2" type="mouse"/>')

		guestxml.append('<graphics autoport="yes" keymap="en-us" type="vnc" port="-1"/>')

		guestxml.append('<video>')
		guestxml.append('<model heads="1" vram="9216" type="cirrus"/>')
		guestxml.append('</video>')

		guestxml.append('<rng model="virtio">')
		guestxml.append('<backend model="random">/dev/random</backend>')
		guestxml.append('<address type="pci" domain="0x0000" bus="0x00" slot="0x0c" function="0x0"/>')
		guestxml.append('</rng>')

		guestxml.append('</devices>')

		guestxml.append('</domain>')

		return '\n'.join(guestxml)

	def run(self, param, args):
		self.beginOutput()
		vm_hosts = self.valid_vm_args(args)

		out = []

		# Strip the SUX tags if set to true
		bare_output, hypervisor = self.fillParams([
			('bare', False),
			('hypervisor', '')
		])
		bare_output = self.str2bool(bare_output)
		vm_info =  {vm['virtual machine']: vm for vm in self.call('list.vm', vm_hosts)}
		vm_disks = {}
		for disk in self.call('list.vm.storage', vm_hosts):
			host = disk['Virtual Machine']
			disk.pop('Virtual Machine')
			vm_disks.setdefault(host, []).append(disk)

		# Check if the hypervisor is valid
		# if the param is set
		if hypervisor and not self.is_hypervisor(hypervisor):
			raise ParamError(self, 'hypervisor', '{hypervisor} is not a valid hypervisor')

		for vm in vm_hosts:

			# If the hypervisor param is set
			# ignore any VM not belonging to the
			# specified hypervisor host
			if hypervisor and self.get_hypervisor_by_name(vm) != hypervisor:
				continue

			# Handle if no disks are defined for a
			# virtual machine
			if vm not in vm_disks:
				curr_disks = []
			else:
				curr_disks = vm_disks[vm]
			guestxml = self.buildGuestXML(vm, vm_info[vm], curr_disks)
			if not bare_output:
				if len(vm_hosts) > 1:
					self.addOutput(vm, f'<stack:file stack:name=/etc/libvirt/qemu/{vm}.xml>')
				else:
					self.addOutput('', f'<stack:file stack:name=/etc/libvirt/qemu/{vm}.xml>')
				self.addOutput('', guestxml)
				self.addOutput('', '</stack:file>')
			else:
				self.addOutput(vm, guestxml)
		self.endOutput(padChar='', trimOwner=True)
