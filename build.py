import PyInstaller.__main__
import sys
import os
import tempfile

version_info = """
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
#
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 2),
    prodvers=(1, 0, 0, 2),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'funDAVEover'),
        StringStruct(u'FileDescription', u'Морской бой - сетевая игра'),
        StringStruct(u'FileVersion', u'1.0.0.2'),
        StringStruct(u'InternalName', u'SeaBattle'),
        StringStruct(u'LegalCopyright', u'Copyright 2026 funDAVEover'),
        StringStruct(u'OriginalFilename', u'SeaBattle.exe'),
        StringStruct(u'ProductName', u'SeaBattle'),
        StringStruct(u'ProductVersion', u'1.0.0.2')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [0x409, 1200])])
  ]
)
"""

version_file = 'version_info.txt'
with open(version_file, 'w', encoding='utf-8') as f:
    f.write(version_info)

params = [
    'main.py',
    '--name=SeaBattle',
    '--onefile',
    '--windowed',
    f'--add-data=config.py{";" if sys.platform.startswith("win") else ":"}.',
    f'--add-data=theme.py{";" if sys.platform.startswith("win") else ":"}.',
    f'--add-data=enums.py{";" if sys.platform.startswith("win") else ":"}.',
    f'--add-data=models.py{";" if sys.platform.startswith("win") else ":"}.',
    f'--add-data=game_field.py{";" if sys.platform.startswith("win") else ":"}.',
    f'--add-data=ui.py{";" if sys.platform.startswith("win") else ":"}.',
    f'--add-data=network.py{";" if sys.platform.startswith("win") else ":"}.',
    f'--add-data=game.py{";" if sys.platform.startswith("win") else ":"}.',
    '--hidden-import=pygame',
    '--hidden-import=queue',
    '--hidden-import=threading',
    '--hidden-import=socket',
    '--hidden-import=json',
    '--hidden-import=random',
    '--hidden-import=collections',
    '--hidden-import=enum',
    '--hidden-import=dataclasses',
    '--hidden-import=typing',
    '--collect-all=pygame',
    '--noconfirm',
]

if sys.platform.startswith('win'):
    params.append(f'--version-file={version_file}')

if __name__ == '__main__':
    print("\nНачинаю сборку...\n")
    
    try:
        PyInstaller.__main__.run(params)
        print("Сборка завершена успешно!")

    except Exception as e:
        print(f"\nОшибка при сборке: {e}")
    finally:
        if os.path.exists(version_file):
            os.remove(version_file)