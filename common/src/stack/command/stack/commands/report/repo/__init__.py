import stack.commands
from stack.argument_processors.repo import RepoArgumentProcessor

class Command(stack.commands.report.command, stack.commands.HostArgumentProcessor,
	stack.commands.BoxArgumentProcessor, RepoArgumentProcessor):
	"""
	Create a report that describes the repository configuration file
	that should be put on hosts.

	<arg optional='0' type='string' name='host'>
	Host name of machine
	</arg>

	<example cmd='report host repo backend-0-0'>
	Create a report of the repository configuration file for backend-0-0.
	</example>
	"""

	def run(self, params, args):
		self.beginOutput()

		hosts = self.getHostnames(args)
		self.host_attrs = self.getHostAttrDict(hosts)

		# get the boxes that are actually in use by the hosts we're running against
		box_repos = {
			attrs['box']: self.get_repos_by_box(attrs['box'])
			for attrs in self.host_attrs.values()
		}

		# only generate repo file contents once for each box.
		self.box_repo_data = {}
		for box, repo_data in box_repos.items():
			# replace the variables in the yum repo with data from the repo tables
			repo_lines = self.build_repo_files(repo_data, '/opt/stack/share/templates/yum_repo.j2')
			self.box_repo_data[box] = '\n\n'.join(repo_lines)

		# now for each host, build its customized repo file
		for host in hosts:
			# TODO: ubuntu
			imp = 'yum'
			self.runImplementation(imp, (host,))

		self.endOutput(padChar='', trimOwner=True)
