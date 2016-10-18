from setuptools import setup

# name is the package name in pip, should be lower case and not conflict with existing packages
# packages are code source

setup(name='astro_simon',
      version='0.1',
      description='A simulation monitor for astrophysical N-body simulations',
      url='https://github.com/maxwelltsai/SiMon',
      author='Maxwell Cai, Penny Qian',
      author_email='pennyqxr@gmail.com',
      license='',
      packages=['SiMon'],
      zip_safe=False)