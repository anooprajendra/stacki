import pytest
import json
from pathlib import Path

class TestAddVM:
	"""
	Tests for adding a new virtual machine
	to Stacki
	"""

	STOR_POOL = '/export/pools/stacki'

	def test_add_vm(self, add_hypervisor, host):

		# The host must be added to the database before adding as a VM
		add_host = host.run(f'stack add host vm-backend-0-3 appliance=backend rank=0 rack=1')
		assert add_host.rc == 0
		params = f'hypervisor=hypervisor-0-1 storage_directory={self.STOR_POOL} memory=4096 cpu=4 disks=100'
		add_result = host.run(f'stack add vm vm-backend-0-3 {params}')
		assert add_result.rc == 0

		# Make sure it matches the expected values
		list_result = host.run(f'stack list vm output-format=json')
		assert list_result.rc == 0

		assert json.loads(list_result.stdout) == [{
			'virtual machine': 'vm-backend-0-3',
			'hypervisor': 'hypervisor-0-1',
			'memory': 4096,
			'cpu': 4,
			'pending deletion': False,
			'status': 'Connection failed to hypervisor'
		}]

	def test_add_vm_minimal(self, add_hypervisor, host):

		# The host must be added to the database before adding as a VM
		add_host = host.run(f'stack add host vm-backend-0-3 appliance=backend rank=0 rack=1')
		assert add_host.rc == 0
		cmd = f'stack add vm vm-backend-0-3 hypervisor=hypervisor-0-1 storage_directory={self.STOR_POOL}'
		add_result = host.run(cmd)
		assert add_result.rc == 0

		# Make sure it matches the expected values
		list_result = host.run(f'stack list vm output-format=json')
		assert list_result.rc == 0

		assert json.loads(list_result.stdout) == [{
			'virtual machine': 'vm-backend-0-3',
			'hypervisor': 'hypervisor-0-1',
			'memory': 3072,
			'cpu': 1,
			'pending deletion': False,
			'status': "Connection failed to hypervisor"
		}]

	ADD_VM_BAD_DATA = [
	('', ''),
	('virtual-backend-0-3', ''),
	('virtual-backend-0-3', f'hypervisor=backend-0-0 storage_directory={STOR_POOL}'),
	('virtual-backend-0-3', f'hypervisor=fake-host-0-0 storage_directory={STOR_POOL}'),
	('virtual-backend-0-3', f'storage_directory={STOR_POOL}'),
	('virtual-backend-0-3', f'hypervisor=hypervisor-0-1 cpu=2 memory=3072'),
	('virtual-backend-0-3', f'hypervisor=hypervisor-0-1 cpu=2 memory=3072 storage_directory='),
	('virtual-backend-0-3', f'hypervisor=hypervisor-0-1 cpu=a storage_directory={STOR_POOL}'),
	('virtual-backend-0-3', f'hypervisor=hypervisor-0-1 memory=a storage_directory={STOR_POOL}'),
	('virtual-backend-0-3', f'hypervisor=hypervisor-0-1 memory= storage_directory={STOR_POOL}'),
	('virtual-backend-0-3', f'hypervisor=hypervisor-0-1 cpu= storage_directory={STOR_POOL}'),
	('virtual-backend-0-3', f'hypervisor=hypervisor-0-1 cpu=-1 storage_directory={STOR_POOL}'),
	('virtual-backend-0-3', f'hypervisor=hypervisor-0-1 memory=-1 storage_directory={STOR_POOL}')
	]

	@pytest.mark.parametrize('host_name, params', ADD_VM_BAD_DATA)
	def test_add_vm_bad(self, add_hypervisor, host, host_name, params):

		# The host must be added to the database before adding as a VM
		if host_name:
			add_host = host.run(f'stack add host {host_name} appliance=backend rank=0 rack=3')
			assert add_host.rc == 0

		add_result = host.run(f'stack add vm {host_name} {params}')
		assert add_result.rc != 0
