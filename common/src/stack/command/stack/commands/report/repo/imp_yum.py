# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import jinja2

import stack.commands

class Implementation(stack.commands.Implementation):

	def run(self, args):
		host	= args[0]
		osname	= self.owner.host_attrs[host]['os']
		box	= self.owner.host_attrs[host]['box']
		repo	= []

		if osname == 'sles':
			filename = '/etc/zypp/repos.d/stacki.repo'
		elif osname == 'redhat':
			filename = '/etc/yum.repos.d/stacki.repo'

		repo.append('<stack:file stack:name="%s">' % filename)

		# make a second jinja pass at the repo data, in case it has variables with stacki attributes
		repo_str = jinja2.Template(self.owner.box_repo_data[box]).render(**self.owner.host_attrs[host])
		repo.extend(repo_str.splitlines())

		# TODO carts should call add repo, then this goes away
		for o in self.owner.call('list.cart'):
			if box in o['boxes'].split():
				repo.append('[%s-cart]' % o['name'])
				repo.append('name=%s cart' % o['name'])
				repo.append('baseurl=http://%s/install/carts/%s' % (server, o['name']))
				repo.append('gpgcheck=0')

		repo.append('</stack:file>')
		repo.append('zypper clean --all')

		for line in repo:
			self.owner.addOutput(host, line)

