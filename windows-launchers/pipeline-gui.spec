# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['..\\pipeline-gui.py'],
    pathex=['..'],
    binaries=[],
    datas=[
        ('..\\start-pipeline.sh', '_data'),
        ('..\\stop-pipeline.sh', '_data'),
        ('..\\watcher_core.py', '_data'),
        ('..\\pipeline_gui\\token_usage_shared.py', '_data'),
        ('..\\pipeline_gui\\token_dashboard_shared.py', '_data'),
        ('..\\_data', '_data'),
        ('..\\schemas\\agent_manifest.schema.json', '_data/schemas'),
        ('..\\schemas\\job_state.schema.json', '_data/schemas'),
        ('..\\.pipeline\\README.md', '_data/.pipeline'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pipeline-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
