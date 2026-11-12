import subprocess
import shutil
import os
import stat
import sys
import tempfile
import unittest
import zipfile
import io
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
import vsp
import check_links
from vsp_common import tool_path, font_path


class Portability(unittest.TestCase):
    def test_windows_skill_path_components(self):
        self.assertTrue(check_links.is_expected_skill_path(PureWindowsPath('video-making\\SKILL.md')))
        self.assertFalse(check_links.is_expected_skill_path(PureWindowsPath('other\\SKILL.md')))
        self.assertEqual(check_links.check(ROOT)[0], [])

    def test_cache_override_is_exact(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(vsp.cache_path({'VSP_CACHE': td, 'XDG_CACHE_HOME': 'unused'}), Path(td))
            self.assertEqual(vsp.cache_path({'XDG_CACHE_HOME': td}), Path(td) / 'video-skill-pack')

    def test_chrome_zip_preserves_symlinks_and_modes(self):
        with tempfile.TemporaryDirectory() as td:
            cache = Path(td) / 'cache'
            archive = Path(td) / 'chrome.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                for name, data, mode in [('bundle/chrome', b'chrome', stat.S_IFREG | 0o755),
                                         ('bundle/lib.so', b'lib', stat.S_IFREG | 0o644),
                                         ('bundle/link.so', b'lib.so', stat.S_IFLNK | 0o777)]:
                    info = zipfile.ZipInfo(name)
                    info.create_system = 3
                    info.external_attr = mode << 16
                    z.writestr(info, data)
            with patch.object(vsp, 'CACHE', cache), patch.dict(vsp.CHROME, {'test': ('unused', 'bundle/chrome')}), \
                 patch('vsp.download', return_value=archive), patch('vsp.Path.symlink_to') as symlink:
                binary = vsp.install_chrome('test')
            self.assertTrue(binary.is_file())
            symlink.assert_called_once()
            self.assertEqual(symlink.call_args.args[0], 'lib.so')
            if os.name != 'nt':
                self.assertTrue(binary.stat().st_mode & stat.S_IXUSR)

    def test_tool_override_and_path(self):
        with tempfile.TemporaryDirectory() as td:
            exe = Path(td) / 'ffmpeg.exe'; exe.touch()
            self.assertEqual(tool_path('ffmpeg', system='win32', environ={'VSP_FFMPEG': str(exe)},
                                       which=lambda _: None, extra_dirs=[]), str(exe))
            self.assertEqual(tool_path('ffmpeg', system='win32', environ={}, which=lambda _: str(exe),
                                       extra_dirs=[]), str(exe))

    def test_well_known_directory_lookup(self):
        with tempfile.TemporaryDirectory() as td:
            for os_name, exe_name in [('darwin', 'ffmpeg'), ('win32', 'ffmpeg.exe')]:
                with self.subTest(os_name=os_name):
                    exe = Path(td) / exe_name
                    exe.touch()
                    self.assertEqual(tool_path('ffmpeg', system=os_name, environ={}, which=lambda _: None,
                                               extra_dirs=[td]), str(exe))
                    exe.unlink()

    def test_missing_messages(self):
        for os_name, expected in [('linux', 'apt-get'), ('darwin', 'brew install'), ('win32', 'winget install')]:
            with self.subTest(os_name=os_name), self.assertRaisesRegex(FileNotFoundError, expected):
                tool_path('ffmpeg', system=os_name, environ={}, which=lambda _: None, extra_dirs=[])

    def test_platform_and_intel_gate(self):
        self.assertEqual(vsp.os_key('linux', 'x86_64'), 'linux64')
        self.assertEqual(vsp.os_key('win32', 'AMD64'), 'win64')
        self.assertEqual(vsp.os_key('darwin', 'arm64', '14.5'), 'mac-arm64')
        self.assertEqual(vsp.os_key('darwin', 'x86_64', '14.5'), 'mac-x64')
        with patch('vsp.subprocess.check_output', return_value='1'):
            self.assertTrue(vsp.rosetta_translated('darwin', 'x86_64'))
        with patch('vsp.subprocess.check_output', side_effect=OSError):
            self.assertFalse(vsp.rosetta_translated('darwin', 'x86_64'))
        with self.assertRaisesRegex(RuntimeError, 'macOS 14'):
            vsp.os_key('darwin', 'arm64', '13.5')

    def test_voice_tier_gates_video_before_creating_files(self):
        with tempfile.TemporaryDirectory() as td, patch.object(vsp, 'STATE', Path(td)), patch.dict('os.environ', {'VSP_VOICE_ONLY': '1'}):
            self.assertTrue(vsp.voice_only(vsp.os_key('linux', 'x86_64')))
            a = type('Args', (), {'project': str(Path(td) / 'missing'), 'force': False, 'skip_aligner': False, 'clean': False})()
            for command in (vsp.build, vsp.smoke):
                with self.assertRaisesRegex(RuntimeError, 'Voice-only mode'):
                    command(a)
            self.assertFalse((Path(td) / 'missing').exists())
        with tempfile.TemporaryDirectory() as td, patch.object(vsp, 'STATE', Path(td)), patch.dict('os.environ', {'VSP_VOICE_ONLY': ''}):
            self.assertTrue(vsp.voice_only('mac-x64'))
            self.assertTrue(vsp.voice_only('linux64', forced=True))
            self.assertFalse(vsp.voice_only('linux64'))

    def test_intel_install_uses_voice_lock_without_video_assets(self):
        with tempfile.TemporaryDirectory() as td, patch.object(vsp, 'STATE', Path(td)):
            opts = SimpleNamespace(voice_only=False, check=False, install_system=False, skip_aligner=False,
                no_chrome=False, with_maps=False, with_puppeteer=False, with_hyperframes=False,
                with_remotion=False, with_blender=False, no_link=True)
            with patch('vsp.os_key', return_value='mac-x64'), patch('vsp.rosetta_translated', return_value=False), \
                 patch('vsp.check_system', return_value=True), patch('vsp.bootstrap_uv', return_value='uv'), \
                 patch('vsp.create_venv', return_value=Path(td) / 'python'), patch('vsp.run') as run, \
                 patch('vsp.download'), patch('vsp.install_chrome') as chrome:
                self.assertEqual(vsp.install(opts), 0)
            self.assertEqual((Path(td) / 'tier').read_text().strip(), 'voice-only')
            self.assertTrue(any('requirements-voice.lock.txt' in str(part) for call in run.call_args_list for part in call.args))
            self.assertFalse(any('torch' in str(part).lower() for call in run.call_args_list for part in call.args))
            chrome.assert_not_called()

    def check_plan(self, voice):
        output = io.StringIO()
        def command_output(argv, **_):
            return 'v20.0.0' if '--version' in argv else 'libx264'
        with patch('vsp_common.tool_path', side_effect=lambda name, **_: '/fake/' + name), \
             patch('vsp.subprocess.check_output', side_effect=command_output), \
             patch('vsp.shutil.which', return_value='/fake/uv'), \
             patch('vsp.system_manager', return_value=None), redirect_stdout(output):
            result = vsp.check_system(dry=True, voice=voice)
        self.assertTrue(result)
        return output.getvalue()

    def test_voice_only_check(self):
        output = self.check_plan(voice=True)
        self.assertIn('requirements-voice.lock.txt', output)
        self.assertNotIn('Chrome-for-Testing', output)

    def test_system_command_plans(self):
        self.assertIn('apt-get', vsp.system_commands(['node'], 'apt')[0])
        self.assertEqual(vsp.system_commands(['ffmpeg'], 'brew'), ['brew install ffmpeg'])
        self.assertEqual(len(vsp.system_commands(['ffmpeg', 'node'], 'winget')), 2)
        self.assertIn('choco install', vsp.system_commands(['ffprobe'], 'choco')[0])
        self.assertEqual(vsp.system_manager('darwin', lambda x: '/bin/brew' if x == 'brew' else None), 'brew')
        self.assertEqual(vsp.system_manager('linux', lambda x: '/usr/bin/apt-get' if x == 'apt-get' else None), 'apt')
        self.assertEqual(vsp.system_manager('win32', lambda x: 'winget' if x == 'winget' else None), 'winget')
        self.assertEqual(vsp.system_manager('win32', lambda x: 'choco' if x == 'choco' else None), 'choco')

    def test_venv_paths(self):
        self.assertEqual(vsp.venv_python('win32').name, 'python.exe')
        self.assertEqual(vsp.venv_python('linux').parent.name, 'bin')

    def test_windows_uv_bootstrap_and_newer_bootstrap_python(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / 'state'
            uv = state / 'uv-bootstrap' / 'Scripts' / 'uv.exe'
            uv.parent.mkdir(parents=True)
            uv.touch()
            with patch.object(vsp, 'STATE', state), patch('vsp.sys.platform', 'win32'), \
                 patch('vsp.shutil.which', return_value=None):
                self.assertEqual(vsp.bootstrap_uv(), str(uv))
            venv = Path(td) / '.venv'
            with patch.object(vsp, 'STATE', state), patch.object(vsp, 'VENV', venv), \
                 patch('vsp.venv_python', return_value=venv / 'Scripts' / 'python.exe'), \
                 patch('vsp.subprocess.run') as run:
                vsp.create_venv(str(uv))
            run.assert_called_once_with([str(uv), 'venv', '--python', '3.13', str(venv)], check=True)

    def test_download_local_and_checksum(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / 'source'; src.write_bytes(b'hello')
            dst = Path(td) / 'target'
            vsp.download(src.as_uri(), dst, vsp.sha256(src))
            self.assertEqual(dst.read_bytes(), b'hello')
            with self.assertRaisesRegex(RuntimeError, 'SHA256 mismatch'):
                vsp.download(src.as_uri(), dst, '0' * 64)

    def test_check_no_changes(self):
        with tempfile.TemporaryDirectory() as td, patch.object(vsp, 'STATE', Path(td) / 'state'):
            output = self.check_plan(voice=False)
            self.assertIn('ffmpeg', output)
            self.assertIn('requirements.lock.txt', output)
            self.assertFalse(vsp.STATE.exists())

    def test_legacy_leading_install_options(self):
        explicit = subprocess.run([sys.executable, str(ROOT / 'vsp.py'), 'install', '--apt', '--help'],
                                  cwd=ROOT, capture_output=True, text=True)
        legacy = subprocess.run([sys.executable, str(ROOT / 'vsp.py'), '--apt', '--help'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual((legacy.returncode, legacy.stdout, legacy.stderr),
                         (explicit.returncode, explicit.stdout, explicit.stderr))
        help_result = subprocess.run([sys.executable, str(ROOT / 'vsp.py'), '--help'],
                                     cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn('install --help', help_result.stdout)

    def test_fonts(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(font_path(td, 'win32', {'WINDIR': td}))
            font = Path(td) / 'fonts/Inter.ttf'; font.parent.mkdir(); font.touch()
            self.assertEqual(font_path(td, 'win32', {'WINDIR': td}), font)

    def test_skill_link_and_copy(self):
        with tempfile.TemporaryDirectory() as td:
            a = type('Args', (), {'skills_dir': td, 'link_codex': False, 'link_claude': False, 'copy': False, 'relink': False})()
            vsp.link_skills(a)
            self.assertTrue((Path(td) / 'video-making/SKILL.md').exists())
            link = Path(td) / 'video-making'
            if link.is_symlink(): link.unlink()
            else: shutil.rmtree(link)
            a.copy = True
            vsp.link_skills(a)
            self.assertTrue((Path(td) / 'video-making/.vsp-copy').exists())

    def test_new_vertical(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / 'demo'
            a = type('Args', (), {'project': str(dest), 'motion': True, 'vertical': True})()
            vsp.new(a)
            self.assertIn('const W = 1080, H = 1920;', (dest / 'index.html').read_text())
            self.assertIn('"size": [1080, 1920]', (dest / 'beats.json').read_text())
            self.assertEqual(__import__('json').loads((dest / 'project.json').read_text())['width'], 1080)


if __name__ == '__main__': unittest.main()
