# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import tarfile
import zipfile

__all__ = ['extract_tarball', 'extract_zip', 'extract', 'rmtree']


### utilities for extracting archives

def extract_tarball(src, dest):
    """extract a .tar file"""

    bundle = tarfile.open(src)
    namelist = bundle.getnames()

    for name in namelist:
        bundle.extract(name, path=dest)
    bundle.close()
    return namelist


def extract_zip(src, dest):
    """extract a zip file"""

    bundle = zipfile.ZipFile(src)
    namelist = bundle.namelist()

    for name in namelist:
        filename = os.path.realpath(os.path.join(dest, name))
        if name.endswith('/'):
            os.makedirs(filename)
        else:
            path = os.path.dirname(filename)
            if not os.path.isdir(path):
                os.makedirs(path)
            _dest = open(filename, 'wb')
            _dest.write(bundle.read(name))
            _dest.close()
    bundle.close()
    return namelist


def extract(src, dest=None):
    """
    Takes in a tar or zip file and extracts it to dest

    If dest is not specified, extracts to os.path.dirname(src)

    Returns the list of top level files that were extracted
    """

    assert os.path.exists(src), "'%s' does not exist" % src
    assert not os.path.isfile(dest), "dest cannot be a file"

    if dest is None:
        dest = os.path.dirname(src)
    elif not os.path.isdir(dest):
        os.makedirs(dest)

    if zipfile.is_zipfile(src):
        namelist = extract_zip(src, dest)
    elif tarfile.is_tarfile(src):
        namelist = extract_tarball(src, dest)
    else:
        raise Exception("mozfile.extract: no archive format found for '%s'" %
                        src)

    # namelist returns paths with forward slashes even in windows
    top_level_files = [os.path.join(dest, name) for name in namelist
                       if len(name.rstrip('/').split('/')) == 1]

    # namelist doesn't include folders, append these to the list
    for name in namelist:
        root = os.path.join(dest, name[:name.find('/')])
        if root not in top_level_files:
            top_level_files.append(root)

    return top_level_files


def rmtree(dir):
    """Removes the specified directory tree

    This is a replacement for shutil.rmtree that works better under
    windows."""
    # (Thanks to Bear at the OSAF for the code.)
    if not os.path.exists(dir):
        return
    if os.path.islink(dir):
        os.remove(dir)
        return

    # Verify the directory is read/write/execute for the current user
    os.chmod(dir, 0700)

    # os.listdir below only returns a list of unicode filenames
    # if the parameter is unicode.
    # If a non-unicode-named dir contains a unicode filename,
    # that filename will get garbled.
    # So force dir to be unicode.
    try:
        dir = unicode(dir, "utf-8")
    except:
        print("rmtree: decoding from UTF-8 failed")

    for name in os.listdir(dir):
        full_name = os.path.join(dir, name)
        # on Windows, if we don't have write permission we can't remove
        # the file/directory either, so turn that on
        if os.name == 'nt':
            if not os.access(full_name, os.W_OK):
                # I think this is now redundant, but I don't have an NT
                # machine to test on, so I'm going to leave it in place
                # -warner
                os.chmod(full_name, 0600)

        if os.path.islink(full_name):
            os.remove(full_name)
        elif os.path.isdir(full_name):
            rmtree(full_name)
        else:
            if os.path.isfile(full_name):
                os.chmod(full_name, 0700)
            os.remove(full_name)
    os.rmdir(dir)
