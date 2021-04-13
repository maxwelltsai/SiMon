from setuptools import setup, find_packages

# name is the package name in pip, should be lower case and not conflict with existing packages
# packages are code source

setup(name='astrosimon',
      version='0.8.5',
      description='Simulation Monitor for computational astrophysics',
      url='https://github.com/maxwelltsai/SiMon',
      author='Maxwell Cai, Penny Qian',
      author_email='maxwellemail@gmail.com',
      license='BSD 2-Clause',
      packages=find_packages(),
      zip_safe=False,
      install_requires=['python-daemon', 'numpy'],
      entry_points={'console_scripts': ['simon = SiMon.simon:main'], },
      )
