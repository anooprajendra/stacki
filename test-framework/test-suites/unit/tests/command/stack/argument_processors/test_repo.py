from unittest.mock import create_autospec, ANY
import pytest

from operator import itemgetter
import pathlib

from stack.argument_processors.repo import RepoArgumentProcessor
from stack.commands import DatabaseConnection

FAKE_REPO_DATA = {
	'name': 'fakename',
	'alias': 'fakealias',
	'uri': 'uri:///',
	'autorefresh': 0,
	'assumeyes': 0,
	'type': 'rpm-md',
	'is_mirrorlist': 0,
	'gpgcheck': 0,
	'gpgkey': '',
	'os': 'sles',
	'pallet_id': None,
	'is_enabled': '1'
}

FAKE_REPO_FILE = '''[fakealias]
name=fakename
baseurl=uri:///
enabled=1
type=rpm-md
gpgcheck=0'''

REPO_NON_REQUIRED_ARGS = [
	{'is_mirrorlist': 1},
	{'EXTRA_IGNORED': 'KWARG'},
	{'is_mirrorlist': 1, 'EXTRA_IGNORED': 'KWARG'},
	{'autorefresh': '1'},
	{'type': 'yast'},
]

class TestRepoArgumentProcessor:
	@pytest.fixture
	def argument_processor(self):
		test_arg_processor = RepoArgumentProcessor()
		test_arg_processor.db = create_autospec(DatabaseConnection, instance=True)
		return test_arg_processor

	def test_get_repos_by_box(self, argument_processor):
		fakebox_name = 'fakebox'
		fakebox_id = 0
		argument_processor.db.select.side_effect = [
			[[fakebox_id]],
			[list(FAKE_REPO_DATA.values())[0:-1]]
		]
		assert {fakebox_name: {FAKE_REPO_DATA['name']: FAKE_REPO_DATA}} == argument_processor.get_repos_by_box(fakebox_name)
		argument_processor.db.select.assert_called_with(ANY, (fakebox_id,))

	def test_insert_repo(self, argument_processor):
		basic_repo_data = itemgetter('name', 'alias', 'uri')(FAKE_REPO_DATA)
		argument_processor.insert_repo(*basic_repo_data)
		argument_processor.db.execute.assert_called_with(ANY, basic_repo_data)

	@pytest.mark.parametrize("kwargs", REPO_NON_REQUIRED_ARGS)
	def test_insert_repo_optional_args(self, argument_processor, kwargs):
		''' many columns in the repos table are optional - the arg proc should ignore invalid columns '''
		basic_repo_data = itemgetter('name', 'alias', 'uri')(FAKE_REPO_DATA)
		argument_processor.insert_repo(*basic_repo_data, **kwargs)

		expected_vals = []
		for key in argument_processor.OPTIONAL_REPO_COLUMNS:
			if key in kwargs:
				expected_vals.append(kwargs[key])

		argument_processor.db.execute.assert_called_with(ANY, (basic_repo_data + tuple(expected_vals)))

	def test_build_repo_files(self, argument_processor):
		templ = pathlib.Path('/opt/stack/share/templates/yum_repo.j2').read_text()
		print(FAKE_REPO_DATA)
		repo_stanzas = argument_processor.build_repo_files({'fakebox': FAKE_REPO_DATA}, templ)

		assert '\n'.join(repo_stanzas) == FAKE_REPO_FILE
