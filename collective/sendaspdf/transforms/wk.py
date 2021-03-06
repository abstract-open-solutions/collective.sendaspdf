# Defines the html_to_pdf method using WKHTMLTOPDF:
# http://code.google.com/p/wkhtmltopdf/
import os
import signal
import subprocess
import logging

from tempfile import TemporaryFile
from threading import Timer

from collective.sendaspdf.utils import find_filename

logger = logging.getLogger('collective.sendaspdf')

wk_command = os.environ.get('WKHTMLTOPDF_PATH')
if wk_command:
    logger.info('wkhtmltopdf found at  %s: ' % wk_command)
else:
    wk_command = 'wkhtmltopdf'
    logger.warn("wkhtmltopdf path unknown, hope it's in the path")

simple_options = ['book', 'collate',
                  'disable-external-links', 'disable-internal-links',
                  'disable-pdf-compression', 'disable-smart-shrinking',
                  'forms', 'grayscale', 'lowquality', 'no-background',
                  'header-line', 'footer-line',
                  'toc', 'toc-disable-back-links', 'toc-disable-links']

valued_options = ['copies', 'cover', 'dpi',
                  'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
                  'minimum-font-size', 'orientation',
                  'page-height', 'page-offset', 'page-size', 'page-width',
                  'header-font-name', 'header-html', 'header-font-size',
                  'header-spacing', 'header-left', 'header-center',
                  'header-right', 'footer-font-name', 'footer-html',
                  'footer-font-size', 'footer-spacing',
                  'footer-left', 'footer-center', 'footer-right',
                  'toc-depth', 'toc-header-text', 'cookie']


def html_to_pdf(source, export_dir, filename,
                original_url, use_print_css, extra_options=[]):
    # First we need to store the source in a temporary
    # file.
    html_filename = find_filename(export_dir,
                                  filename,
                                  'html')
    if not html_filename:
        return None, ['no_filename_temp_html']

    html_file = file('%s/%s' % (export_dir, html_filename),
                     'wb')

    html_file.write(source)
    html_file.close()

    # Run the wkhtmltopdf command.
    args = [wk_command,
            '--disable-javascript',
            '--encoding',
            'utf-8',
            # to work with diazo.
            # https://stackoverflow.com/questions/39934741/plone-collective-sendaspdf-ignores-diazo-theme/39935624
            original_url,
            #'file://%s/%s' % (export_dir, html_filename),
            '%s/%s' % (export_dir, filename)]

    if use_print_css:
        args.insert(4, '--print-media-type')

    for opt in extra_options:
        args.insert(4, opt)

    try:
        proc = subprocess.Popen(args,
                                stdin=TemporaryFile(),
                                stdout=TemporaryFile(),
                                stderr=TemporaryFile())

        if hasattr(proc, 'kill'):
            # Plone 4
            timer = Timer(10, proc.kill)
        else:
            # Plone 3
            timer = Timer(10, lambda pid: os.kill(pid, signal.SIGKILL),
                          [proc.pid])
        timer.start()
        proc.communicate()
        timer.cancel()
    except Exception, err:
        logger.error('Running wkhtmltopdf failed. wkhtmltopdf cmd: %s. '
                     'Error: %s', args, err)
        return None, ['pdf_generation_failed']

    try:
        os.remove('%s/%s' % (export_dir, html_filename))
    except IOError, err:
        logger.error('Temp file does not exist: %s. wkhtmltopdf cmd: %s',
                     err, args)

    try:
        pdf_file = file('%s/%s' % (export_dir, filename), 'r')
    except IOError, err:
        logger.error('No PDF output file: %s. wkhtmltopdf cmd: %s', err, args)
        return None, ['pdf_generation_failed']

    return pdf_file, None
