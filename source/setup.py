# Examples of setup
#
# python setup.py install
# python setup.py install --prefix=/opt/python-2.3
# python setup.py install --home=~
#
# Some times you'll have to add a file called pypar.pth
# containing the word pypar to site-packages
#
# See http://docs.python.org/dist/pure-pkg.html for more on distutils

# FIXME: Now mpiext.c and pypar.py are assumed to be in this directory.
# Maybe, we should put them in the default package directory, pypar.
# The repository structure would then be
# 
# pypar
#     demos
#     documentation
#     source
#          pypar

from distutils.core import setup, Extension

# FIXME (Ole): This works, but I don't know how to use it
# Generate Python EGG if possible.
#try:
#   from setuptools import setup, Extension
#except ImportError:
#   pass

import distutils.sysconfig
import distutils.debug
import os, sys
import popen2 # FIXME: Replace with subprocess - http://docs.python.org/library/subprocess.html#replacing-older-functions-with-the-subprocess-module
import string
import tempfile
import numpy
from __metadata__ import __version__, __date__, __author__


def setup_compiler():
    distutils.sysconfig.get_config_vars()
    config_vars = distutils.sysconfig._config_vars
    
    if sys.platform == 'sunos5':
        config_vars['LDSHARED'] = 'gcc -G'
        config_vars['CCSHARED'] = ''
        

def uniq_arr(arr):
    """Remove repeated values from an array and return new array."""
    ret = []
    for i in arr:
        if i not in ret:
            ret.append(i)
    return ret


def _run_command(cmd):
    """Get mpi compile command
    """
    out_file, in_file, err_file = popen2.popen3(cmd)
    output = out_file.read() + err_file.read()
    out_file.close()
    in_file.close()
    err_file.close()
    # Need this hack to get the exit status
    out_file = os.popen(cmd)
    if out_file.close():
        # Close returns exit status of command.
        return ""
    else:
        # No errors, out_file.close() returns None.
        return output


def _get_mpi_cmd():
    """Returns the output of the command used to compile using
    mpicc."""

    # LAM/OPENMPI/MPICH2
    output = _run_command('mpicc -show')
    if output:
        return output
    else:
        # Try to get mpi command anyway

        if sys.platform=='win32': # From Simon Frost
            # This didn't work on my machine (Vladimir Lazunin on April 7, 2009)
            # output = "gcc -L$MPICH_DIR\SDK.gcc\lib -lmpich -I$MPICH_DIR\SDK.gcc\include"

            # "MPICH_DIR" must be set manually in environment variables
            mpi_dir = os.getenv("MPICH_DIR")

            # for MPICH2
            sdk_prefix = mpi_dir
            lib_name = "mpi"

            # for MPICH1
            # FIXME (Ole): Can this be phased out?
            if os.path.exists(sdk_prefix + "\\SDK"):
                sdk_prefix += "\\SDK"
                lib_name = "mpich"
            output = "gcc -L%(sdk_prefix)s\lib -l%(lib_name)s -I%(sdk_prefix)s\include" % {"sdk_prefix" : sdk_prefix, "lib_name" : lib_name}
        else:
            output = "cc -L/usr/opt/mpi -lmpi -lelan"

           
        return output



def get_mpi_flags():
    output = _get_mpi_cmd()
    if not output:
        msg = 'Could not get mpi compile command'
        raise Exception(msg)

    print output


    # Now get the include, library dirs and the libs to link with.
    flags = string.split(output)
    flags = uniq_arr(flags) # Remove repeated values.
    inc_dirs = []
    lib_dirs = []
    libs = []
    def_macros = []
    undef_macros = []
    for f in flags:
        if f[:2] == '-I':
            inc_dirs.append(f[2:])
        elif f[:2] == '-L':
            lib_dirs.append(f[2:])
        elif f[:2] == '-l' and f[-1] != "'": # Patched by Michael McKerns July 2009
            libs.append(f[2:])
        elif f[:2] == '-U':
            undef_macros.append(f[2:])
        elif f[:2] == '-D':
            tmp = string.split(f[2:], '=')
            if len(tmp) == 1:
                def_macros.append((tmp[0], None))
            else:
                def_macros.append(tuple(tmp))
    return {'inc_dirs': inc_dirs, 'lib_dirs': lib_dirs, 'libs':libs,
            'def_macros': def_macros, 'undef_macros': undef_macros}


if __name__ == '__main__':
    setup_compiler()
    
    mpi_flags = get_mpi_flags()
    mpi_flags['inc_dirs'].append(numpy.get_include())


    if os.name == 'posix' and os.uname()[4] == 'x86_64':
        # Extra flags for 64 bit architectures    
        extra_compile_args = ['-fPIC']
    else:
        extra_compile_args = None



    setup(name='Pypar',
          version=__version__,
          description='Pypar - Parallel Python',
          long_description='Pypar - Parallel Python, no-frills MPI interface',
          author=__author__,
          author_email='ole.moller.nielsen@gmail.com',
          url='http://sourceforge.net/projects/pypar',
          package_dir = {'pypar': ''}, # Use files in this dirctory 
          packages  = ['pypar'],
          ext_modules = [Extension('pypar.mpiext',
                                   ['mpiext.c'], 
                                   include_dirs=mpi_flags['inc_dirs'],
                                   library_dirs=mpi_flags['lib_dirs'],
                                   libraries=mpi_flags['libs'],
                                   define_macros=mpi_flags['def_macros'],
                                   undef_macros=mpi_flags['undef_macros'],
                                   extra_compile_args=extra_compile_args)]
         )
