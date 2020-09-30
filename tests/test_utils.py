from django.test import TestCase, RequestFactory
from django.utils import timezone

from djangoplicity.mailinglists.utils import DataQueryParser


class UtilsTest(TestCase):
    def test_data_query_parser(self):
        parsed_data = DataQueryParser.parse({
            "data[merges][GROUPINGS][0][name]": "Tick the category you qualify for:",
            "data[merges][GROUPINGS][0][id]": "1",
        })

        self.assertEquals(parsed_data, {u'merges': {u'GROUPINGS': [{u'id': u'1', u'name': u'Tick the category you qualify for:'}]}})
