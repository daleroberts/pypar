Files in this directory gives examples of different parallel strategies using the mandbrot fractal as example.

Here are the steps to run the mandelbrot parallel examples:

Step 1:
Ensure pypar is installed and that the tests pass.

Step 2:
Compile C extensions in this directory.

python compile_mandelbrot_extensions.py

Step 3:
Run the sequential code and three parallel examples - e.g.

python mandel_sequential.py
mpirun -np 4 python mandel_parallel_blockwise.py
mpirun -np 4 python mandel_parallel_cyclic.py
mpirun -np 4 python mandel_parallel_dynamic.py


Notes:

The codes need PIL (Python Imaging Library) to
show the results, but the computational bit will still work without PIL.
It also tries to show images using either xv of eog (EyeOfGnome).

An alternative way of compiling the c extensions is:
python compile.py mandel_ext.c
python compile.py mandelplot_ext.c

This material was developed as part of a teaching module during a
summer school in computational science at the ANU in 2005.

