'''
To create the wheel run - python setup.py bdist_wheel
'''

from setuptools import setup
import os

packages = []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('lca_disclosures'):
    # Ignore dirnames that start with '.'
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


my_package_files = []
#my_package_files.extend(package_files(os.path.join('lcopt', 'assets')))
#my_package_files.extend(package_files(os.path.join('lcopt', 'static')))
#my_package_files.extend(package_files(os.path.join('lcopt', 'templates')))
#my_package_files.extend(package_files(os.path.join('lcopt', 'bin')))
#print(my_package_files)

setup(
    name='lca_disclosures',
    version="0.1.0",
    packages=packages,
    author="P. James Joyce",
    author_email="pjamesjoyce@gmail.com",
    license=open('LICENSE').read(),
    package_data={'lca_disclosures': my_package_files},
    #entry_points = {
    #    'console_scripts': [
    #    ]
    #},
    #install_requires=[
    #],
    include_package_data=True, 
    url="https://github.com/pjamesjoyce/lca_disclosures/",
    download_url="https://github.com/pjamesjoyce/lca_disclosures/archive/0.1.0.tar.gz",
    long_description=open('README.md').read(),
    description='Python based tools for working with LCA foreground model disclosures',
    keywords=['LCA', 'Life Cycle Assessment', 'Foreground system', 'Background system', 'Foreground model', 'Fully parameterised'],
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Visualization',
    ],
)

# Also consider:
# http://code.activestate.com/recipes/577025-loggingwebmonitor-a-central-logging-server-and-mon/
