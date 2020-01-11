import stack.commands
from stack.exception import CommandError
from stack.argument_processors.repo import RepoArgumentProcessor

class Command(stack.commands.PalletArgumentProcessor, RepoArgumentProcessor,
	stack.commands.add.command):
	"""
	Add a remote software repository to stacki.

	<arg type='string' name='repo'>
	The name of the repo.
	</arg>

	<param type='string' name='alias' optional='1'>
	An alias for the repository.  This must be a string with no spaces.
	If not provided, the 'name' of the repo will be used, replacing
	spaces with hypens.
	</param>

	<param type='string' name='url' optional='1'>
	The URL of the repository.  This can be a remote URL or a URL pointing
	to the stacki frontend's webserver.  Attributes can be used inside this
	string as jinja variables.  For example,
	'http://{{ Kickstart_PrivateAddress }}/some/path/'
	</param>

	<example cmd='add repo coolstuff url=http://{{ Kickstart_PrivateAddress }}/install/random_path/sles12/sles/x86_64'>
	Add a 'coolstuff' repository to stacki.  '{{ Kickstart_PrivateAddress }}'
	will be replaced with that attribute
	</example>

	<example cmd='add repo ceph_pkgs url=http://192.168.0.2/install/pallets/ceph/5.4.2/sles12/sles/x86_64'>
	Add a 'ceph_pkgs' repository to stacki
	</example>

	<example cmd='add repo EPEL url=http://dl.fedoraproject.org/pub/epel'>
	Add the EPEL repository to stacki
	</example>
	"""

	def run(self, params, args):
		if len(args) != 1:
			raise CommandError(self, 'only one repo may be specified at a time')

		alias, url, = self.fillParams([
			('alias', None),
			('url', None, True),
		])

		repo_data = []
		for repo_name in args:
			if not alias:
				alias = repo_name.replace(' ', '-')

			repo_data.append({
				'name': repo_name,
				'alias': alias,
				'uri': url,
			})

		for repo in repo_data:
			self.insert_repo(**repo)
