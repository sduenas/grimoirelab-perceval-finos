#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018-2019 Fintech Open Source Foundation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, 51 Franklin Street, Fifth Floor, Boston, MA 02110-1335, USA.
#
# Authors:
#     Maurizio Pillitu <maoo@finos.org>
#     Santiago Dueñas <sduenas@bitergia.com>
#

import os
import unittest

import httpretty
import pkg_resources

pkg_resources.declare_namespace('perceval.backends')

from perceval.backend import BackendCommandArgumentParser, uuid
from perceval.backends.finos.finosmeetings import (FinosMeetings,
                                                   FinosMeetingsCommand,
                                                   FinosMeetingsClient)


MEETINGS_URL = 'http://example.com/finosmeetings_entries'

requests_http = []


def file_abs_path(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def read_file(filename, mode='r'):
    with open(file_abs_path(filename), mode) as f:
        content = f.read()
    return content


def configure_http_server():
    bodies_entries_job = read_file('data/finosmeetings/finosmeetings_entries.csv')

    http_requests = []

    def request_callback(method, uri, headers):
        last_request = httpretty.last_request()

        if uri.startswith(MEETINGS_URL):
            body = bodies_entries_job
        else:
            body = ''

        requests_http.append(httpretty.last_request())

        http_requests.append(last_request)

        return (200, headers, body)

    httpretty.register_uri(httpretty.GET,
                           MEETINGS_URL,
                           responses=[
                               httpretty.Response(body=request_callback)
                               for _ in range(2)
                           ])

    return http_requests


class TestFinosMeetingsBackend(unittest.TestCase):
    """FinosMeetings backend tests"""

    def test_initialization(self):
        """Test whether attributes are initializated"""

        finosmeetings = FinosMeetings(MEETINGS_URL)

        self.assertTrue(finosmeetings.origin, MEETINGS_URL)
        self.assertIsNone(finosmeetings.client)

    def test_has_archiving(self):
        """Test if it returns True when has_archiving is called"""

        self.assertEqual(FinosMeetings.has_archiving(), False)

    def test_has_resuming(self):
        """Test if it returns False when has_resuming is called"""

        self.assertEqual(FinosMeetings.has_resuming(), False)

    @httpretty.activate
    def test_fetch(self):
        """Test whether a list of entries is returned"""

        http_requests = configure_http_server()

        finosmeetings = FinosMeetings(MEETINGS_URL)

        entries = [entry for entry in finosmeetings.fetch()]
        self.assertEqual(len(entries), 3)
        self.assertEqual(len(http_requests), 1)

        # Test metadata
        expected = [('rob.underwood@finos.org', 'Rob Underwood', 'brooklynrob',
                     'Data Tech', 'Data Tech PMC', 'PMC', '2018-09-28', '2018-09-28T00:00:00+00:00'),
                    ('tosha.ellison@finos.org', 'Tosha Ellison', '', 'Data Tech',
                     'Security Reference Data', 'WORKING_GROUP', '2018-12-11', '2018-12-11T00:00:00+00:00'),
                    ('maoo@finos.org', 'Maurizio Pillitu', 'maoo',
                     'FDC3', 'FDC3 PMC', 'PMC', '2018-10-19', '2018-10-19T00:00:00+00:00')]

        for x in range(len(expected)):
            entry = entries[x]['data']
            self.assertEqual(entries[x]['uuid'], uuid(finosmeetings.origin, FinosMeetings.metadata_id(entry)))
            self.assertEqual(entries[x]['updated_on'], FinosMeetings.metadata_updated_on(entry))
            self.assertEqual(entry['email'], expected[x][0])
            self.assertEqual(entry['name'], expected[x][1])
            self.assertEqual(entry['org'], 'FINOS')
            self.assertEqual(entry['githubid'], expected[x][2])
            self.assertEqual(entry['cm_program'], expected[x][3])
            self.assertEqual(entry['cm_title'], expected[x][4])
            self.assertEqual(entry['cm_type'], expected[x][5])
            self.assertEqual(entry['date'], expected[x][6])
            self.assertEqual(entry['date_iso_format'], expected[x][7])

    @httpretty.activate
    def test_fetch_from_file(self):
        """Test whether a list of entries is returned from a file definition"""

        finosmeetings = FinosMeetings(
            "file://" + file_abs_path('data/finosmeetings/finosmeetings_entries.csv'))

        entries = [entry for entry in finosmeetings.fetch()]
        self.assertEqual(len(entries), 3)

        # Test metadata
        expected = [('rob.underwood@finos.org', 'Rob Underwood', 'brooklynrob',
                     'Data Tech', 'Data Tech PMC', 'PMC', '2018-09-28', '2018-09-28T00:00:00+00:00'),
                    ('tosha.ellison@finos.org', 'Tosha Ellison', '', 'Data Tech',
                     'Security Reference Data', 'WORKING_GROUP', '2018-12-11', '2018-12-11T00:00:00+00:00'),
                    ('maoo@finos.org', 'Maurizio Pillitu', 'maoo',
                     'FDC3', 'FDC3 PMC', 'PMC', '2018-10-19', '2018-10-19T00:00:00+00:00')]

        for x in range(len(expected)):
            entry = entries[x]['data']
            self.assertEqual(entries[x]['uuid'], uuid(finosmeetings.origin, FinosMeetings.metadata_id(entry)))
            self.assertEqual(entries[x]['updated_on'], FinosMeetings.metadata_updated_on(entry))
            self.assertEqual(entry['email'], expected[x][0])
            self.assertEqual(entry['name'], expected[x][1])
            self.assertEqual(entry['org'], 'FINOS')
            self.assertEqual(entry['githubid'], expected[x][2])
            self.assertEqual(entry['cm_program'], expected[x][3])
            self.assertEqual(entry['cm_title'], expected[x][4])
            self.assertEqual(entry['cm_type'], expected[x][5])
            self.assertEqual(entry['date'], expected[x][6])
            self.assertEqual(entry['date_iso_format'], expected[x][7])

    @httpretty.activate
    def test_fetch_empty(self):
        """Test whether it works when no entries are fetched"""

        body = """"""
        httpretty.register_uri(httpretty.GET,
                               MEETINGS_URL,
                               body=body, status=200)

        finosmeetings = FinosMeetings(
            MEETINGS_URL)

        entries = [entry for entry in finosmeetings.fetch()]

        self.assertEqual(len(entries), 0)


class TestFinosMeetingsCommand(unittest.TestCase):
    """CSVCommand unit tests"""

    def test_backend_class(self):
        """Test if the backend class is FinosMeetings"""

        self.assertIs(FinosMeetingsCommand.BACKEND, FinosMeetings)

    def test_setup_cmd_parser(self):
        """Test if it parser object is correctly initialized"""

        parser = FinosMeetingsCommand.setup_cmd_parser()
        self.assertIsInstance(parser, BackendCommandArgumentParser)

        args = [MEETINGS_URL]

        parsed_args = parser.parse(*args)
        self.assertEqual(parsed_args.uri, MEETINGS_URL)


class TestFinosMeetingsClient(unittest.TestCase):
    """FinosMeetings API client tests

    These tests not check the body of the response, only if the call
    was well formed and if a response was obtained. Due to this, take
    into account that the body returned on each request might not
    match with the parameters from the request.
    """
    @httpretty.activate
    def test_get_entries(self):
        """Test get_entries API call"""

        # Set up a mock HTTP server
        body = read_file('data/finosmeetings/finosmeetings_entries.csv')
        httpretty.register_uri(httpretty.GET,
                               MEETINGS_URL,
                               body=body, status=200)

        client = FinosMeetingsClient(MEETINGS_URL, ',', True)
        response = client.get_entries()

        self.assertEqual(len(response), 4)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
