import json

import pytest


class TestDumpGroup:

    """
	Test that dumping the group data works properly by adding a group
	then dumping it and checking that it is valid
	"""

    def test_dump_host(self, host):

        # first lets add a group so we know what to look for in the dump
        results = host.run("stack add group test")
        assert results.rc == 0

        # dump our group information
        results = host.run("stack dump group")
        assert results.rc == 0
        dumped_data = json.loads(results.stdout)

        # check to make sure that the information we just added is in the dump data
        assert dumped_data["group"][0] == "test"
