import subprocess
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
import vsp
from vsp_common import tool_path, font_path


class Portability(unittest.TestCase):
    def test_tool_override_and_path(self):
        with tempfile.TemporaryDirectory() as td:
            exe = Path(td) / 'ffmpeg.exe'; exe.touch()
            self.assertEqual(tool_path('ffmpeg', system='win32', environ={'VSP_FFMPEG': str(exe)}, which=lambda _: None), str(exe))
            self.assertEqual(tool_path('ffmpeg', system='win32', environ={}, which=lambda _: str(exe)), str(exe))

    def test_missing_messages(self):
        for os_name, expected in [('linux', 'apt-get'), ('darwin', 'brew install'), ('win32', 'winget install')]:
            with self.subTest(os_name=os_name), self.assertRaisesRegex(FileNotFoundError, expected):
                tool_path('ffmpeg', system=os_name, environ={}, which=lambda _: None)

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

    def test_voice_only_check(self):
        p = subprocess.run([sys.executable, str(ROOT / 'vsp.py'), 'install', '--check', '--voice-only'],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertIn('requirements-voice.lock.txt', p.stdout)
        self.assertNotIn('Chrome-for-Testing', p.stdout)

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
        p = subprocess.run([sys.executable, str(ROOT / 'vsp.py'), 'install', '--check'], cwd=ROOT, capture_output=True, text=True)
        self.assertIn('ffmpeg', p.stdout)
        self.assertIn(p.returncode, (0, 1))

    def test_legacy_leading_install_options(self):
        explicit = subprocess.run([sys.executable, str(ROOT / 'vsp.py'), 'install', '--apt', '--check'],
                                  cwd=ROOT, capture_output=True, text=True)
        legacy = subprocess.run([sys.executable, str(ROOT / 'vsp.py'), '--apt', '--check'],
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
