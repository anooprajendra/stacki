import stack.commands
from stack.exception import CommandError
from stack.argument_processors.repo import RepoArgumentProcessor

class Command(stack.commands.PalletArgumentProcessor, RepoArgumentProcessor,
	stack.commands.add.command):
	"""
	Add a software repository to stacki.

	You can specify a repo by specifying metadata describing it, or if
	it is contained inside a pallet already added to stacki, by
	specifying the pallet.  If you specify a pallet, all repos inside
	that pallet will be added.

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
	The name of the pallet (which must already added to stacki) to add repos
	from. This should be the pallet base name (e.g., stacki, boss, os).
	</param>

	<param type='string' name='version' optional='1'>
	The version number of the pallet to add repos from. If no version number
	is supplied, then all versions of a pallet will be searched for repo's.
	</param>

	<param type='string' name='release' optional='1'>
	The release number of the pallet to add repos from. If no release number
	is supplied, then all releases of a pallet will be searched for repo's.
	</param>

	<param type='string' name='arch' optional='1'>
	The architecture of the pallet to add repos from. The default value is
	native architecture of the host.
	</param>

	<param type='string' name='os' optional='1'>
	The OS of the pallet to add repos from. If no OS is supplied, then all OS
	versions of a pallet will be enabled.
	</param>

	<example cmd='add repo ceph_pkgs url=http://192.168.0.2/install/pallets/ceph/5.4.2/sles12/sles/x86_64'>
	Add a 'ceph_pkgs' repository to stacki
	</example>

	<example cmd='add repo EPEL url=http://dl.fedoraproject.org/pub/epel'>
	Add the EPEL repository to stacki
	</example>
	"""

	def run(self, params, args):
		if len(args) > 1:
			raise CommandError(self, 'only one repo may be specified at a time')

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

		repo_data = []
		if args:
			repo_name = args[0]
			if not url:
				raise CommandError(self, 'a URL must be specified when adding a repo')

			if not alias:
				alias = repo_name.replace(' ', '-')

			repo_data.append({
				'name': repo_name,
				'alias': alias,
				'url': url,
			})

		# user tried to specify a pallet?
		if not args:
			params = {}
			params['version'] = version
			params['release'] = release
			params['arch'] = arch
			params['os'] = os
			params = {k: v for k, v in params.items() if v is not None}

			pallets = self.getPallets([pallet], params)

			pallet_ids = [pal.id for pal in pallets]
			# TODO, probe pallets on disk for repositories

			pallet_web_path = 'http://{{ fe_ip }}/install/pallets/'
			for pal in pallets:
				name = f'{pal.name} {pal.version} {pal.rel}'
				path = '/'.join([pal.name, pal.version, pal.rel, pal.os, pal.arch])
				repo_data.append({
					'name': name,
					'alias': name.replace(' ', '-'),
					'uri': pallet_web_path + path,
					'pallet_id': pal.id,
				})

		for repo in repo_data:
			self.insert_repo(**repo)
