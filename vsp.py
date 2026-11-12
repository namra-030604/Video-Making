#!/usr/bin/env python3
"""Portable, standard-library entry point for the video skill pack."""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = Path(os.environ.get('VSP_CACHE') or Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'video-skill-pack')
STATE = ROOT / '.vsp-state'
VENV = ROOT / '.venv'
CHROME_VERSION = '156.0.8078.47'
CHROME = {
    'linux64': ('0d5acc62c3e213f8c87d3c298d66ffcf9a236d12ea4b9f85318bf85dbc279daa', 'chrome-headless-shell-linux64/chrome-headless-shell'),
    'mac-arm64': ('2fd1c09a3e1ebde9e69e6aba92f1dd3f21ad247b55d9bf66e39213ff4205436d', 'chrome-headless-shell-mac-arm64/chrome-headless-shell'),
    'mac-x64': ('5e230044c6ac989597f4a4e301a0a710d257e07d6f7754754da2bf62ea3d272c', 'chrome-headless-shell-mac-x64/chrome-headless-shell'),
    'win64': ('e0af9b23f8051cca4f37ca49cd425e8055701bfc0383c198d67f8d5cc5884249', 'chrome-headless-shell-win64/chrome-headless-shell.exe'),
}
MODEL_BASE = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0'
MODELS = [('kokoro-v1.0.int8.onnx', '6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb'),
          ('voices-v1.0.bin', 'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d')]
FONT_COMMIT = '6157dfaa640ca5738b4d1a7070fe389c3036d7fc'
FONTS = [('Inter.ttf', 'ofl/inter/Inter%5Bopsz,wght%5D.ttf', '29160a80ff49ddcab2c97711247e08b1fab27a484a329ce8b813d820dc559031'),
         ('Inter-OFL.txt', 'ofl/inter/OFL.txt', '5b9321a4298cfeb6b34354164a1c3afc3db114569984c502b9b35d988fd58c57'),
         ('Caveat.ttf', 'ofl/caveat/Caveat%5Bwght%5D.ttf', '0bdb6b660482d31531b3945849fba5916b3ef8695da7024a9e6b9ee3c4157988'),
         ('Caveat-OFL.txt', 'ofl/caveat/OFL.txt', '1f9d81d094273d82f3898a1ee8b598a717d050ecbf5ff7bede105b704880157b')]
MMS_SHA = '20ef12963ab4924bef49ac4fc7f58ad5da2ee43b2c11bc8c853c9b90ecdbc680'
HINTS = {'linux': 'sudo apt-get install -y ffmpeg nodejs npm', 'darwin': 'brew install ffmpeg node',
         'win32': 'winget install -e --id Gyan.FFmpeg; winget install -e --id OpenJS.NodeJS.LTS'}


def fail(message):
    raise RuntimeError(message)


VOICE_ONLY_MESSAGE = ('Voice-only mode: Intel Macs and --voice-only installs do not have the pinned Torch/onnxruntime '
                      'video stack or a supported Chrome rendering path. Video build, smoke, stills and render are disabled. '
                      'Use vsp.py voice <project>, vsp.py audio <project>, or scripts/make_voice.py; see the docs.')


def rosetta_translated(system=None, machine=None):
    """Report Rosetta when a macOS x86_64 interpreter is running on Apple Silicon."""
    if (system or sys.platform) != 'darwin' or (machine or platform.machine()).lower() not in ('x86_64', 'amd64'):
        return False
    try:
        return subprocess.check_output(['sysctl', '-n', 'sysctl.proc_translated'],
                                       text=True, stderr=subprocess.DEVNULL).strip() == '1'
    except (OSError, subprocess.CalledProcessError):
        return False


def os_key(system=None, machine=None, release=None):
    system = system or sys.platform
    machine = (machine or platform.machine()).lower()
    if system.startswith('linux'):
        return 'linux64'
    if system == 'win32':
        if machine not in ('amd64', 'x86_64'):
            fail('Windows 10/11 x64 is required.')
        return 'win64'
    if system == 'darwin':
        major = int((release or platform.mac_ver()[0] or '0').split('.')[0])
        if major < 14:
            fail('macOS 14 or newer is required by this pack.')
        if machine in ('arm64', 'aarch64'):
            return 'mac-arm64'
        if machine in ('x86_64', 'amd64'):
            return 'mac-x64'
        fail('Unsupported Mac CPU: ' + machine)
    fail('Unsupported platform: %s %s' % (system, machine))


def voice_only(key=None, forced=False, include_state=True):
    return bool(forced or os.environ.get('VSP_VOICE_ONLY') == '1' or key == 'mac-x64' or
                (include_state and (STATE / 'tier').is_file() and
                 (STATE / 'tier').read_text(encoding='utf-8').strip() == 'voice-only'))


def venv_python(os_name=None):
    return VENV / ('Scripts/python.exe' if (os_name or sys.platform) == 'win32' else 'bin/python')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest, expected):
    dest = Path(dest)
    if dest.is_file() and sha256(dest) == expected:
        print('  cached:', dest.name)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + '.part')
    try:
        with urllib.request.urlopen(url, timeout=60) as src, open(part, 'wb') as out:
            shutil.copyfileobj(src, out)
        if sha256(part) != expected:
            fail('SHA256 mismatch: %s' % url)
        part.replace(dest)
    finally:
        part.unlink(missing_ok=True)
    print('  downloaded and verified:', dest.name)
    return dest


def available_memory_mb(system=None):
    """Best-effort available RAM; None means unknown, never an automatic failure."""
    system = system or sys.platform
    try:
        import psutil
        return int(psutil.virtual_memory().available / 1048576)
    except ImportError:
        pass
    try:
        if system.startswith('linux'):
            import re
            data = Path('/proc/meminfo').read_text(encoding='ascii')
            return int(re.search(r'^MemAvailable:\s+(\d+)', data, re.M).group(1)) // 1024
        if system == 'darwin':
            import re
            page = int(subprocess.check_output(['sysctl', '-n', 'hw.pagesize'], text=True).strip())
            stat = subprocess.check_output(['vm_stat'], text=True)
            counts = {k: int(v.replace('.', '')) for k, v in re.findall(r'^(Pages [^:]+):\s+([\d.]+)', stat, re.M)}
            return page * sum(counts.get(k, 0) for k in ('Pages free', 'Pages inactive', 'Pages speculative')) // 1048576
        if system == 'win32':
            import ctypes
            class Status(ctypes.Structure):
                _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong),
                            ('total_phys', ctypes.c_ulonglong), ('avail_phys', ctypes.c_ulonglong),
                            ('total_page', ctypes.c_ulonglong), ('avail_page', ctypes.c_ulonglong),
                            ('total_virtual', ctypes.c_ulonglong), ('avail_virtual', ctypes.c_ulonglong),
                            ('avail_extended', ctypes.c_ulonglong)]
            status = Status()
            status.length = ctypes.sizeof(Status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return status.avail_phys // 1048576
    except (OSError, ValueError, AttributeError):
        pass
    return None


def system_manager(system=None, which=shutil.which):
    system = system or sys.platform
    if system.startswith('linux') and which('apt-get'):
        return 'apt'
    if system == 'darwin' and which('brew'):
        return 'brew'
    if system == 'win32':
        if which('winget'):
            return 'winget'
        if which('choco'):
            return 'choco'
    return None


def system_commands(missing, manager):
    missing = set(missing)
    if not missing:
        return []
    if manager == 'apt':
        packages = [p for p in ('ffmpeg', 'nodejs', 'npm') if (p == 'ffmpeg' and missing.intersection(('ffmpeg', 'ffprobe'))) or (p in ('nodejs', 'npm') and 'node' in missing)]
        return ['sudo apt-get install -y ' + ' '.join(packages)]
    if manager == 'brew':
        return ['brew install ' + ' '.join(p for p, needed in [('ffmpeg', bool(missing.intersection(('ffmpeg', 'ffprobe')))), ('node', 'node' in missing)] if needed)]
    if manager == 'winget':
        return (['winget install -e --id Gyan.FFmpeg'] if missing.intersection(('ffmpeg', 'ffprobe')) else []) + (['winget install -e --id OpenJS.NodeJS.LTS'] if 'node' in missing else [])
    if manager == 'choco':
        return ['choco install -y ' + ' '.join(p for p, needed in [('ffmpeg', bool(missing.intersection(('ffmpeg', 'ffprobe')))), ('nodejs-lts', 'node' in missing)] if needed)]
    return [HINTS['linux' if sys.platform.startswith('linux') else sys.platform]]


def command_allowed(manager):
    if manager == 'choco':
        return False  # Chocolatey commonly requests UAC; print its command for the operator.
    if manager != 'apt':
        return True
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        return True
    return bool(shutil.which('sudo') and subprocess.run(['sudo', '-n', 'true'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)


def check_system(install=False, dry=False, voice=False):
    sys.path.insert(0, str(ROOT / 'scripts'))
    from vsp_common import tool_path
    required = ('ffmpeg',) if voice else ('ffmpeg', 'ffprobe', 'node')
    missing = [n for n in required if not tool_path(n, required=False)]
    manager = system_manager()
    commands = system_commands(missing, manager)
    for n in required:
        print('%-8s %s' % (n, 'MISSING' if n in missing else 'present'))
    if missing:
        print('Install commands:')
        for c in commands:
            print('  ' + c)
        if not install or dry:
            return False
        if manager is None or not command_allowed(manager):
            fail('System installation needs an interactive administrator step. Run the command above yourself.')
        for c in commands:
            argv = c.split()
            if manager == 'apt' and hasattr(os, 'geteuid') and os.geteuid() == 0:
                argv = argv[1:]
            subprocess.run(argv, check=True)
        return check_system(dry=True, voice=voice)
    from vsp_common import tool_path
    if not voice:
        node = tool_path('node')
        version = subprocess.check_output([node, '--version'], text=True).strip().lstrip('v')
        if int(version.split('.')[0]) < 18:
            print('Node >=18 required; found ' + version + '. ' + HINTS['linux' if sys.platform.startswith('linux') else sys.platform])
            return False if dry else fail('Node >=18 required')
    encoders = subprocess.check_output([tool_path('ffmpeg'), '-hide_banner', '-encoders'], text=True, stderr=subprocess.STDOUT)
    if not voice and 'libx264' not in encoders:
        print('ffmpeg: missing libx264. ' + HINTS['linux' if sys.platform.startswith('linux') else sys.platform])
        return False if dry else fail('ffmpeg has no libx264 encoder')
    if dry:
        print('Would run:')
        if not shutil.which('uv'): print('  %s -m pip install --target .vsp-state/uv-bootstrap uv==0.13.7' % sys.executable)
        print('  uv venv --python 3.13 .venv')
        if voice:
            print('  uv pip sync --python .venv/%s requirements-voice.lock.txt' % ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python'))
            print('  download and SHA256-check pinned Kokoro models and Inter/Caveat fonts; link skills unless --no-link')
        else:
            print('  uv pip sync --python .venv/%s requirements.lock.txt --extra-index-url https://download.pytorch.org/whl/cpu' % ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python'))
            print('  download and SHA256-check pinned Kokoro models, Inter/Caveat fonts and Chrome-for-Testing %s' % CHROME_VERSION)
            print('  prefetch MMS_FA unless --skip-aligner; link skills unless --no-link')
    return True


def bootstrap_uv():
    uv = shutil.which('uv')
    if uv:
        return uv
    local = STATE / 'uv-bootstrap'
    candidates = ([local / 'Scripts' / 'uv.exe', local / 'bin' / 'uv.exe'] if sys.platform == 'win32' else
                  [local / 'bin' / 'uv'])
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    print('uv missing; installing pinned uv==0.13.7 into .vsp-state/uv-bootstrap')
    try:
        local.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', '--target', str(local), 'uv==0.13.7'], check=True)
    except (OSError, subprocess.CalledProcessError):
        print('uv bootstrap unavailable; trying a local Python 3.13/3.12 venv. Install uv for managed Python: macOS brew install uv; Windows winget install --id astral-sh.uv -e; Linux python3 -m pip install --user uv==0.13.7.')
        return None
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def fallback_python():
    candidates = ([['py', '-3.13'], ['py', '-3.12']] if sys.platform == 'win32' else
                  [['python3.13'], ['python3.12']])
    for cmd in candidates:
        try:
            if subprocess.run(cmd + ['-c', 'import sys; sys.exit(0 if (3,12)<=sys.version_info[:2]<=(3,13) else 1)'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                return cmd
        except OSError:
            pass
    fail('Python 3.12 or 3.13 is required without uv. Windows: py -3.13 or py -3.12; macOS/Linux: python3.13 or python3.12. Install uv to download Python 3.13 automatically.')


def create_venv(uv):
    py = venv_python()
    if py.exists():
        result = subprocess.run([str(py), '-c', 'import sys; sys.exit(0 if (3,12)<=sys.version_info[:2]<=(3,13) else 1)'])
        if result.returncode:
            fail('Existing .venv uses unsupported Python. Remove .venv and rerun.')
    else:
        if uv: subprocess.run([uv, 'venv', '--python', '3.13', str(VENV)], check=True)
        else: subprocess.run(fallback_python() + ['-m', 'venv', str(VENV)], check=True)
    STATE.mkdir(exist_ok=True)
    (STATE / 'python').write_text(str(py) + '\n', encoding='utf-8')
    return py


def install_chrome(key):
    sha, rel = CHROME[key]
    folder = CACHE / 'chrome' / CHROME_VERSION
    binary = folder / rel
    if binary.exists():
        return binary
    zipname = 'chrome-headless-shell-' + key + '.zip'
    url = 'https://storage.googleapis.com/chrome-for-testing-public/%s/%s/%s' % (CHROME_VERSION, key, zipname)
    archive = download(url, CACHE / 'chrome' / zipname, sha)
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        z.extractall(folder)
    if key != 'win64':
        binary.chmod(binary.stat().st_mode | 0o755)
    archive.unlink()
    return binary


def run_env():
    return {**os.environ, 'VSP_CACHE': str(CACHE), 'TORCH_HOME': str(CACHE / 'torch'), 'PYTHONUTF8': '1'}


def run(*argv):
    subprocess.run([str(a) for a in argv], cwd=ROOT, env=run_env(), check=True)


def install(a):
    key = os_key()
    voice = voice_only(key, a.voice_only, include_state=False)
    if voice:
        print(VOICE_ONLY_MESSAGE)
        if key == 'mac-x64' and rosetta_translated():
            print('Rosetta detected: this x86_64 Python process uses the voice-only tier.')
    if a.check:
        return 0 if check_system(dry=True, voice=voice) else 1
    ram = available_memory_mb()
    print('Available RAM:', str(ram) + ' MB' if ram is not None else 'unknown (continuing)')
    free_gb = shutil.disk_usage(ROOT).free / (1024**3)
    if free_gb < 4: print('WARN: %.1f GB free; full install may need about 4 GB.' % free_gb)
    if not check_system(a.install_system, voice=voice):
        return 1
    uv = bootstrap_uv()
    py = create_venv(uv)
    tier = STATE / 'tier'
    if uv:
        if voice:
            run(uv, 'pip', 'sync', '--python', py, ROOT / 'requirements-voice.lock.txt')
        else:
            run(uv, 'pip', 'sync', '--python', py, ROOT / 'requirements.lock.txt',
                '--extra-index-url', 'https://download.pytorch.org/whl/cpu')
    else:
        run(py, '-m', 'pip', 'install', '-r', ROOT / ('requirements-voice.lock.txt' if voice else 'requirements.txt'))
        if not voice:
            cmd = [py, '-m', 'pip', 'install', '-r', ROOT / 'requirements-torch.txt']
            if key != 'mac-arm64': cmd += ['--index-url', 'https://download.pytorch.org/whl/cpu']
            run(*cmd)
    if voice: tier.write_text('voice-only\n', encoding='utf-8')
    else: tier.unlink(missing_ok=True)
    for name, sha in MODELS:
        download(MODEL_BASE + '/' + name, CACHE / 'models' / name, sha)
    for name, rel, sha in FONTS:
        download('https://raw.githubusercontent.com/google/fonts/' + FONT_COMMIT + '/' + rel, CACHE / 'fonts' / name, sha)
    if not voice and not a.skip_aligner:
        run(py, '-c', 'import torchaudio; torchaudio.pipelines.MMS_FA.get_model(dl_kwargs={"progress": False})')
        if sha256(CACHE / 'torch/hub/checkpoints/model.pt') != MMS_SHA:
            fail('MMS_FA model checksum mismatch')
    if not voice and not a.no_chrome:
        # A pinned Chrome is installed for reproducible first use; existing cached copy is reused.
        install_chrome(key)
    optional = []
    if a.with_maps: optional += ['d3-geo@3.1.1', 'topojson-client@3.1.0', 'world-atlas@2.0.2']
    if a.with_puppeteer: optional += ['puppeteer-core@25.16.0']
    if a.with_hyperframes: optional += ['hyperframes@0.8.217']
    if a.with_remotion: optional += ['remotion@4.0.539', '@remotion/cli@4.0.539']
    if optional and voice:
        print('Optional video npm packages skipped in voice-only mode.')
    elif optional:
        sys.path.insert(0, str(ROOT / 'scripts'))
        from vsp_common import tool_path
        npm = shutil.which('npm') or ('npm.cmd' if sys.platform == 'win32' else 'npm')
        run(npm, 'install', '--no-audit', '--no-fund', '--save-exact', '--prefix', ROOT, *optional)
    if a.with_blender:
        sys.path.insert(0, str(ROOT / 'scripts'))
        from vsp_common import tool_path
        print('Blender:', tool_path('blender', required=False) or 'optional; install from blender.org')
    if not a.no_link:
        link_skills(a)
    print('Install complete. Next: python vsp.py verify; ' + ('python vsp.py voice <project>' if voice else 'python vsp.py smoke'))
    return 0


def link_skills(a):
    src = ROOT / 'video-making'
    targets = []
    if a.skills_dir:
        targets = [Path(a.skills_dir)]
    else:
        for agent in ('codex', 'claude'):
            if getattr(a, 'link_' + agent, False) or (Path.home() / ('.' + agent)).exists():
                targets.append(Path.home() / ('.' + agent) / 'skills')
    if not targets:
        print('No agent skills directory found; use --skills-dir DIR to link explicitly.')
    for base in targets:
        base.mkdir(parents=True, exist_ok=True)
        dest = base / 'video-making'
        if dest.is_symlink():
            if dest.resolve() == src:
                print('Already linked:', dest)
                continue
            old = dest.resolve()
            if not a.relink or (old.exists() and not (old / 'SKILL.md').exists()):
                print('Kept existing link:', dest)
                continue
            dest.unlink()
        elif dest.exists():
            if not (dest / '.vsp-copy').exists():
                print('Kept existing directory:', dest)
                continue
            shutil.rmtree(dest)
        if not a.copy and sys.platform != 'win32':
            try:
                dest.symlink_to(src, target_is_directory=True)
                print('Linked:', dest)
                continue
            except OSError:
                pass
        shutil.copytree(src, dest)
        (dest / 'PACK_ROOT').write_text(str(ROOT) + '\n', encoding='utf-8')
        (dest / '.vsp-copy').write_text('copied by vsp.py\n', encoding='utf-8')
        print('Copied:', dest)
    return 0


def verify(a):
    voice = voice_only(os_key(), a.voice_only)
    py = venv_python()
    if not py.exists():
        fail('Missing .venv. Run install first.')
    rows = []
    def check(name, argv):
        p = subprocess.run([str(x) for x in argv], cwd=ROOT, env=run_env(), capture_output=True, text=True)
        rows.append((name, p.returncode == 0, (p.stdout or p.stderr).strip().splitlines()[-1:] or ['']))
    check('Python 3.12-3.13', [py, '-c', 'import sys; assert (3,12)<=sys.version_info[:2]<=(3,13)'])
    modules = 'import kokoro_onnx,onnxruntime,numpy,soundfile,PIL'
    if not voice: modules += ',torch,torchaudio'
    check('Python packages', [py, '-c', modules])
    sys.path.insert(0, str(ROOT / 'scripts'))
    from vsp_common import tool_path
    if not voice: check('Node >=18', [tool_path('node'), '-e', 'if (+process.versions.node.split(".")[0]<18) process.exit(1)'])
    if voice:
        check('ffmpeg audio mix', [tool_path('ffmpeg'), '-hide_banner', '-loglevel', 'error', '-f', 'lavfi',
                                   '-i', 'sine=d=0.2', '-af', 'loudnorm=I=-14:TP=-1.5', '-f', 'null', '-'])
    with tempfile.TemporaryDirectory(prefix='vsp-verify-') as td:
        mp4 = Path(td) / 'test.mp4'
        wav = Path(td) / 'voice.wav'
        if not voice:
            check('ffmpeg libx264+aac', [tool_path('ffmpeg'), '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=64x64:r=30:d=0.5', '-f', 'lavfi', '-i', 'sine=d=0.5', '-c:v', 'libx264', '-c:a', 'aac', '-shortest', '-y', mp4])
        if mp4.exists() and not voice:
            check('ffprobe', [tool_path('ffprobe'), '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', mp4])
            check('loudnorm filter', [tool_path('ffmpeg'), '-hide_banner', '-nostats', '-i', mp4, '-af', 'loudnorm=I=-14:TP=-1.5:print_format=json', '-f', 'null', '-'])
        speech = ('from kokoro_onnx import Kokoro; import numpy as np, soundfile as sf; '
                  'k=Kokoro(%r,%r); a,sr=k.create("Testing one two three.",voice="af_heart",lang="en-us",speed=1.0); '
                  'a=np.asarray(a); assert sr==24000 and len(a)>sr*0.6 and np.abs(a).max()>0.05; sf.write(%r,a,sr)') % (
                      str(CACHE / 'models/kokoro-v1.0.int8.onnx'), str(CACHE / 'models/voices-v1.0.bin'), str(wav))
        check('Kokoro speaks', [py, '-c', speech])
        if wav.exists() and not voice and not a.skip_aligner:
            alignment = ('import torch,torchaudio,soundfile as sf; a,sr=sf.read(%r,dtype="float32"); '
                         'x=torchaudio.functional.resample(torch.from_numpy(a),sr,16000); b=torchaudio.pipelines.MMS_FA; '
                         'm=b.get_model(); tok=b.get_tokenizer(); al=b.get_aligner(); e,_=m(x.unsqueeze(0)); '
                         'sp=al(e[0],tok(["testing","one","two","three"])); '
                         'assert len(sp)==4') % str(wav)
            check('MMS_FA alignment', [py, '-c', alignment])
    for name, sha in MODELS:
        path = CACHE / 'models' / name
        rows.append((name, path.exists() and sha256(path) == sha, ['checksum']))
    if not voice and not a.skip_aligner:
        path = CACHE / 'torch/hub/checkpoints/model.pt'
        rows.append(('MMS_FA', path.exists() and sha256(path) == MMS_SHA, ['checksum']))
    for name, _, sha in FONTS:
        path = CACHE / 'fonts' / name
        rows.append((name, path.exists() and sha256(path) == sha, ['checksum']))
    free_gb = shutil.disk_usage(ROOT).free / (1024**3)
    rows.append(('disk space', free_gb >= 1, ['%.1f GB free' % free_gb]))
    ram = available_memory_mb()
    if ram is not None: rows.append(('available RAM', ram >= 1500, ['%d MB' % ram]))
    else: print('WARN: available RAM could not be measured')
    if not voice: check('Chrome renders', [tool_path('node'), ROOT / 'lib/selftest.mjs'])
    check('router', [py, ROOT / 'scripts/router_test.py'])
    check('links', [py, ROOT / 'scripts/check_links.py'])
    for name, ok, detail in rows: print('%-23s %-4s %s' % (name, 'PASS' if ok else 'FAIL', detail[0][:100]))
    good = all(ok for _, ok, _ in rows)
    print('verify: all required components PASS' if good else 'verify: FAIL')
    return 0 if good else 1


def build(a):
    if voice_only(os_key()): fail(VOICE_ONLY_MESSAGE)
    py = venv_python()
    if not py.exists(): fail('Install first: python vsp.py install')
    sys.path.insert(0, str(ROOT / 'scripts'))
    from vsp_common import tool_path
    ram = available_memory_mb()
    if ram is not None and ram < 1500: print('WARN: only %d MB RAM available; heavy stages may fail.' % ram)
    project = Path(a.project).resolve()
    if not (project / 'project.json').exists(): fail('project.json not found: ' + str(project))
    force = ['--force'] if a.force else []
    steps = [('voice', [py, ROOT / 'scripts/make_voice.py', '--project', project, *force]),
             ('align', [py, ROOT / 'scripts/align_words.py', '--project', project, *force]),
             ('audio', [py, ROOT / 'scripts/make_audio.py', '--project', project, *force]),
             ('stills', [tool_path('node'), ROOT / 'scripts/stills.mjs', '--project', project, '--scan']),
             ('render', [tool_path('node'), ROOT / 'scripts/render.mjs', '--project', project]),
             ('subtitles', [tool_path('node'), ROOT / 'scripts/subtitle_qc.mjs', '--project', project]),
             ('qc', [py, ROOT / 'scripts/qc_final.py', '--project', project])]
    if a.skip_aligner:
        steps = [x for x in steps if x[0] not in ('align', 'subtitles')]
    for name, cmd in steps:
        print('==', name, flush=True)
        run(*cmd)
    return 0


def smoke(a):
    if voice_only(os_key()): fail(VOICE_ONLY_MESSAGE)
    ram = available_memory_mb()
    if ram is not None and ram < 1500: print('WARN: only %d MB RAM available; heavy stages may fail.' % ram)
    out = ROOT / 'smoke-test/out'
    if a.clean and out.exists(): shutil.rmtree(out)
    project = out / 'project'
    project.mkdir(parents=True, exist_ok=True)
    if not (project / 'project.json').exists():
        for name in ('project.json', 'index.html'):
            shutil.copy2(ROOT / 'examples/hello-world' / name, project / name)
        (out / 'PROGRESS.md').write_text('# PROGRESS (smoke test)\n', encoding='utf-8')
    py = venv_python()
    if not py.exists(): fail('Install first: python vsp.py install')
    sys.path.insert(0, str(ROOT / 'scripts'))
    from vsp_common import tool_path
    steps = [('voice', [py, ROOT / 'scripts/make_voice.py', '--project', project]),
             ('align', [py, ROOT / 'scripts/align_words.py', '--project', project]),
             ('audio', [py, ROOT / 'scripts/make_audio.py', '--project', project]),
             ('stills', [tool_path('node'), ROOT / 'scripts/stills.mjs', '--project', project, '--n', '6', '--scan']),
             ('render', [tool_path('node'), ROOT / 'scripts/render.mjs', '--project', project]),
             ('subtitles', [tool_path('node'), ROOT / 'scripts/subtitle_qc.mjs', '--project', project]),
             ('qc', [py, ROOT / 'scripts/qc_final.py', '--project', project])]
    if a.skip_aligner: steps = [x for x in steps if x[0] not in ('align', 'subtitles')]
    for name, cmd in steps:
        marker = out / ('.done-' + name)
        if marker.exists():
            print('==', name, 'already done')
            continue
        run(*cmd)
        marker.touch()
        with (out / 'PROGRESS.md').open('a', encoding='utf-8') as log:
            log.write('\n- %s %s done' % (time.strftime('%Y-%m-%d %H:%M:%S'), name))
    result = json.loads((project / 'out/qc/qc_final.json').read_text(encoding='utf-8'))
    if not result.get('pass'): fail('Smoke QC did not pass')
    print('SMOKE TEST PASS')
    return 0


def new(a):
    dest = Path(a.project).resolve()
    if a.motion:
        source = ROOT / 'video-making/components/motion-studio/templates'
        dest.mkdir(parents=True, exist_ok=True)
        for sub in ('assets', 'audio', 'out'): (dest / sub).mkdir(exist_ok=True)
        for name in ('index.html', 'mslib.js', 'beats.json'):
            if not (dest / name).exists(): shutil.copy2(source / name, dest / name)
        w, h = (1080, 1920) if a.vertical else (1920, 1080)
        if a.vertical:
            p = dest / 'index.html'; p.write_text(p.read_text(encoding='utf-8').replace('const W = 1920, H = 1080;', 'const W = 1080, H = 1920;'), encoding='utf-8')
            p = dest / 'beats.json'; p.write_text(p.read_text(encoding='utf-8').replace('"size": [1920, 1080]', '"size": [1080, 1920]'), encoding='utf-8')
        cfg = {'name': dest.name, 'width': w, 'height': h, 'fps': 60, 'duration': 3.0, 'page': 'index.html',
               'render': {'part_frames': 120, 'crf': 18, 'threads': 2, 'hash_dirs': ['assets']},
               'audio': {'lufs': -14, 'true_peak': -1.5}, 'qc': {'freeze_s': 0.75}, 'output': 'out/' + dest.name + '.mp4'}
        if not (dest / 'project.json').exists(): (dest / 'project.json').write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8')
        if not (dest / 'CHANGELOG.md').exists(): (dest / 'CHANGELOG.md').write_text('# Changelog\n\n## V1\n- first render\n', encoding='utf-8')
    else:
        if (dest / 'project.json').exists(): fail('project.json already exists: ' + str(dest))
        for sub in ('audio', 'align', 'out', 'assets'): (dest / sub).mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / 'examples/hello-world/index.html', dest / 'index.html')
        cfg = json.loads((ROOT / 'examples/hello-world/project.json').read_text(encoding='utf-8'))
        cfg['name'] = dest.name
        cfg['output'] = 'out/' + dest.name + '.mp4'
        (dest / 'project.json').write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8')
        (dest / 'PROGRESS.md').write_text('# PROGRESS\n\nProject scaffolded from examples/hello-world.\n', encoding='utf-8')
    print('Scaffolded', dest)
    return 0


def voice_or_audio(a):
    py = venv_python()
    if not py.exists(): fail('Install first: python vsp.py install')
    script = 'make_voice.py' if a.command == 'voice' else 'make_audio.py'
    run(py, ROOT / 'scripts' / script, '--project', Path(a.project).resolve(), *(['--force'] if a.force else []))
    return 0


def main():
    parser = argparse.ArgumentParser(description='Video skill pack installer and pipeline (Python 3.12-3.13 runtime).',
                                     epilog='Use "vsp.py install --help" for installer options.')
    sub = parser.add_subparsers(dest='command')
    ins = sub.add_parser('install', help='install pinned dependencies and assets')
    ins.add_argument('--check', '--dry-run', action='store_true', help='report missing tools and planned commands; change nothing')
    ins.add_argument('--install-system', '--apt', action='store_true', help='install missing system tools without a password prompt')
    for flag in ('with-chrome', 'no-chrome', 'with-maps', 'with-puppeteer', 'with-hyperframes', 'with-remotion', 'with-blender', 'skip-aligner', 'voice-only', 'no-link', 'link-codex', 'link-claude', 'copy', 'relink'):
        ins.add_argument('--' + flag, action='store_true')
    ins.add_argument('--skills-dir')
    check_parser = sub.add_parser('check', help='alias for install --check')
    check_parser.add_argument('--voice-only', action='store_true')
    ver = sub.add_parser('verify', help='exercise installed components')
    ver.add_argument('--skip-aligner', action='store_true'); ver.add_argument('--voice-only', action='store_true')
    link = sub.add_parser('link-skills', help='link or copy the skill into agent directories')
    for flag in ('link-codex', 'link-claude', 'copy', 'relink'): link.add_argument('--' + flag, action='store_true')
    link.add_argument('--skills-dir')
    sub.add_parser('uninstall-notes', help='show installed paths; remove nothing')
    b = sub.add_parser('build', help='run the seven-stage pipeline')
    b.add_argument('project'); b.add_argument('--force', action='store_true'); b.add_argument('--skip-aligner', action='store_true')
    sm = sub.add_parser('smoke', help='run the sample end-to-end')
    sm.add_argument('--clean', action='store_true'); sm.add_argument('--skip-aligner', action='store_true')
    n = sub.add_parser('new', help='scaffold a project')
    n.add_argument('project'); n.add_argument('--vertical', action='store_true'); n.add_argument('--motion', action='store_true')
    for command in ('voice', 'audio'):
        p = sub.add_parser(command, help='run the voice-only narration or audio mix step')
        p.add_argument('project'); p.add_argument('--force', action='store_true')
    argv = sys.argv[1:]
    if not argv or (argv[0].startswith('-') and argv[0] not in ('-h', '--help')):
        argv = ['install', *argv]
    a = parser.parse_args(argv)
    if a.command == 'check': return 0 if check_system(dry=True, voice=voice_only(os_key(), a.voice_only)) else 1
    if a.command == 'uninstall-notes':
        for p in (VENV, STATE, ROOT / 'node_modules', CACHE): print(p)
        print('Remove these paths manually if desired; linked skills are in ~/.codex/skills or ~/.claude/skills.')
        return 0
    if a.command == 'link-skills': return link_skills(a)
    if a.command == 'new': return new(a)
    if a.command in ('voice', 'audio'): return voice_or_audio(a)
    if a.command in ('install', 'verify', 'build', 'smoke'):
        if sys.version_info < (3, 8): fail('Bootstrap Python 3.8+ required; install with uv, then use Python 3.13.')
        if a.command == 'install': return install(a)
        if a.command == 'verify': return verify(a)
        if a.command == 'build': return build(a)
        return smoke(a)
    return 0


if __name__ == '__main__':
    try: sys.exit(main())
    except (RuntimeError, subprocess.CalledProcessError, OSError, ValueError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
