# @copyright@
# Copyright (c) 2006 - 2019 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import json
from collections import OrderedDict

import stack
import stack.commands


class Command(stack.commands.dump.command):
    """
	Dump the contents of the stacki database as json.

	This command dumps specifically the pallet data.
	For each pallet, output the name of the pallet, as
	well as its version, release, architecture, OS,
	source URL, and its tag.

	<example cmd='dump pallet'>
	Dump json data for pallets in the stacki database
	</example>

	<related>load</related>
	"""

    def run(self, params, args):

        self.set_scope("software")

        dump = []
        for row in self.call("list.pallet", ["expanded=true"]):
            name = row["name"]
            version = row["version"]
            release = row["release"]
            arch = row["arch"]
            os = row["os"]
            tag = []

            for _row in self.call(
                "list.pallet.tag",
                [
                    name,
                    f"version={version}",
                    f"release={release}",
                    f"arch={arch}",
                    f"os={os}",
                ],
            ):
                tag.append(OrderedDict(name=_row["tag"], value=_row["value"]))

            dump.append(
                OrderedDict(
                    name=name,
                    version=version,
                    release=release,
                    arch=arch,
                    os=os,
                    url=row["url"],
                    tag=tag,
                )
            )

        self.addText(
            json.dumps(
                OrderedDict(version=stack.version, software={"pallet": dump}), indent=8
            )
        )
