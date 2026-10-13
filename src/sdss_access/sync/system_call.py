# License information goes here
# -*- coding: utf-8 -*-
#
# $Id: system_call.py 157318 2014-06-29 12:10:03Z weaver $
#
"""
"""
#
# This will help with 2to3 support.
#
from __future__ import absolute_import, division, print_function, unicode_literals
#
#
#
def system_call(command,test=False,logger=None,logall=False,message=None,outname=None,errname=None):
    """A convenient wrapper to log and perform system calls.

    Parameters
    ----------
    command : str
        The system command to run.  It will be split internally by shlex.split().
    test : bool, optional
        Set this to true to not actually run the commands.
    logger : logging.logging, optional
        If passed a logging object, diagnostic output will be set to this object.
    logall : bool, optional
        Set this to true to always log stdout and stderr (at level DEBUG).
        Otherwise stdout and stderr will only be logged for nonzero status
    message : str, optional
        Call logger.critical(message) with this message and then call
        sys.exit(status).
    outname : str, optional
        If set, use ``outname`` as the name of a file to contain stdout.  It
        is the responsibility of the caller of this function to clean up
        the resulting file.  Otherwise a temporary file will be used.
    errname : str, optional
        Same as ``outname``, but will contain stderr.

    Returns
    -------
    (status,out,err) : tuple
        The exit status, stdout and stderr of the process

    Examples
    --------
    >>> status,out,err = transfer.common.system_call('date')
    """
    from math import log10
    from sys import exit
    from subprocess import Popen
    from shlex import split
    from tempfile import TemporaryFile
    from time import time, sleep
    if logger is not None:
        logger.debug(command)
    status = 0
    out = ''
    err = ''
    # if test, return early
    if test:
        return (status, out, err)

    # Perform the system call
    if outname is None:
        outfile = TemporaryFile()
    else:
        outfile = open(outname, 'w+')
    if errname is None:
        errfile = TemporaryFile()
    else:
        errfile = open(errname, 'w+')
    proc = Popen(split(str(command)), stdout=outfile, stderr=errfile)
    tstart = time()
    while proc.poll() is None:
        elapsed = time() - tstart
        if elapsed > 500000:
            message = "Process still running after more than 5 days!"
            proc.kill()
            break
        tsleep = 10**(int(log10(elapsed)) - 1)
        if tsleep < 1:
            tsleep = 1
        sleep(tsleep)
    # proc.wait()
    status = proc.returncode
    outfile.seek(0)
    out = outfile.read()
    errfile.seek(0)
    err = errfile.read()
    outfile.close()
    errfile.close()
    if logger is not None:
        if status == 0 and logall:
            if len(out) > 0:
                logger.debug('STDOUT = \n' + out)
            if len(err) > 0:
                logger.debug('STDERR = \n' + err)
        if status != 0:
            logger.error('status = {0}'.format(status))
            if len(out) > 0:
                logger.error('STDOUT = \n' + out)
            if len(err) > 0:
                logger.error('STDERR = \n' + err)
            if message is not None:
                logger.critical(message)
                exit(status)
    return (status, out, err)
