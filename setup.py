from setuptools import setup

setup(
    name='vcutter',
    version='1.0',
    py_modules=['vcutter'],
    install_requires=[
        'yt-dlp[default]',
        'argparse'
    ],
    entry_points={
        'console_scripts': [
            'vcutter = vcutter:main',
        ],
    },
)
