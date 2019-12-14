import pytest
import json

class TestSyncVM:
	"""
	Tests for sync vm
	"""

	BAD_SYNC_VM_INPUT = [
	'fake-backend-0-0',
	'backend-0-0',
	'hypervisor=backend-0-0'
	]
	@pytest.mark.parametrize('params', BAD_SYNC_VM_INPUT)
	def test_invalid_parameters(self, add_hypervisor, add_vm_multiple, add_host, host, params):
		result = host.run(f'stack sync vm {params}')
		assert result.rc != 0

	# Test VM's marked for deletion
	# aren't removed without using force
	def test_remove_after_sync(self, add_hypervisor, add_vm_multiple, host):
		remove_host = host.run(f'stack remove vm vm-backend-0-4')
		assert remove_host.rc == 0

		sync_host = host.run('stack sync vm')
		assert sync_host.rc == 0

		list_host = host.run('stack list vm hypervisor=hypervisor-0-1 output-format=json')
		assert list_host.rc == 0

		assert json.loads(list_host.stdout) == [
			{
				'virtual machine': 'vm-backend-0-3',
				'hypervisor': 'hypervisor-0-1',
				'memory': 2048,
				'cpu': 1,
				'pending deletion': False,
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

	# Test with the force parameter
	# if VM's marked for deletion
	# are removed after running sync
	# even though the hypervisor
	# can't be reached
	def test_remove_after_sync_force(self, add_hypervisor, add_vm_multiple, host):
		remove_host = host.run(f'stack remove vm vm-backend-0-4')
		assert remove_host.rc == 0

		sync_host = host.run('stack sync vm force=y')
		assert sync_host.rc == 0

		list_host = host.run('stack list vm hypervisor=hypervisor-0-1 output-format=json')
		assert list_host.rc == 0

		assert json.loads(list_host.stdout) == [{
			'virtual machine': 'vm-backend-0-3',
			'hypervisor': 'hypervisor-0-1',
			'memory': 2048,
			'cpu': 1,
			'pending deletion': False,
			'status': 'Connection failed to hypervisor'
		}]

	# Test syncing per hypervisor
	def test_sync_hypervisor(self, add_hypervisor, add_vm_multiple, host):

		# We mark two hosts for deletion but
		# only sync hypervisor-0-2, so only
		# vm-backend-0-6 should be removed
		remove_host = host.run(f'stack remove vm vm-backend-0-4')
		assert remove_host.rc == 0

		remove_host = host.run(f'stack remove vm vm-backend-0-6')
		assert remove_host.rc == 0

		# Since there is no live hypervisor
		# connection, force is needed here
		sync_host = host.run('stack sync vm hypervisor=hypervisor-0-2 force=y')
		assert sync_host.rc == 0

		list_host = host.run('stack list vm output-format=json')
		assert list_host.rc == 0

		assert json.loads(list_host.stdout) == [
			{
				'virtual machine': 'vm-backend-0-3',
				'hypervisor': 'hypervisor-0-1',
				'memory': 2048,
				'cpu': 1,
				'pending deletion': False,
				'status': 'Connection failed to hypervisor'
			},
			{
				'virtual machine': 'vm-backend-0-4',
				'hypervisor': 'hypervisor-0-1',
				'memory': 2048,
				'cpu': 2,
				'pending deletion': True,
				'status': 'Connection failed to hypervisor'
			},
			{
				'virtual machine': 'vm-backend-0-5',
				'hypervisor': 'hypervisor-0-2',
				'memory': 3072,
				'cpu': 3,
				'pending deletion': False,
				'status': 'Connection failed to hypervisor'
			}
		]
