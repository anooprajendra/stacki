from collections import namedtuple
import jinja2

class RepoArgumentProcessor:
	REQUIRED_REPO_COLUMNS = [
		'name',
		'alias',
		'uri',
	]

	OPTIONAL_REPO_COLUMNS = [
		'autorefresh',
		'assumeyes',
		'type',
		'is_mirrorlist',
		'gpgcheck',
		'gpgkey',
		'os',
		'pallet_id',
	]

	REPO_COLUMNS = REQUIRED_REPO_COLUMNS + OPTIONAL_REPO_COLUMNS

	def insert_repo(self, name, alias, uri, **kwargs):
		'''
		Insert a repo with optional kwargs into the repos table.
		This works like add pallet - if you try to add a repo that already exists, silently succeed
		 '''
		data = {}
		for key in self.OPTIONAL_REPO_COLUMNS:
			if key in kwargs:
				data[key] = kwargs[key]

		where_clause = ' AND '.join(f'{col}=%s' for col in self.REQUIRED_REPO_COLUMNS + list(data))
		select_stmt = f'''id FROM repos WHERE {where_clause}'''

		if len(self.db.select(select_stmt, [name, alias, uri] + list(data.values()))) != 0:
			return

		cols = ', '.join(['name', 'alias', 'uri'] + list(data))
		vals = ', '.join(['%s'] * (3 + len(data.values())))

		sql = f'''INSERT INTO repos
			({cols})
			VALUES
			({vals})
			'''
		self.db.execute(sql, (name, alias, uri, *data.values()))

	def delete_repo(self, name):
		''' delete the repo from the database, should also remove any box associations '''
		sql = '''DELETE FROM repos WHERE name=%s '''
		self.db.execute(sql, (name, ))

	def enable_repo(self, repo, box):
		''' add a row to the repo_stacks table, tying a repo to a box '''

		repo_id = self.db.select('id FROM repos WHERE name=%s', (repo,))[0][0]
		box_id = self.db.select('id FROM boxes WHERE name=%s', (box,))[0][0]
		sql = '''INSERT INTO repo_stacks
			(box, repo)
			VALUES
			(%s, %s)
			'''
		self.db.execute(sql, (box_id, repo_id))

	def disable_repo(self, repo, box):
		''' disable the repo for a given box '''
		repo_id = self.db.select('id FROM repos WHERE name=%s', (repo,))[0][0]
		box_id = self.db.select('id FROM boxes WHERE name=%s', (box,))[0][0]
		sql = '''DELETE FROM repo_stacks WHERE box=%s AND repo=%s '''
		self.db.execute(sql, (box_id, repo_id))

	def get_repos(self):
		'''
		return a list of repo named tuples
		'''

		cols = ["repos.{}".format(c) for c in self.REPO_COLUMNS if c != 'pallet_id']
		cols.append('pallets.name as palletname')

		sql = f'''{", ".join(cols)}
			FROM repos
			LEFT JOIN rolls AS pallets
				ON pallets.id = repos.pallet_id
		'''

		RepoStuff = namedtuple('RepoStuff', ['palletname' if c == 'pallet_id' else c for c in self.REPO_COLUMNS])
		
		repos = []
		for result in self.db.select(sql):
			repos.append(RepoStuff(*result))
		return repos

	def get_repos_by_box(self, box):
		'''
		return a dictionary `{box_name: [{repo_name: {repo_keys: repo_vals}}]}`"
		For example:
		{'default': [{
			'stacki': {
				'name': "stacki 5.4.1 sles15",
				'alias': 'stacki-5.4.1-sles15',
				'uri': 'http://example.com/etc/',
				'foo': 'bar',
				},
			},]
		}
		'''

		sql = f'''{", ".join(["repos.{}".format(c) for c in self.REPO_COLUMNS])}
			FROM repos, repo_stacks, boxes
			WHERE boxes.id=repo_stacks.box
				AND repos.id=repo_stacks.repo
				AND boxes.id=%s
			'''
		#TODO replace this query?
		box_id = self.db.select('id FROM boxes WHERE name=%s', box)[0][0]
		box_data = {}
		for result in self.db.select(sql, (box_id, )):
			repo_data = dict(zip(self.REPO_COLUMNS, result))
			# who knows, maybe someday we want to return disabled repos
			repo_data['is_enabled'] = '1'
			box_data[repo_data['name']] = repo_data
		return {box: box_data}

	def build_repo_files(self, box_data, repo_template):
		# TODO does this belong here?
                import pathlib
                templ = jinja2.Template(pathlib.Path(repo_template).read_text(), lstrip_blocks=True, trim_blocks=True)
                repo_stanzas = []
                for repo_data in box_data.values():
                        for repo in repo_data.values():
                                lines = [s for s in templ.render(**repo).splitlines() if s]
                                repo_stanzas.append('\n'.join(lines))
                return repo_stanzas
