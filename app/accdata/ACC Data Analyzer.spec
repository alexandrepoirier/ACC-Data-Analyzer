# -*- mode: python -*-
a = Analysis(['ACC Data Analyzer.py'],
             pathex=['/Volumes/DOCUMENTS/UdeM/Creation musicale en langage python 2/Projet-app/accdata'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='ACC Data Analyzer',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='icn_main.icns')
app = BUNDLE(exe,
             name='ACC Data Analyzer.app',
             icon='icn_main.icns')
