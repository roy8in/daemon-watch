from setuptools import setup

APP = ['daemon_watch.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
        'CFBundleName': 'DaemonWatch',
        'CFBundleDisplayName': 'Daemon Watch',
        'CFBundleIdentifier': "com.local.osx.daemonwatch",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
    },
    'packages': ['rumps', 'cron_descriptor'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
