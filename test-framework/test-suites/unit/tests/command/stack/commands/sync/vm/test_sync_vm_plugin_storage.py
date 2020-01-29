import pytest
from unittest.mock import create_autospec, patch, call, ANY
from stack.commands import DatabaseConnection
from stack.commands.sync.vm.plugin_storage import Plugin, VmException
from stack.commands.sync.vm import Command
from stack.bool import str2bool
from pathlib import Path

class TestSyncVmStorage:
	def mock_vm_exception(self, *args):
		raise VmException('Oh no something went wrong!')

	def mock_os_error(self, *args):
		raise OSError('Oh no something went wrong!')

	@pytest.fixture
	def mock_sync_storage_plugin(self):
		"""
		A fixture for mocking Plugin instances
		"""

		mock_command = create_autospec(
			spec = Command,
			instance = True
		)

		mock_command.db = create_autospec(
			spec = DatabaseConnection,
			spec_set = True,
			instance = True
		)

		return Plugin(mock_command)

	ADD_DISK_ARGS = [
		(
			'foo',
			'hypervisor-foo',
			{
				'Name': 'disk1',
				'Type': 'disk',
				'Image Name': 'disk_name',
				'Location': 'loc',
				'Pending Deletion': 'False',
				'Size': 100
			},
			True
		),
		(
			'bar', 'hypervisor-bar',
			{
				'Name': 'disk1',
				'Type': 'image',
				'Image Name': 'disk_name',
				'Image Archive': 'disk.tar.gz',
				'Location': 'loc',
				'Pending Deletion': 'False'
			},
			True
		),
		(
			'baz',
			'hypervisor-baz',
			{
				'Name': 'disk1',
				'Type': 'image',
				'Image Name': 'disk.qcow2',
				'Image Archive': '',
				'Location': 'loc',
				'Pending Deletion': 'False'
			},
			True
		)
	]
	@patch.object(Plugin, 'pack_ssh_key', autospec=True)
	@patch('stack.commands.sync.vm.plugin_storage.Hypervisor', autospec=True)
	@patch('stack.commands.sync.vm.plugin_storage.copy_remote_file', autospec=True)
	@pytest.mark.parametrize('host, hypervisor_name, disk, sync_ssh', ADD_DISK_ARGS)
	def test_sync_storage_plugin_add_disk(
		self,
		mock_copy_file,
		mock_hypervisor,
		mock_pack_ssh,
		mock_sync_storage_plugin,
		host,
		hypervisor_name,
		disk,
		sync_ssh
	):
		hypervisor = mock_hypervisor.return_value
		hypervisor.add_pool.return_value = True
		mock_pack_ssh.return_value = []
		disk_location = Path(disk['Location'])
		image_name = Path(disk['Image Name']).name
		output = mock_sync_storage_plugin.add_disk(
			host,
			hypervisor_name,
			disk,
			sync_ssh,
			True
		)
		if disk['Type'] == 'disk':
			hypervisor.add_pool.assert_called_once_with(
				disk_location.name,
				disk_location
			)
			hypervisor.add_volume.assert_called_once_with(
				disk['Image Name'],
				disk_location,
				disk_location.name,
				disk['Size']
			)
			mock_pack_ssh.assert_not_called()
		elif disk['Type'] == 'image':
			if disk.get('Image Archive'):
				copy_file = disk['Image Archive']
			else:
				copy_file = disk['Image Name']

			mock_copy_file.assert_called_once_with(
				copy_file,
				disk_location,
				image_name,
				hypervisor_name
			)
			if sync_ssh:
				mock_pack_ssh.assert_called_once_with(ANY, host, hypervisor_name, disk)

		assert output == []


	@patch('stack.commands.sync.vm.plugin_storage.Hypervisor', autospec=True)
	def test_sync_storage_plugin_add_disk_vm_except(
		self,
		mock_hypervisor,
		mock_sync_storage_plugin
	):
		hypervisor = mock_hypervisor.return_value
		hypervisor.add_pool.side_effect = self.mock_vm_exception
		disk = {
				'Name': 'disk1',
				'Type': 'disk',
				'Image Name': 'disk_name',
				'Location': 'loc',
				'Pending Deletion': 'False',
				'Size': 100
		}
		output = mock_sync_storage_plugin.add_disk('foo', 'hypervisor-foo', disk, True, True)
		assert output == ['Oh no something went wrong!']

	@patch.object(Plugin, 'pack_ssh_key', autospec=True)
	@patch('stack.commands.sync.vm.plugin_storage.copy_remote_file', autospec=True)
	def test_sync_storage_plugin_add_disk_copy_file_except(
		self,
		mock_copy_remote_file,
		mock_pack_ssh_key,
		mock_sync_storage_plugin
	):
		mock_copy_remote_file.side_effect = self.mock_os_error
		mock_pack_ssh_key.return_value = 'Key could not be copied'
		disk = {
				'Name': 'disk1',
				'Type': 'image',
				'Image Name': 'disk.qcow2',
				'Image Archive': '',
				'Location': 'loc',
				'Pending Deletion': 'False',
				'Size': ''
		}
		output = mock_sync_storage_plugin.add_disk('foo', 'hypervisor-foo', disk, True, True)
		assert output == [
				'Oh no something went wrong!',
				'Failed to pack frontend ssh key: Key could not be copied'
		]

	REMOVE_DISK_ARGS = [
		(
			'hypervisor-foo',
			{
				'Name': 'disk1',
				'Type': 'disk',
				'Image Name': 'disk_name',
				'Location': 'loc',
				'Pending Deletion': 'True',
				'Size': 100
			}
		),
		(
			'hypervisor-baz',
			{
				'Name': 'disk1',
				'Type': 'image',
				'Image Name': 'disk.qcow2',
				'Image Archive': '',
				'Location': 'loc',
				'Pending Deletion': 'True'
			}
		)
	]
	@patch('stack.commands.sync.vm.plugin_storage.Hypervisor', autospec=True)
	@patch('stack.commands.sync.vm.plugin_storage.remove_remote_file', autospec=True)
	@pytest.mark.parametrize('hypervisor_name, disk', REMOVE_DISK_ARGS)
	def test_sync_storage_plugin_remove_disk(
		self,
		mock_remove_remote_file,
		mock_hypervisor,
		mock_sync_storage_plugin,
		hypervisor_name,
		disk
	):
		hypervisor = mock_hypervisor.return_value
		output = mock_sync_storage_plugin.remove_disk(hypervisor_name, disk, True)

		if disk['Type'] == 'disk':
			hypervisor.remove_volume.assert_called_once_with(disk['Location'], disk['Image Name'])
		elif disk['Type'] == 'image':
			file_loc = f'{disk["Location"]}/{disk["Image Name"]}'
			mock_remove_remote_file.assert_called_once_with(file_loc, hypervisor_name)
		assert output == []

	@patch('stack.commands.sync.vm.plugin_storage.Hypervisor', autospec=True)
	def test_sync_storage_plugin_remove_disk_vm_except(
		self,
		mock_hypervisor,
		mock_sync_storage_plugin
	):
		hypervisor = mock_hypervisor.return_value
		hypervisor.remove_volume.side_effect = self.mock_vm_exception
		disk = {
				'Name': 'disk1',
				'Type': 'disk',
				'Image Name': 'disk_name',
				'Location': 'loc',
				'Pending Deletion': 'False',
				'Size': 100
		}
		output = mock_sync_storage_plugin.remove_disk('hypervisor-foo', disk, True)
		assert output == ['Oh no something went wrong!']

	@patch('stack.commands.sync.vm.plugin_storage.remove_remote_file', autospec=True)
	def test_sync_storage_plugin_remove_disk_remove_file_except(
		self,
		mock_remove_remote_file,
		mock_sync_storage_plugin
	):
		mock_remove_remote_file.side_effect = self.mock_os_error
		disk = {
				'Name': 'disk1',
				'Type': 'image',
				'Image Name': 'disk.qcow2',
				'Image Archive': '',
				'Location': 'loc',
				'Pending Deletion': 'False',
				'Size': ''
		}
		output = mock_sync_storage_plugin.remove_disk('hypervisor-foo', disk, True)
		assert output == ['Oh no something went wrong!']

	RUN_ARGS = [
		(
			{
				'foo': {
					'hypervisor': 'hypervisor-foo'
				}
			},
			{
				'foo': [
					{
						'Name': 'disk1',
						'Type': 'disk',
						'Image Name': 'disk_name',
						'Location': 'loc',
						'Pending Deletion': 'True',
						'Size': 100
					}
				]
			},
			'hypervisor-foo'
		),
		(
			{
				'foo': {
					'hypervisor': 'hypervisor-foo'
				},
				'bar': {
					'hypervisor': 'hypervisor-bar'
				},
				'baz': {
					'hypervisor': 'hypervisor-baz'
				},
			},
			{
				'foo': [
					{
						'Name': 'disk1',
						'Type': 'disk',
						'Image Name': 'disk_name',
						'Location': 'loc',
						'Pending Deletion': 'True',
						'Size': 100
					}
				],
				'bar': [
					{
						'Name': 'disk1',
						'Type': 'image',
						'Image Name': 'disk_name.qcow2',
						'Image Archive': '',
						'Location': 'loc',
						'Pending Deletion': 'False',
						'Size': ''
					}
				],
				'baz': [
					{
						'Name': 'disk1',
						'Type': 'disk',
						'Image Name': 'disk_name',
						'Location': 'loc',
						'Pending Deletion': 'False',
						'Size': 100
					},
					{
						'Name': 'disk1',
						'Type': 'image',
						'Image Name': 'disk_name.raw',
						'Image Archive': 'disk.tar.gz',
						'Location': 'loc',
						'Pending Deletion': 'True',
						'Size': ''
					}
				]
			},
			'hypervisor-foo'
		)
	]
	@patch.object(Plugin, 'add_disk', autospec=True)
	@patch.object(Plugin, 'remove_disk', autospec=True)
	@pytest.mark.parametrize('hosts, host_disks, hypervisor', RUN_ARGS)
	def test_sync_storage_plugin_run(
		self,
		mock_remove_disk,
		mock_add_disk,
		mock_sync_storage_plugin,
		hosts,
		host_disks,
		hypervisor
	):
		add_disks = {}
		delete_disks = {}
		mock_remove_disk.return_value = ['remove_disk errors!']
		mock_add_disk.return_value = ['add_disk errors!']
		expect_output = []
		for host, disks in host_disks.items():
			for disk in disks:
				host_hypervisor = hosts[host]['hypervisor']
				if str2bool(disk['Pending Deletion']):
					delete_disks[host_hypervisor] = disk
				else:
					add_disks[host] = (host_hypervisor, disk)
		mock_sync_storage_plugin.owner.str2bool.side_effect = str2bool
		output = mock_sync_storage_plugin.run((hosts, host_disks, True, True, False, hypervisor))
		for hypervisor_name, disk in delete_disks.items():
			mock_remove_disk.assert_any_call(ANY, hypervisor_name, disk,True)
			expect_output.append('remove_disk errors!')
		for host, info in add_disks.items():
			mock_add_disk.assert_any_call(ANY, host, info[0], info[1], sync_ssh = True, debug = True)
			expect_output.append('add_disk errors!')
		assert sorted(output) == sorted(expect_output)
