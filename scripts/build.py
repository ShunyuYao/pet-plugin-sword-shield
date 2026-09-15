#!/usr/bin/env python3
"""Validate and package only this plugin, using the Python standard library."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_ACTION_COUNTS = dict(idle=12, walk=12, greet=121, speak=6, sleep=6, wake=6, drag=6, send=8)
ACTION_COUNTS = dict(ACCEPTED_ACTION_COUNTS, peek=12, unpeek=12, edgehide=1)
EDGE_LOOPS = dict(peek=False, unpeek=False, edgehide=True)
EDGE_FPS = dict(peek=12, unpeek=15, edgehide=1)
MAX_PNG_BYTES = 8 * 1024**2
MAX_PIXELS = 32 * 1024**2
BASE_FILES = ('manifest.json', 'character.json', 'panel.html', 'panel.css', 'panel.js',
              'preview.js', 'tray.png', 'LICENSE', 'ASSETS.md', 'arrival.wav')


def read_regular(root, name):
    path = root
    for component in Path(name).parts:
        path = path / component
        if path.is_symlink():
            raise ValueError('symlink is not allowed: ' + name)
    if not path.is_file():
        raise ValueError('missing regular file: ' + name)
    return path.read_bytes()


def runtime_files(root):
    return list(BASE_FILES) + [f'{state}/{state}{i:02}.png'
                              for state, count in ACTION_COUNTS.items() for i in range(count)]


def png_pixels(raw):
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('invalid PNG signature')
    offset, width, height, seen_end = 8, 0, 0, False
    compressed = bytearray()
    while offset < len(raw):
        if offset + 12 > len(raw):
            raise ValueError('truncated PNG')
        length, kind = struct.unpack('>I4s', raw[offset:offset + 8])
        end = offset + 12 + length
        if end > len(raw):
            raise ValueError('truncated PNG chunk')
        payload = raw[offset + 8:offset + 8 + length]
        crc = struct.unpack('>I', raw[offset + 8 + length:end])[0]
        if zlib.crc32(kind + payload) != crc:
            raise ValueError('PNG CRC mismatch')
        if kind == b'IHDR':
            if offset != 8 or length != 13 or width:
                raise ValueError('invalid PNG header')
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', payload)
            if not (0 < width <= 1024 and 0 < height <= 1024) or (depth, color, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                raise ValueError('expected bounded RGBA8 static PNG')
        elif kind == b'IDAT':
            if not width:
                raise ValueError('PNG header missing')
            compressed.extend(payload)
        elif kind == b'IEND':
            if length or end != len(raw):
                raise ValueError('invalid PNG end')
            seen_end = True
        else:
            raise ValueError('unexpected PNG chunk')
        offset = end
    if not seen_end or not compressed:
        raise ValueError('incomplete PNG')
    expected = (width * 4 + 1) * height
    decoder = zlib.decompressobj()
    try:
        decoded = decoder.decompress(bytes(compressed), expected + 1)
    except zlib.error as error:
        raise ValueError('invalid PNG stream') from error
    if len(decoded) != expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('PNG decode budget or stream mismatch')
    if any(decoded[y * (width * 4 + 1)] > 4 for y in range(height)):
        raise ValueError('invalid PNG row filter')
    return width * height


def validate(root):
    root = Path(root)
    manifest = json.loads(read_regular(root, 'manifest.json'))
    package = json.loads(read_regular(root, 'package.json'))
    if (manifest.get('id') != 'sword-shield-pilot' or manifest.get('version') != package.get('version')
            or not re.fullmatch(r'\d+\.\d+\.\d+', manifest.get('version', ''))
            or manifest.get('apiVersion') != 1 or manifest.get('minHostVersion') != '0.24.0'
            or manifest.get('permissions') != ['ui', 'appearance', 'pet']
            or manifest.get('kind') != ['asset', 'panel'] or manifest.get('nodeAccess') is not False
            or set(manifest.get('entry', {})) != {'character', 'panel'}
            or manifest['entry']['character'] != 'character.json'
            or manifest['entry']['panel'].get('src') != 'panel.html'):
        raise ValueError('plugin metadata or permission contract mismatch')
    character = json.loads(read_regular(root, 'character.json'))
    if character.get('key') != manifest['id'] or character.get('icon') != 'tray.png' or set(character.get('anim', {})) != set(ACTION_COUNTS):
        raise ValueError('character contract mismatch')
    hashes = json.loads(read_regular(root, 'tests/assets.sha256.json'))
    expected_images = set(runtime_files(root)) - set(BASE_FILES) | {'tray.png'}
    if set(hashes) != expected_images:
        raise ValueError('frozen asset inventory mismatch')
    accepted = json.loads(read_regular(root, 'tests/accepted-v0.5.0.sha256.json'))
    accepted_images = {f'{state}/{state}{i:02}.png'
                       for state, count in ACCEPTED_ACTION_COUNTS.items() for i in range(count)} | {'tray.png'}
    if set(accepted) != accepted_images:
        raise ValueError('accepted v0.5.0 inventory mismatch')
    if any(hashes[name] != digest for name, digest in accepted.items()):
        raise ValueError('accepted v0.5.0 assets must remain unchanged')
    total_bytes = pixels = frames = 0
    edge_dimensions = set()
    for state, count in ACTION_COUNTS.items():
        clip = character['anim'][state]
        if (clip.get('dir') != state or clip.get('base') != state or clip.get('count') != count
                or clip.get('pad') != 2 or clip.get('ext') != 'png' or clip.get('face') != 1
                or type(clip.get('loop')) is not bool or not isinstance(clip.get('fps'), (int, float))
                or not 0 < clip['fps'] <= 60):
            raise ValueError('animation contract mismatch: ' + state)
        if state == 'greet' and (clip['fps'] != 24 or clip['loop'] is not False):
            raise ValueError('greet timing contract mismatch')
        if state in EDGE_LOOPS and clip['loop'] is not EDGE_LOOPS[state]:
            raise ValueError('edge animation loop contract mismatch: ' + state)
        if state in EDGE_FPS and clip['fps'] != EDGE_FPS[state]:
            raise ValueError('edge animation timing contract mismatch: ' + state)
        for i in range(count):
            name = f'{state}/{state}{i:02}.png'
            raw = read_regular(root, name)
            pixels += png_pixels(raw)
            if state in EDGE_LOOPS:
                edge_dimensions.add(struct.unpack('>II', raw[16:24]))
            if hashlib.sha256(raw).hexdigest() != hashes[name]:
                raise ValueError('accepted asset hash changed: ' + name)
            total_bytes += len(raw)
            frames += 1
    if total_bytes > MAX_PNG_BYTES or pixels > MAX_PIXELS or frames > 256:
        raise ValueError('appearance resource budget exceeded')
    if len(edge_dimensions) != 1:
        raise ValueError('edge animation canvas dimensions must match')
    endpoint = read_regular(root, 'peek/peek11.png')
    if (read_regular(root, 'unpeek/unpeek00.png') != endpoint
            or read_regular(root, 'edgehide/edgehide00.png') != endpoint):
        raise ValueError('peek, edgehide and unpeek seam must be byte-identical')
    icon = read_regular(root, 'tray.png')
    png_pixels(icon)
    if hashlib.sha256(icon).hexdigest() != hashes['tray.png']:
        raise ValueError('accepted icon hash changed')
    if character.get('arrivalAudio') != dict(file='arrival.wav', repeats=2, gapMs=180):
        raise ValueError('arrival audio contract mismatch')
    voice = read_regular(root, 'arrival.wav')
    if hashlib.sha256(voice).hexdigest() != '6070e49c11ea2da9cf1ef89bcfceb3fb3229f3e63dd93652f9ae0012ba85ecc2':
        raise ValueError('arrival audio hash changed')
    for name in BASE_FILES:
        read_regular(root, name)
    return {'frames': frames, 'pngBytes': total_bytes, 'pixels': pixels}


def validate_tag(root, tag):
    manifest = json.loads(read_regular(Path(root), 'manifest.json'))
    package = json.loads(read_regular(Path(root), 'package.json'))
    if tag != 'v' + manifest['version'] or manifest['version'] != package['version']:
        raise ValueError('release tag must match plugin and package versions')


def audit_public_source(root):
    """A narrow disclosure guard; editorial and asset-rights review remain required."""
    root = Path(root)
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if any(part in {'.git', 'dist', '__pycache__'} for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError('public source contains a symlink')
        if path.name.startswith('.env') or path.suffix.lower() in {'.pem', '.key', '.log', '.dmg', '.asar', '.exe'}:
            raise ValueError('unexpected private or binary distribution file')
        if not path.is_file() or path.suffix in {'.png', '.gif', '.jpg', '.wav'}:
            continue
        content = path.read_text(encoding='utf-8')
        # Build these markers from pieces so the scanner does not flag its own source.
        forbidden = ('/Users' + '/', '/home' + '/', 'file:' + '//',
                     'BEGIN ' + 'PRIVATE KEY', 'sk-' + 'proj-', 'github_' + 'pat_')
        if any(marker in content for marker in forbidden):
            raise ValueError('public text contains a private-location or credential marker')


def build(root=ROOT, destination=None):
    root = Path(root)
    report = validate(root)
    destination = Path(destination) if destination is not None else root / 'dist'
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / 'plugin.zip'
    # PNG is already compressed. STORE avoids zlib-version variance across runners.
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
        for name in sorted(runtime_files(root)):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(entry, read_regular(root, name))
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    (destination / 'plugin.zip.sha256').write_text(digest + '  plugin.zip\n', encoding='ascii')
    (destination / 'release-notes.md').write_text(
        '刀盾小狗 / Sword & Shield Pup\n\n'
        '11 个动作状态，202 帧透明 PNG；正常串门站定后播放约5秒B版打招呼，保留探头、收回与贴边停靠。\n'
        '11 states, 202 transparent PNG frames. Two voice repeats before the five-second B greeting; dragging and recall stop audio. Both peers require host 0.24.0. Host builds remain invitation-only.\n'
        '需要吐梨邦 0.24.0 或更新的兼容测试版本。Requires compatible Tulibang 0.24.0 or later.\n\n'
        '透明留白扩大，默认100%尺寸建议调至125%保持身体大小；不会自动调整。\n'
        'For the enlarged transparent canvas, change default size from 100% to 125% to preserve body scale; not automatic.\n'
        '权限 / Permissions: ui, appearance, pet. Node access: false.\n'
        '安装不会自动换装；在插件面板选择使用。Installing does not change appearance automatically.\n\n'
        '代码使用 MIT 许可；图片来源与权利说明见包内 ASSETS.md，不包含在代码许可内。\n'
        'MIT applies to code only; see ASSETS.md for image provenance and rights.\n\n'
        f'SHA-256 (plugin.zip): `{digest}`\n', encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-tag')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    try:
        if args.check_tag is not None:
            validate_tag(ROOT, args.check_tag)
        audit_public_source(ROOT)
        report = validate(ROOT)
        if not args.check_only:
            build()
        print(json.dumps(report, sort_keys=True))
        if not args.check_only:
            print((ROOT / 'dist/plugin.zip.sha256').read_text().strip())
    except (ValueError, OSError) as error:
        parser.exit(1, 'Plugin validation failed: ' + str(error) + '\n')
