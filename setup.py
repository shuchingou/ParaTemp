from distutils.core import setup
import versioneer

setup(
    name='ParaTemp',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=['paratemp'],
    url='https://github.com/theavey/ParaTemp',
    license='Apache License 2.0',
    author='Thomas Heavey',
    author_email='thomasjheavey@gmail.com',
    description='Scripts for molecular dynamics analysis and parallel tempering in GROMACS'
)