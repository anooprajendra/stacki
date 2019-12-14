import json
import pytest
from tempfile import TemporaryDirectory

class TestRemoveVM:
	def test_no_vm(self, host):
		result = host.run('stack remove vm')
		assert result.rc != 0

	def test_invalid_vm(self, host):
		result = host.run('stack remove vm fake-backend-0-0')
		assert result.rc != 0

	def test_single_host(self, add_hypervisor, add_vm, host):
		result = host.run('stack remove vm vm-backend-0-3')
		assert result.rc == 0

		# Check that it made it into the database
		result = host.run('stack list vm vm-backend-0-3 output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [{
			'virtual machine': 'vm-backend-0-3',
			'hypervisor': 'hypervisor-0-1',
			'memory': 2048,
			'cpu': 1,
			'pending deletion': True,
			'status': 'Connection failed to hypervisor'
		}]

	def test_multiple_hosts(self, add_hypervisor, add_vm_multiple, host):
		result = host.run('stack remove vm vm-backend-0-3 vm-backend-0-4')
		assert result.rc == 0

		# Check that it made it into the database
		result = host.run('stack list vm vm-backend-0-3 vm-backend-0-4 output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'virtual machine': 'vm-backend-0-3',
				'hypervisor': 'hypervisor-0-1',
				'memory': 2048,
				'cpu': 1,
				'pending deletion': True,
				'status': 'Connection failed to hypervisor'
			},
			{
				'virtual machine': 'vm-backend-0-4',
				'hypervisor': 'hypervisor-0-1',
				'memory': 2048,
				'cpu': 2,
				'pending deletion': True,
				'status': 'Connection failed to hypervisor'
			}
		]

	def test_nukedisks(self, add_hypervisor, add_vm_multiple, add_vm_storage, host, create_image_files, test_file):
		tmp_dir = TemporaryDirectory()
		images = create_image_files(tmp_dir)
		add_vm_storage(images, 'vm-backend-0-3')

		result = host.run('stack remove vm vm-backend-0-3 nukedisks=y')
		assert result.rc == 0

		# Check that it made it into the database
		result = host.run('stack list vm storage vm-backend-0-3 output-format=json')
		assert result.rc == 0

		# Make sure every disk is marked
		# for deletion
		for disk in json.loads(result.stdout):
			assert disk['Pending Deletion']
