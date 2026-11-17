"""One supported renderer; detail pages are built only when requested."""
import io
import sys
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch
import xml.etree.ElementTree as E
from oci_lenz.model import sample
from oci_lenz.display import prepare_display
from oci_lenz.architecture import make_scene
from oci_lenz.draw import render,validate
from oci_lenz.cli import main


class GenerationPathTests(unittest.TestCase):
    def test_overview_builds_no_discarded_vcn_pages(self):
        scene=make_scene(prepare_display(sample('overview')),view='overview')
        self.assertEqual(len(E.fromstring(scene['xml']).findall('diagram')),1)

    def test_default_library_render_matches_cli_architecture_mode(self):
        snapshot=prepare_display(sample('overview'))
        xml=render(snapshot)
        self.assertEqual(xml,render(snapshot,style='architecture'))
        self.assertEqual([p.get('id') for p in E.fromstring(xml)],['region','information-index'])
        validate(xml,snapshot)

    def test_retired_styles_are_rejected_before_files_or_model_calls(self):
        for style in ('inventory','service-map'):
            argv=['oci-lenz','draw','--snapshot','unused','--output','unused','--style',style]
            with self.subTest(style=style),patch.object(sys,'argv',argv),redirect_stderr(io.StringIO()),patch('oci_lenz.cli.skill_layout') as model:
                with self.assertRaises(SystemExit) as failure:main()
                self.assertEqual(failure.exception.code,2)
                model.assert_not_called()
            with self.assertRaises(ValueError):render(sample(),style=style)

    def test_optional_network_details_still_preserve_all_page_evidence(self):
        snapshot=prepare_display(sample('overview'))
        xml=render(snapshot,detail_pages=True);validate(xml,snapshot)
        pages=E.fromstring(xml).findall('diagram')
        self.assertEqual(len(pages),5)
        self.assertEqual(pages[-1].get('id'),'information-index')
