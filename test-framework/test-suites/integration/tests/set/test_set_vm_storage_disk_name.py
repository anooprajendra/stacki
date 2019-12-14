import json
import pytest
from collections import namedtuple

class TestSetVmStorageName:
	def test_no_vm(self, host):
		result = host.run('stack set vm storage name')
		assert result.rc != 0

	def test_no_parameters(self, add_hypervisor, add_vm, host):
		result = host.run('stack set vm storage name vm-backend-0-3')
		assert result.rc != 0

	Disk = namedtuple('disk', 'backing name')
	INVALID_PARAMS = [
		Disk('', ''),
		Disk('fake_disk.qcow2', 'sda'),
		Disk('image.qcow2', 'sda')
	]

	@pytest.mark.parametrize('params', INVALID_PARAMS)
	def test_invalid_parameters(self, add_hypervisor, add_vm, host, params):
		result = host.run(f'stack set vm storage name vm-backend-0-3 backing={params.backing} name={params.name}')
		assert result.rc != 0

	def test_invalid_vm(self, host):
		result = host.run('stack set vm memory fake-backend-0-0 backing=images.qcow2 name=sda')
		assert result.rc != 0

	def test_single_host(self, add_hypervisor, add_vm_multiple, host):
		result = host.run('stack set vm storage name vm-backend-0-3 backing=vm-backend-0-3_disk1.qcow2 name=sdb')
		assert result.rc == 0

		# Check that it made it into the database
		result = host.run('stack list vm storage vm-backend-0-3 output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [{
			'Virtual Machine': 'vm-backend-0-3',
			'Name': 'sdb',
			'Type': 'disk',
			'Location': '/export/pools/stacki',
			'Size': 100,
			'Image Name': 'vm-backend-0-3_disk1.qcow2',
			'Image Archive': None,
			'Mountpoint': None,
			'Pending Deletion': False
		}]

	def test_disk_swap(self, add_hypervisor, add_vm_multiple, host):

		# Set the first disk to blank to allow the disks to be swapped
		# if a new disk name is already set, the disk cannot be swapped
		result = host.run('stack set vm storage name vm-backend-0-4 backing=vm-backend-0-4_disk1.qcow2 name=')
		assert result.rc == 0

		result = host.run('stack set vm storage name vm-backend-0-4 backing=vm-backend-0-4_disk2.qcow2 name=sda')
		assert result.rc == 0

		result = host.run('stack set vm storage name vm-backend-0-4 backing=vm-backend-0-4_disk1.qcow2 name=sdb')
		assert result.rc == 0

		# Check that it made it into the database
		result = host.run('stack list vm storage vm-backend-0-4 output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'Virtual Machine': 'vm-backend-0-4',
				'Name': 'sdb',
				'Type': 'disk',
				'Location': '/export/pools/stacki',
				'Size': 200,
				'Image Name': 'vm-backend-0-4_disk1.qcow2',
				'Image Archive': None,
				'Mountpoint': None,
				'Pending Deletion': False
			},
			{
				'Virtual Machine': 'vm-backend-0-4',
				'Name': 'sda',
				'Type': 'disk',
				'Location': '/export/pools/stacki',
				'Size': 100,
				'Image Name': 'vm-backend-0-4_disk2.qcow2',
				'Image Archive': None,
				'Mountpoint': None,
				'Pending Deletion': False
			}
		]
