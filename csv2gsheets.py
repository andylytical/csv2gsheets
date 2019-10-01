#!/usr/bin/env python3

from simplegoogledrive import SimpleGoogleDrive
from timeseriesdb import TimeSeriesDB
import bisect
import signal
import queue

import pprint

#needed?
import os
import sys
import time

#module level paramter settings
_params = {}
_events = queue.SimpleQueue()

### Getter methods for program parameters.
def _get_param( pname, ptype=str ):
    if pname not in _params:
        try:
            rawval = _params[ 'args' ][ pname ]
        except ( KeyError ) as e:
            msg = ( f"\nMissing parameter '{pname}'.\n" )
            raise SystemExit( msg )
        _params[ pname ] = ptype( rawval )
    return _params[ pname ]


def _get_csv_filename():
    ''' Local csv filename
    '''
    return _get_param( 'CSV_FILENAME', pathlib.Path )

def _get_google_folder_id():
    ''' Parent folder in google
    '''
    return _get_param( 'GOOGLE_DRIVE_FOLDER_ID' )


def _get_google_filename():
    ''' Google sheets filename (used as search prefix)
    '''
    return _get_param( 'GOOGLE_SHEETS_FILENAME', pathlib.Path )

def _get_google_sheetname():
    ''' Name of sheet inside google sheets workbook
    '''
    return _get_param( 'GOOGLE_DRIVE_FOLDER_ID' )


def _parse_cmdline():
    arg_defaults = {
        'GOOGLE_SHEETS_FILENAME': '',
        'CSV_FILENAME': '',
    }
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            argument_default=argparse.SUPPRESS)
    parser.add_argument(
        '-o', '--outfile',
        dest = 'GOOGLE_SHEETS_FILENAME',
        help = ( 'Google Sheets Filename; CSV data will be uploaded to here' ),
        )
    parser.add_argument(
        '-i', '--infile',
        dest = 'CSV_FILENAME',
        help = ( 'CSV input file ' ),
        )
    namespace = parser.parse_args()
    cmdline_args = { k:v for k,v in vars(namespace).items() if v }
    combined = collections.ChainMap( cmdline_args, os.environ, arg_defaults )
    _params[ 'args' ] = combined


def get_tsdb():
    sheets_parms = {
        'parent': _get_google_folder_id(),
        'pfx': _get_google_filename(),
    }
    file_list = googl.get_sheet_by_name_prefix( **sheets_parms )
    if len(file_list) > 1:
        msg = "Found more than one file with name '{}' in google drive".format( name )
        raise UserWarning( msg )
    elif len( file_list ) < 1:
        msg = "No files found matching name '{}' in google drive".format( name )
        raise UserWarning( msg )
    else:
        file_id = file_list[0]['id']
    tsdb_parms = {
        'sheets_service': googl.sheets,
        'file_id': file_id,
        'sheet_name': _get_google_sheet_name(),
    }
    return TimeSeriesDB( **tsdb_parms )


#def assert_headers_equal( tsdb, beer ):
#    tsdb_headers = tsdb.headers()
#    local_headers = beer.headers()
#    if len(local_headers) != len(tsdb_headers) :
#        msg = "Header length mismatch: local data header count='{}' cloud data header count='{}'".format(
#            len(local_headers),
#            len(tsdb_headers)
#        )
#        raise UserWarning(msg)


#def update_cloud( local, cloud ):
#    # Find local timestamps that are newer than cloud data
#    timestamps = sorted( cloud.timestamps() )
#    start = 0
#    if len(timestamps) > 0:
#        start = bisect.bisect( local.timestamps(), timestamps[-1] )
#    if start < len(local.data['values']) :
#        #APPEND
#        print( "Start index into local data is '{}'".format( start ) )
#        num_rows_added = cloud.append( local.data['values'][start:] )
#        print( 'Added {} new rows'.format( num_rows_added ) )
#    else :
#        print( "Start='{}' , local beer data row count='{}' , nothing to do".format(
#            start, len(local.data['values'])
#        ) )


def process_events():
    global _events
    continue_ok = True
    while continue_ok:
        try:
            sig = _events.get_noblock()
        except ( queue.EMPTY) as e:
            continue_ok = False
            continue
        os.kill( os.getpid(), sig ) #resend signal to this process


def hold_signal( signum, stack ):
    global _events
    _events.put( signum )


def clean_exit( signum, stack ):
    sys.exit()

def run_loop( runonce=False ):
    global _events
    pause = int( os.environ['CLOUD_BACKUP_INTERVAL_SECONDS'] )
    while True:
        signal.signal( signal.SIGTERM, hold_signal )
        print( "Start new loop" )
        print( "  ...get TSDB" )
        tsdb = get_tsdb()
#        print( "  assert headers equal" )
#        assert_headers_equal( tsdb, beer )
#        print( "  update cloud data" )
#        update_cloud( beer, tsdb )
        signal.signal( signal.SIGTERM, clean_exit )
        process_events()
        if runonce:
            print( "  end" )
            break
        print( "  pause {}".format( pause ) )
        time.sleep( pause )


if __name__ == '__main__':
    pprint.pprint( __name__ )
    signal.signal( signal.SIGTERM, clean_exit )
    googl = SimpleGoogleDrive()
    run_loop()
