# vim: fileencoding=utf-8

#
# The Qubes OS Project, https://www.qubes-os.org/
#
# Copyright (C) 2016
#                   Marek Marczykowski-Górecki <marmarek@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import os
import unittest

import itertools
import qubes.tests.extra


# noinspection PyPep8Naming
class TC_00_PDFConverter(qubes.tests.extra.ExtraTestCase):
    def setUp(self):
        super(TC_00_PDFConverter, self).setUp()
        # noinspection PyAttributeOutsideInit
        self.vm = self.create_vms(["vm"])[0]
        self.vm.start()

    def create_pdf(self, filename, content):
        '''Create PDF file with given (textual) content

        :param filename: output filename
        :param content: content to be placed on each page (list of str)
        '''
        for (page_content, page_no) in zip(content, itertools.count()):
            p = self.vm.run(
                'cat > /tmp/page{no:04}.txt && '
                'convert /tmp/page{no:04}.txt /tmp/page{no:04}.pdf 2>&1'.format(
                    no=page_no), passio_popen=True)
            (stdout, _) = p.communicate(page_content)
            if p.returncode != 0:
                self.skipTest('failed to create test page: {}'.format(stdout))

        p = self.vm.run('pdfunite /tmp/page*.pdf "{}" 2>&1'.format(filename),
            passio_popen=True)
        (stdout, _) = p.communicate()
        if p.returncode != 0:
            self.skipTest('failed to create test pdf: {}'.format(stdout))

    def get_pdfinfo(self, filename):
        p = self.vm.run('pdfinfo "{}"'.format(filename), passio_popen=True)
        (stdout, _) = p.communicate()
        self.assertEquals(p.returncode, 0,
            "Failed to get pdfinfo of {}".format(filename))
        pdfinfo = {}
        for line in stdout.splitlines():
            k, v = line.split(':', 1)
            pdfinfo[k] = v.strip()
        return pdfinfo

    def assertCorrectlyTransformed(self, orig_filename, trusted_filename):
        self.assertEquals(
            self.vm.run('test -r "{}"'.format(trusted_filename), wait=True), 0)
        # TODO: somehow verify content of generated file, for now perform
        # some heuristics
        orig_info = self.get_pdfinfo(orig_filename)
        trusted_info = self.get_pdfinfo(trusted_filename)
        # 1. check number of pages
        self.assertEqual(trusted_info['Pages'], orig_info['Pages'])

        untrusted_backup = 'QubesUntrustedPDFs/{}'.format(os.path.basename(
            trusted_filename.replace('.trusted', '')))
        self.assertEquals(
            self.vm.run('test -r "{}"'.format(untrusted_backup), wait=True), 0)
        self.assertEquals(self.vm.run(
            'diff "{}" "{}"'.format(orig_filename, untrusted_backup), wait=True), 0)

    def test_000_one_page(self):
        self.create_pdf('test.pdf', ['This is test'])
        p = self.vm.run('cp test.pdf orig.pdf; qvm-convert-pdf test.pdf 2>&1',
            passio_popen=True)
        (stdout, _) = p.communicate()
        self.assertEquals(p.returncode, 0, 'qvm-convert-pdf failed: ' + stdout)
        self.assertCorrectlyTransformed('orig.pdf', 'test.trusted.pdf')

    def test_001_two_pages(self):
        self.create_pdf('test.pdf', ['This is test', 'Second page'])
        p = self.vm.run('cp test.pdf orig.pdf; qvm-convert-pdf test.pdf 2>&1',
            passio_popen=True)
        (stdout, _) = p.communicate()
        self.assertEquals(p.returncode, 0, 'qvm-convert-pdf failed: ' + stdout)
        self.assertCorrectlyTransformed('orig.pdf', 'test.trusted.pdf')

    def test_002_500_pages(self):
        self.create_pdf('test.pdf', ['This is test'] * 500)
        p = self.vm.run('cp test.pdf orig.pdf; qvm-convert-pdf test.pdf 2>&1',
            passio_popen=True)
        (stdout, _) = p.communicate()
        self.assertEquals(p.returncode, 0, 'qvm-convert-pdf failed: ' + stdout)
        self.assertCorrectlyTransformed('orig.pdf', 'test.trusted.pdf')

    def test_003_filename_with_spaces(self):
        self.create_pdf('test with spaces.pdf', ['This is test'])
        p = self.vm.run(
            'cp "test with spaces.pdf" orig.pdf; '
            'qvm-convert-pdf "test with spaces.pdf" 2>&1',
            passio_popen=True)
        (stdout, _) = p.communicate()
        self.assertEquals(p.returncode, 0, 'qvm-convert-pdf failed: ' + stdout)
        self.assertCorrectlyTransformed('orig.pdf',
            'test with spaces.trusted.pdf')


def list_tests():
    tests = [TC_00_PDFConverter]
    return tests
