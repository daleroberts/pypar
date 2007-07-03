"""Create a release of pypar

The release name will be compose of a major release code obtained from
pypar.py as well as the subversion version number.
For example

pypar-1.9.3_39

refers to pypar version 1.9.3 with subversion number 39.

The release files will be store locally in ~ (home) and also
copied to sourceforge where the release manager must log in
and create the Release using the File Releases interface.

This script assumes a Linux platform

"""

from os import sep, system, remove, popen
from tempfile import mktemp
from sys import platform, stdout
from anuga.abstract_2d_finite_volumes.util import get_revision_number



def get_revision_number():
    """Get the version number of the SVN
    NOTE: This requires that the command svn is on the system PATH
    (simply aliasing svn to the binary will not work)
    """

    # Error msg
    msg = 'Command "svn" is not '
    msg += 'recognised on the system PATH.\n\n'
    msg += 'Try to obtain the version info '
    msg += 'by using the command: "svn info".\n'
    msg += 'In this case, make sure svn is accessible on the system path. '
    msg += 'Simply aliasing svn to the binary will not work. '
      
    try:
        # The null stuff is so this section fails quitly.
        # This could cause the svn info command to fail due to
        # the redirection being bad on some platforms.
        # If that occurs then change this code.
        if platform[0:3] == 'win':
            fid = popen('svn info 2> null')
        else:
            fid = popen('svn info 2>/dev/null')
	
    except:
        raise Exception(msg)
    else:
        #print 'Got version from svn'            
        version_info = fid.read()
      
        if version_info == '':
          raise Exception(msg)    
        else:
          pass
          print 'Got version from file'

            
    for line in version_info.split('\n'):
        if line.startswith('Revision:'):
            break

    fields = line.split(':')
    msg = 'Keyword "Revision" was not found anywhere in text: %s'\
          %version_info
    assert fields[0].startswith('Revision'), msg            

    try:
        revision_number = int(fields[1])
    except:
        msg = 'Revision number must be an integer. I got %s' %fields[1]
        msg += 'Check that the command svn is on the system path' 
        raise Exception(msg)                
        
    return revision_number



if __name__ == '__main__':
  
    if platform == 'win32':
        msg = 'This script is not written for Windows.'+\
              'Please run it on a Unix platform'
        raise Exception, msg


    import source.pypar
    major_revision = source.pypar.__version__
      

    package = 'pypar'



    # line separator 
    lsep = '----------------------------------------------------------------------'


    # Get svn revision number and create
    # file with version info for release.
    # This will mean that the version currently checked out is
    # the one which will be released.

    svn_revision = get_revision_number()
    revision = '%s_%s' %(major_revision, svn_revision)
    print 'Creating pypar revision %s' %revision

    distro_filename = 'pypar-%s.tgz' %revision

    # Create area directory
    release_dir = '~/pypar_release_%s' %revision 
    s = 'mkdir %s' %release_dir
    try:
        print s    
        system(s)
    except:
        pass


    # Export a clean directory tree from the working copy to a temporary dir
    distro_dir = mktemp()
    s = 'mkdir %s' %distro_dir
    print s    
    system(s)



    s = 'svn export -r %d source %s/pypar' %(svn_revision,
                                             distro_dir) 
    print s
    system(s)



    # Zip it up
    s = 'cd %s;tar cvfz %s *' %(distro_dir, distro_filename)
    print s
    system(s)

    # Move distro to release area
    s = '/bin/mv %s/*.tgz %s' %(distro_dir, release_dir) 
    print s
    system(s)

    # Clean up
    s = '/bin/rm -rf %s/pypar' %(distro_dir) 
    print s
    system(s)


    #-----------------------------
    # Get demos as well


    #-----------------------------

    print 'Done'
    print
    print
    print lsep
    print 'The release files are in %s:' %release_dir
    system('ls -la %s' %release_dir)
    print lsep
    print
    print

    answer = raw_input('Do you want to upload this to sourceforge? Y/N [Y]')
    if answer.lower() != 'n':
        
        #------------------------------
        print 'Uploading to sourceforge'


        import os, os.path
        release_dir = os.path.expanduser(release_dir)
        os.chdir(release_dir)
        print 'Reading from', os.getcwd()


        from ftplib import FTP
        ftp = FTP('upload.sourceforge.net')
        print ftp.login() # Anonymous
        print ftp.cwd('incoming')


        for filename in os.listdir('.'):
            print 'Uploading %s... ' %filename,
            stdout.flush()

            fid=open(filename, 'rb')
            print ftp.storbinary('STOR %s' %filename, fid)
            fid.close()

        print 'FTP done'
        print ftp.quit()

        print
        print lsep
        print '    ********************* NOTE *************************'
        print lsep
        print 'To complete this release you must log into'
        print 'http://sourceforge.net/projects/pypar as admin'
        print 'and complete the process by selecting File Releases '
        print 'in the admin menu there.'
        print lsep
        print
        print
        


import sys; sys.exit() 
# Create installation tree
s = 'mkdir %s/lib %s/lib/pypar %s/examples' %((release_name,)*3)
print s
os.system(s)

#cleanup dev stuff that shouldn't go into package
s = '/bin/rm %s/install.py %s/compile.py %s/Makefile' %((release_name,)*3)
print s
os.system(s)

s = 'mv %s/pypar.py %s/lib/pypar' %((release_name,)*2)
print s
os.system(s)

s = 'mv %s/__init__.py %s/lib/pypar' %((release_name,)*2)
print s
os.system(s)

s = 'mv %s/mpiext.c %s/lib/pypar' %((release_name,)*2)
print s
os.system(s)

s = 'mv %s/*.py %s/examples' %((release_name,)*2)
print s
os.system(s)

s = 'mv %s/examples/setup.py %s' %((release_name,)*2)
print s
os.system(s)

s = 'mv %s/pytiming %s/examples' %((release_name,)*2)
print s
os.system(s)

s = 'mv %s/ring_example.py %s/examples' %((release_name,)*2)
print s
os.system(s)

s = 'mv %s/runpytiming %s/examples' %((release_name,)*2)
print s
os.system(s)

s = 'mv %s/ctiming.c %s/examples' %((release_name,)*2)
print s
os.system(s)

# Make tarball and copy to destination
s = 'tar cvfz %s.tgz %s' %(release_name, release_name)
print s
os.system(s)

s = 'cp %s.tgz %s' %(release_name, destination)
print s
os.system(s)

s = 'cp %s/lib/pypar/pypar.py %s' %(release_name, destination)
print s
os.system(s)

s = 'cp %s/lib/pypar/mpiext.c %s' %(release_name, destination)
print s
os.system(s)

s = 'cp %s/examples/pytiming %s' %(release_name, destination)
print s
os.system(s)

s = 'cp %s/examples/ctiming.c %s' %(release_name, destination)
print s
os.system(s)

s = 'cp %s/examples/ring_example.py %s' %(release_name, destination)
print s
os.system(s)

s = 'cp %s/README %s' %(release_name, destination)
print s
os.system(s)

s = 'cp %s/DOC %s' %(release_name, destination)
print s
os.system(s)

# Update web page
#
print 'Updating WEB page ' + destination
input = open(destination + '/' + 'index.src', 'r')
output = open(destination + '/' + 'index.php', 'w')

output.write('<!-- AUTOMATICALLY GENERATED - EDIT index.src instead -->\n')
for line in input.readlines():
  line = string.replace(line, '<date>', date) 
  output.write(string.replace(line,'<filename>',release_name+'.tgz'))
output.close()    

#os.system('mv %s.tgz /home/web/dm_web/software/%s' %(release_name, package))
#os.system('cp %s/README /home/web/dm_web/software/%s' %(release_name, package))
#os.system('cp %s/DOC /home/web/dm_web/software/%s' %(release_name, package))

# Make soft link
#
s = 'cd %s; rm pypar.tgz; ln -s %s.tgz pypar.tgz' %(destination, release_name)
print s
os.system(s)

#Cleanup
s = '/bin/rm -f -r %s' %release_name
print s
os.system(s)


