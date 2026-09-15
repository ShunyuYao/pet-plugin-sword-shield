"""Standalone packaging boundaries; the host runs the separate real-app acceptance."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('plugin_build', ROOT / 'scripts/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def rgba_png(width, height, *, level=9, depth=8, color=6):
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))
    rows = (b'\0' + b'\0\0\0\0' * width) * height
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, depth, color, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows, level)) + chunk(b'IEND', b''))


class DeliveryTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'source'
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', 'dist', '__pycache__'))
        return root

    def test_historical_baseline_is_retained_and_current_assets_are_frozen(self):
        historical = (ROOT / 'tests/accepted-v0.3.1.sha256.json').read_bytes()
        self.assertEqual(hashlib.sha256(historical).hexdigest(),
                         'cbdb3c56bc29e3f89f04d47ef306fa5cc3ea32c2ff70ecfdb3b59de1d6f3c7f3')
        hashes = json.loads((ROOT / 'tests/accepted-v0.5.0.sha256.json').read_text())
        self.assertEqual(len(hashes), 178)
        for name, expected in hashes.items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)
        self.assertEqual(hashes['tray.png'], json.loads(historical)['tray.png'])

    def test_greeting_keeps_complete_b_timing(self):
        for field, value in [('fps', 12), ('loop', True)]:
            root = self.fixture()
            file = root / 'character.json'
            spec = json.loads(file.read_text())
            spec['anim']['greet'][field] = value
            file.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'greet timing'):
                build.validate(root)

    def test_202_frames_fit_unchanged_production_resource_limits(self):
        self.assertEqual(build.MAX_PNG_BYTES, 8 * 1024**2)
        self.assertEqual(build.MAX_PIXELS, 32 * 1024**2)
        hashes = json.loads((ROOT / 'tests/assets.sha256.json').read_text())
        self.assertEqual(len(hashes), 203)
        report = build.validate(ROOT)
        self.assertEqual(report['frames'], 202)
        self.assertLessEqual(report['pngBytes'], build.MAX_PNG_BYTES)
        self.assertLessEqual(report['pixels'], build.MAX_PIXELS)

    def replace_and_rehash(self, root, replacements):
        ledger = root / 'tests/assets.sha256.json'
        hashes = json.loads(ledger.read_text())
        for name, raw in replacements.items():
            (root / name).write_bytes(raw)
            hashes[name] = hashlib.sha256(raw).hexdigest()
        ledger.write_text(json.dumps(hashes))

    def test_updating_current_ledger_cannot_replace_an_accepted_frame_or_icon(self):
        for name in ('idle/idle00.png', 'tray.png'):
            with self.subTest(name=name):
                root = self.fixture()
                self.replace_and_rehash(root, {name: (root / 'idle/idle01.png').read_bytes()})
                with self.assertRaisesRegex(ValueError, 'v0.5.0 assets must remain unchanged'):
                    build.validate(root)

    def test_real_valid_pngs_cannot_exceed_byte_or_decoded_pixel_budget(self):
        for budget, width, level in [('bytes', 512, 0), ('pixels', 1024, 9)]:
            with self.subTest(budget=budget):
                root = self.fixture()
                raw = rgba_png(width, width, level=level)
                self.assertEqual(build.png_pixels(raw), width * width)
                replacements = {f'{state}/{state}{i:02}.png': raw
                                for state in build.EDGE_LOOPS for i in range(build.ACTION_COUNTS[state])}
                self.replace_and_rehash(root, replacements)
                with self.assertRaisesRegex(ValueError, 'resource budget exceeded'):
                    build.validate(root)

    def test_png_requires_rgba8_and_bounded_dimensions(self):
        for kwargs in ({'depth': 16}, {'color': 2}, {}):
            width = 1025 if not kwargs else 16
            with self.subTest(width=width, kwargs=kwargs):
                with self.assertRaisesRegex(ValueError, 'bounded RGBA8'):
                    build.png_pixels(rgba_png(width, 16, **kwargs))

    def test_peek_hold_unpeek_share_exact_seams_and_have_motion(self):
        endpoint = (ROOT / 'peek/peek11.png').read_bytes()
        self.assertEqual((ROOT / 'edgehide/edgehide00.png').read_bytes(), endpoint)
        self.assertEqual((ROOT / 'unpeek/unpeek00.png').read_bytes(), endpoint)
        for state in ('peek', 'unpeek'):
            frames = [(ROOT / f'{state}/{state}{i:02}.png').read_bytes() for i in range(12)]
            self.assertNotEqual(frames[0], frames[-1], state + ' must transition, not hold one frame')
        for name in ('edgehide/edgehide00.png', 'unpeek/unpeek00.png'):
            with self.subTest(name=name):
                root = self.fixture()
                self.replace_and_rehash(root, {name: (root / 'peek/peek00.png').read_bytes()})
                with self.assertRaisesRegex(ValueError, 'seam must be byte-identical'):
                    build.validate(root)

    def test_edge_clip_loops_and_canvas_seams_are_not_relaxed(self):
        for state, expected in build.EDGE_LOOPS.items():
            root = self.fixture()
            file = root / 'character.json'
            character = json.loads(file.read_text())
            self.assertIs(character['anim'][state]['loop'], expected)
            character['anim'][state]['loop'] = not expected
            file.write_text(json.dumps(character))
            with self.assertRaisesRegex(ValueError, 'loop contract mismatch'):
                build.validate(root)
        root = self.fixture()
        old_width = struct.unpack('>I', (root / 'peek/peek03.png').read_bytes()[16:20])[0]
        new_width = 384 if old_width == 320 else 320
        self.replace_and_rehash(root, {'peek/peek03.png': rgba_png(new_width, new_width)})
        with self.assertRaisesRegex(ValueError, 'canvas dimensions must match'):
            build.validate(root)

    def test_edge_clip_timing_matches_the_accepted_durations(self):
        character = json.loads((ROOT / 'character.json').read_text())
        for state, count, fps in [('peek', 12, 12), ('unpeek', 12, 15), ('edgehide', 1, 1)]:
            with self.subTest(state=state):
                self.assertEqual(character['anim'][state]['count'], count)
                self.assertEqual(character['anim'][state]['fps'], fps)
                root = self.fixture()
                file = root / 'character.json'
                changed = json.loads(file.read_text())
                changed['anim'][state]['fps'] = fps + 1
                file.write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError, 'timing contract mismatch'):
                    build.validate(root)

    def test_public_manifest_limits_permissions_and_old_host_compatibility(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text())
        self.assertEqual(manifest['id'], 'sword-shield-pilot')
        self.assertEqual(manifest['name'], '刀盾小狗')
        self.assertEqual(manifest['version'], '0.5.0')
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

    def test_preview_uses_all_eleven_actual_clips(self):
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
            if state != 'edgehide':
                self.assertTrue((ROOT / f'docs/previews/{state}.gif').read_bytes().startswith(b'GIF89a'))

    def test_release_tag_matches_both_manifests(self):
        build.validate_tag(ROOT, 'v0.5.0')
        for tag in ('v0.3.1', '0.5.0', 'v0.5.0/extra', ''):
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
