from operator import attrgetter

import stack.commands
from stack.exception import CommandError
from stack.argument_processors.repo import RepoArgumentProcessor

class Command(stack.commands.PalletArgumentProcessor, RepoArgumentProcessor,
	stack.commands.remove.command):
	"""
	Remove a software repository from stacki.

	You can specify a repo by specifying metadata describing it, or if
	it is contained inside a pallet already added to stacki, by
	specifying the pallet.  If you specify a pallet, all repos inside
	that pallet will be removed.

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
	to the stacki frontend's webserver.
	</param>

	<param type='string' name='pallet' optional='1'>
	The name of the pallet (which must already added to stacki) to remove
	related repos from. This should be the pallet base name (e.g., stacki,
	boss, os).
	</param>

	<param type='string' name='version' optional='1'>
	The version number of the pallet to remove related repos from. If no
	version number is supplied, then all versions of a pallet will used.
	</param>

	<param type='string' name='release' optional='1'>
	The release number of the pallet to remove related repos from. If no
	release number is supplied, then all releases of a pallet will be
	searched for repo's.
	</param>

	<param type='string' name='arch' optional='1'>
	The architecture of the pallet to remove related repos from. The
	default value is native architecture of the host.
	</param>

	<param type='string' name='os' optional='1'>
	The OS of the pallet to remove related repos from. If no OS is
	supplied, then all OS versions of a pallet will be searched for repo's.
	</param>

	<example cmd='remove repo ceph_pkgs url=http://192.168.0.2/install/pallets/ceph/5.4.2/sles12/sles/x86_64'>
	Remove the 'ceph_pkgs' repository from stacki
	</example>

	<example cmd='remove repo EPEL url=http://dl.fedoraproject.org/pub/epel'>
	Remvoe the EPEL repo from stacki
	</example>
	"""

	def run(self, params, args):
		alias, url, pallet, version, release, arch, os = self.fillParams([
			('alias', None),
			('url', None),
			('pallet', None),
			('version', None),
			('release', None),
			('arch', self.arch),
			('os', self.os),
		])

		if not args and pallet is None:
			raise CommandError(self, 'either a repo argument or pallet parameter must be specified.')

		repo_args = args
		db_repos = self.get_repos()

		# since it's reasonable to use a name or an alias, we'll figure out what they meant
		db_repo_names = {attrgetter('name')(a) for a in db_repos}
		db_repo_aliases = dict(attrgetter('alias', 'name')(a) for a in db_repos)

		bad_repos = []
		for i, repo in enumerate(repo_args):
			if repo in db_repo_names:
				pass
			elif repo in db_repo_aliases:
				repo_args[i] = db_repo_aliases[repo]
			else:
				bad_repos.append(repo)

		if bad_repos:
			msg = 'The following arguments do not appear to be known repos: '
			raise CommandError(self, msg + ', '.join(bad_repos))

		if not repo_args:
			# TODO user tried to specify a pallet...
			pass

		for repo in repo_args:
			self.delete_repo(repo)
