import stack.commands
from stack.exception import CommandError
from stack.argument_processors.repo import RepoArgumentProcessor

class Command(RepoArgumentProcessor, stack.commands.remove.command):
	"""
	Remove remote software repositories from stacki.

	<arg type='string' name='repo'>
	A list of repo's to remove.  This can be the repo name or alias.
	</arg>

	<param type='string' name='url' optional='1'>
	The URL of the repository.  This can be a remote URL or a URL pointing
	to the stacki frontend's webserver.
	</param>

	<example cmd='remove repo ceph_pkgs'>
	Remove the 'ceph_pkgs' repository from stacki
	</example>

	<example cmd='remove repo url=http://dl.fedoraproject.org/pub/epel'>
	Remvoe the EPEL repo from stacki
	</example>
	"""

	def run(self, params, args):
		url, = self.fillParams([
			('url', None),
		])

		if not args:
			raise CommandError(self, 'either a repo name or alias must be specified.')

		#TODO remove by url
		for repo in self.get_repos():
			self.delete_repo(repo.alias)
