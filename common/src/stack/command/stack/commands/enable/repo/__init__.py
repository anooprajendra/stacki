from operator import attrgetter

import stack.commands
from stack.exception import CommandError
from stack.argument_processors.repo import RepoArgumentProcessor

class Command(stack.commands.enable.command, RepoArgumentProcessor,
	stack.commands.BoxArgumentProcessor):
	"""
	Enable a software repository for a stacki box

	<arg type='string' name='repo'>
	A list of repos to enable.  This should be the repo's name or alias.
	</arg>

	<param type='string' name='pallet' optional='1'>
	The name of the pallet (which must already added to stacki) to enable
	repos from. This should be the pallet base name (e.g., stacki, boss, os).
	</param>

	<param type='string' name='version' optional='1'>
	The version number of the pallet to be enabled. If no version number is
	supplied, then all versions of a pallet will be searched for repo's.
	</param>

	<param type='string' name='release' optional='1'>
	The release number of the pallet to be enabled. If no release number is
	supplied, then all releases of a pallet will be searched for repo's.
	</param>

	<param type='string' name='arch' optional='1'>
	If specified enables the pallet for the given architecture.  The default
	value is the native architecture of the host.
	</param>

	<param type='string' name='os' optional='1'>
	The OS of the pallet to be enabled. If no OS is supplied, then all OS
	versions of a pallet will be enabled.
	</param>

	<param type='string' name='box'>
	The name of the box in which to enable the repo(s). If no
	box is specified the repo is enabled for the default box.
	</param>

	<example cmd='enable repo ceph_pkgs'>
	Enable a 'ceph_pkgs' repository for the default box
	</example>

	<example cmd='enable repo EPEL os-updates-20200123 box=frontend'>
	Enable the EPEL and os-updates-20200123 repositories on the frontend box
	</example>
	"""

	def run(self, params, args):
# TODO arg handling
#		if not args and pallet is None:
#			raise CommandError(self, 'either a repo argument or pallet parameter must be specified.')

		# user tried to specify a pallet?
#		if not args:
#			params = {}
#			params['version'] = version
#			params['release'] = release
#			params['arch'] = arch
#			params['os'] = os
#			params = {(k, v) for k, v in params.items() if v is not None}
#
#			pallets = self.getPallets(pallet, params)
#
#			pallet_ids = [pal.id for pal in pallets]
#			# TODO, probe pallets on disk for repositories
#
#			pallet_web_path = 'http://{{ fe_ip }}/install/pallets/'
#			for pal in pallets:
#				name = f'{pallet.name} {pallet.version} {pallet.release}'
#				path = '/'.join([pallet.name, pallet.version, pallet.release, pallet.os, pallet.arch])
#				repo_data.append({
#					'name': name,
#					'alias': name.replace(' ', '-'),
#					'url': pallet_web_path + path,
#				})

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

		box, pallet, version, release, arch, os = self.fillParams([
			('box', 'default'),
			('pallet', None),
			('version', None),
			('release', None),
			('arch', self.arch),
			('os', self.os),
			])

		if box not in self.getBoxNames():
			raise CommandError(self, f'box "{box}" not found')

		for repo in repo_args:
			self.enable_repo(repo, box)
