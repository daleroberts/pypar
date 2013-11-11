#!/usr/bin/env python

from distutils.core import setup, Extension
import distutils.unixccompiler
import sys
import os
import subprocess
import numpy
import shlex


os.environ["CC"] = 'mpicc'


class MPICCompiler(distutils.unixccompiler.UnixCCompiler):
    __set_executable = distutils.unixccompiler.UnixCCompiler.set_executable

    def set_executable(self, key, value):
        if key == 'linker_so' and type(value) == str:
            value = 'mpicc ' + ' '.join(value.split()[1:])

        return self.__set_executable(key, value)

distutils.unixccompiler.UnixCCompiler = MPICCompiler


def get_mpi_flags():
    output = subprocess.check_output(
        'mpicc -show',
        stderr=subprocess.STDOUT,
        shell=True)

    flags = output.split()
    flags = list(set(flags))  # remove repeated
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
        elif f[:2] == '-l' and f[-1] != "'":
            libs.append(f[2:])
        elif f[:2] == '-U':
            undef_macros.append(f[2:])
        elif f[:2] == '-D':
            tmp = f[2:].split('=')
            if len(tmp) == 1:
                def_macros.append((tmp[0], None))
            else:
                def_macros.append(tuple(tmp))

    return {'inc_dirs': inc_dirs, 'lib_dirs': lib_dirs, 'libs': libs,
            'def_macros': def_macros, 'undef_macros': undef_macros}

mpi_flags = get_mpi_flags()
mpi_flags['inc_dirs'].append(numpy.get_include())

if os.name == 'posix' and os.uname()[4] == 'x86_64':
    extra_compile_args = ['-fPIC']
else:
    extra_compile_args = None

setup(name='Pypar',
      version='2.0',
      description='Pypar - Parallel Python',
      long_description='Pypar - Parallel Python, no-frills MPI interface',
      url='http://github.com/daleroberts/pypar',
      package_dir={'pypar': 'src'},
      packages=['pypar'],
      ext_modules=[Extension('pypar.mpiext',
                             ['src/mpiext.c'],
          include_dirs=mpi_flags['inc_dirs'],
          library_dirs=mpi_flags['lib_dirs'],
          libraries=mpi_flags['libs'],
          define_macros=mpi_flags['def_macros'],
          undef_macros=mpi_flags['undef_macros'],
          extra_compile_args=extra_compile_args)]
      )
