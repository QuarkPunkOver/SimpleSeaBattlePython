import PyInstaller.__main__
import sys
import os

params = [
    'main.py',
    '--name=SeaBattle',
    '--onefile',
    '--windowed',
    '--add-data=config.py;.' if sys.platform.startswith('win') else '--add-data=config.py:.',
    '--add-data=theme.py;.' if sys.platform.startswith('win') else '--add-data=theme.py:.',
    '--add-data=enums.py;.' if sys.platform.startswith('win') else '--add-data=enums.py:.',
    '--add-data=models.py;.' if sys.platform.startswith('win') else '--add-data=models.py:.',
    '--add-data=game_field.py;.' if sys.platform.startswith('win') else '--add-data=game_field.py:.',
    '--add-data=ui.py;.' if sys.platform.startswith('win') else '--add-data=ui.py:.',
    '--add-data=network.py;.' if sys.platform.startswith('win') else '--add-data=network.py:.',
    '--add-data=game.py;.' if sys.platform.startswith('win') else '--add-data=game.py:.',
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
    
    '--company=funDAVEover',
    '--copyright=Copyright 2026 funDAVEover',
    '--file-description=Морской бой',
    '--product-name=SeaBattle',
    '--version=1.0.0.0',
]

if __name__ == '__main__':
    print("\nНачинаю сборку...\n")
    
    PyInstaller.__main__.run(params)

    print("Сборка завершена!")