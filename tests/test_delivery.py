"""Standalone packaging boundaries; the host runs the separate real-app acceptance."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('plugin_build', ROOT / 'scripts/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class DeliveryTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'source'
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', 'dist', '__pycache__'))
        return root

    def test_62_accepted_frames_and_icon_are_byte_identical(self):
        hashes = json.loads((ROOT / 'tests/assets.sha256.json').read_text())
        self.assertEqual(len(hashes), 63)
        for name, expected in hashes.items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)
        report = build.validate(ROOT)
        self.assertEqual(report['frames'], 62)
        self.assertEqual(report['pngBytes'], 7931439)
        self.assertEqual(report['pixels'], 16252928)

    def test_public_manifest_limits_permissions_and_old_host_compatibility(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text())
        self.assertEqual(manifest['id'], 'sword-shield-pilot')
        self.assertEqual(manifest['name'], '刀盾小狗')
        self.assertEqual(manifest['version'], '0.3.1')
        self.assertEqual(manifest['minHostVersion'], '0.23.0')
        self.assertEqual(manifest['permissions'], ['ui', 'appearance', 'pet'])
        self.assertIs(manifest['nodeAccess'], False)
        self.assertNotIn('tool', manifest['entry'])

    def test_archive_is_exact_allowlist_and_preserves_bytes(self):
        root = self.fixture()
        (root / 'host-private-file.txt').write_text('must not be packaged')
        (root / '.env').write_text('must not be packaged')
        artifact = build.build(root, root / 'dist')
        with zipfile.ZipFile(artifact) as archive:
            self.assertEqual(archive.namelist(), sorted(build.runtime_files(root)))
            self.assertEqual(archive.testzip(), None)
            for entry in archive.infolist():
                self.assertEqual(archive.read(entry), (root / entry.filename).read_bytes())
                self.assertEqual(entry.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(entry.external_attr >> 16, 0o100644)
                self.assertEqual(entry.compress_type, zipfile.ZIP_STORED)
        expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
        self.assertEqual((artifact.parent / 'plugin.zip.sha256').read_text(), expected + '  plugin.zip\n')

    def test_build_is_identical_across_mtime_permissions_and_output_directory(self):
        root = self.fixture()
        first = build.build(root, root / 'first').read_bytes()
        for name in build.runtime_files(root):
            os.utime(root / name, (1726000000, 1726000000))
            os.chmod(root / name, 0o600)
        second = build.build(root, root / 'second').read_bytes()
        self.assertEqual(first, second)

    def test_symlink_file_and_symlink_action_directory_are_rejected(self):
        for directory in (False, True):
            with self.subTest(directory=directory):
                root = self.fixture()
                target = root / ('idle' if directory else 'idle/idle00.png')
                moved = target.with_name(target.name + '.real')
                target.rename(moved)
                target.symlink_to(moved, target_is_directory=directory)
                with self.assertRaisesRegex(ValueError, 'symlink'):
                    build.build(root, root / 'dist')

    def test_missing_frame_bad_crc_and_modified_frame_are_rejected(self):
        for mutation in ('missing', 'crc', 'modified'):
            with self.subTest(mutation=mutation):
                root = self.fixture()
                frame = root / 'idle/idle00.png'
                if mutation == 'missing':
                    frame.unlink()
                elif mutation == 'crc':
                    raw = bytearray(frame.read_bytes()); raw[-5] ^= 1; frame.write_bytes(raw)
                else:
                    frame.write_bytes((root / 'idle/idle01.png').read_bytes())
                with self.assertRaises(ValueError):
                    build.build(root, root / 'dist')

    def test_character_external_paths_and_extra_actions_are_rejected(self):
        for value in ('../idle', '/idle', 'https://example.invalid/idle'):
            root = self.fixture()
            file = root / 'character.json'
            data = json.loads(file.read_text()); data['anim']['idle']['dir'] = value
            file.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                build.validate(root)
        root = self.fixture()
        file = root / 'character.json'
        data = json.loads(file.read_text()); data['anim']['custom'] = data['anim']['idle']
        file.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            build.validate(root)

    def test_preview_uses_all_eight_actual_clips(self):
        content = (ROOT / 'preview.js').read_text().strip()
        prefix = 'window.appearancePreview = '
        self.assertTrue(content.startswith(prefix))
        preview = json.loads(content[len(prefix):-1])
        character = json.loads((ROOT / 'character.json').read_text())
        self.assertEqual(set(preview['clips']), set(build.ACTION_COUNTS))
        for state, count in build.ACTION_COUNTS.items():
            clip = preview['clips'][state]
            self.assertEqual(clip['frames'], [f'{state}/{state}{i:02}.png' for i in range(count)])
            self.assertEqual(clip['fps'], character['anim'][state]['fps'])
            self.assertEqual(clip['loop'], character['anim'][state]['loop'])
            self.assertTrue((ROOT / f'docs/previews/{state}.gif').read_bytes().startswith(b'GIF89a'))

    def test_release_tag_matches_both_manifests(self):
        build.validate_tag(ROOT, 'v0.3.1')
        for tag in ('v0.3.0', '0.3.1', 'v0.3.1/extra', ''):
            with self.assertRaises(ValueError):
                build.validate_tag(ROOT, tag)

    def test_source_content_has_no_remote_runtime_or_private_configuration(self):
        build.audit_public_source(ROOT)
        for name in ('panel.js', 'preview.js', 'panel.html', 'panel.css'):
            source = (ROOT / name).read_text()
            for forbidden in ('http://', 'https://', 'require(', 'eval(', 'new Function', 'process.env', 'fetch('):
                self.assertNotIn(forbidden, source, name)

    def test_public_source_audit_rejects_credentials_locations_and_distribution_files(self):
        cases = [('.env.local', 'private configuration'),
                 ('notes.md', '/Users' + '/example/private'),
                 ('notes.md', 'BEGIN ' + 'PRIVATE KEY'),
                 ('host.asar', 'not a plugin')]
        for name, text in cases:
            with self.subTest(name=name):
                root = self.fixture()
                (root / name).write_text(text)
                with self.assertRaises(ValueError):
                    build.audit_public_source(root)


if __name__ == '__main__':
    unittest.main()
