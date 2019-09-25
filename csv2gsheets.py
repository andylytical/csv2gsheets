from collections import deque
from simplegoogledrive import SimpleGoogleDrive
from timeseriesdb import TimeSeriesDB
import bisect
import signal

import pprint

#needed?
import os
import sys
import time

#module level paramter settings
_params = {}

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

#
def _get_google_filename():
    ''' Google sheets filename (used as search prefix)
    '''
    return _get_param( 'GOOGLE_SHEETS_FILENAME', pathlib.Path )

def _get_google_sheetname():
    ''' Name of sheet inside google sheets workbook
    '''
    return _get_param( 'GOOGLE_DRIVE_FOLDER_ID' )

#def _get_rate():
#    return _get_param( 'PYTILT_SAMPLE_RATE', int )
#
##def _get_beername():
##    return _get_param( 'PYTILT_BEERNAME', pathlib.Path )
#
#def _get_csvfile():
#    rawpath = _get_param( 'PYTILT_CSVOUTFILE', pathlib.Path )
#    tgtpath = rawpath
#    if not rawpath.is_absolute():
#        tgtpath = pathlib.Path( '/data' ) / rawpath
#    return tgtpath


def _parse_cmdline():
#    arg_defaults = {
#        'PYTILT_COLOR': '',
#        'PYTILT_CSVOUTFILE': 'pytilt_output.csv',
#        'PYTILT_SAMPLE_PERIOD': 900,
#        'PYTILT_SAMPLE_RATE': 5,
#    }
#    parser = argparse.ArgumentParser(
#            description=__doc__,
#            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
#            argument_default=argparse.SUPPRESS)
#    parser.add_argument(
#        '-c', '--color',
#        dest = 'PYTILT_COLOR',
#        help = ( 'Tilt color; which tilt to collect data from '
#                 f'[default={arg_defaults["PYTILT_COLOR"]}] ' )
#        )
#    parser.add_argument(
#        '-f', '--file',
#        dest = 'PYTILT_CSVOUTFILE',
#        help = ( 'CSV output file '
#                 f'[default={arg_defaults["PYTILT_CSVOUTFILE"]}] ' )
#        )
#    parser.add_argument(
#        '-p', '--period', type=int,
#        dest = 'PYTILT_SAMPLE_PERIOD',
#        help = ( 'Tilt sample period, in seconds '
#                 f'[default={arg_defaults["PYTILT_SAMPLE_PERIOD"]}]' )
#        )
#    parser.add_argument(
#        '-r', '--rate', type=int,
#        dest = 'PYTILT_SAMPLE_RATE',
#        help = ( 'Tilt sample rate; number of secs between individual samples '
#                 'in the sampling period'
#                 f'[default={arg_defaults["PYTILT_SAMPLE_RATE"]}]' )
#        )
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


def assert_headers_equal( tsdb, beer ):
    tsdb_headers = tsdb.headers()
    local_headers = beer.headers()
    if len(local_headers) != len(tsdb_headers) :
        msg = "Header length mismatch: local data header count='{}' cloud data header count='{}'".format(
            len(local_headers),
            len(tsdb_headers)
        )
        raise UserWarning(msg)


def update_cloud( local, cloud ):
    # Find local timestamps that are newer than cloud data
    timestamps = sorted( cloud.timestamps() )
    start = 0
    if len(timestamps) > 0:
        start = bisect.bisect( local.timestamps(), timestamps[-1] )
    if start < len(local.data['values']) :
        #APPEND
        print( "Start index into local data is '{}'".format( start ) )
        num_rows_added = cloud.append( local.data['values'][start:] )
        print( 'Added {} new rows'.format( num_rows_added ) )
    else :
        print( "Start='{}' , local beer data row count='{}' , nothing to do".format(
            start, len(local.data['values'])
        ) )


def hold_signal( signum, stack ):
    global EVENTS
    EVENTS.append( signum )


def clean_exit( signum, stack ):
    sys.exit()

def run_loop( runonce=False ):
    global EVENTS
    pause = int( os.environ['BREWPI_BACKUP_INTERVAL_SECONDS'] )
    while True:
        signal.signal( 15, hold_signal )
        print( "Start new loop" )
        print( "  ...get TSDB" )
        tsdb = get_tsdb( beer.name )
        print( "  assert headers equal" )
        assert_headers_equal( tsdb, beer )
        print( "  update cloud data" )
        update_cloud( beer, tsdb )
        if runonce:
            print( "  end" )
            break
        if len( EVENTS ) > 0:
            clean_exit( EVENTS.popleft(), None )
        signal.signal( 15, clean_exit )
        print( "  pause {}".format( pause ) )
        time.sleep( pause )


if __name__ == '__main__':
    pprint.pprint( __name__ )
#    EVENTS = deque()
#    signal.signal( 15, clean_exit )
#    brew_logdir = simpledir.SimpleDir( '/home/pi/brewpi-data/data' )
#    googl = SimpleGoogleDrive()
#    val = False
#    if 'BREWPI_BACKUP_RUNONCE' in os.environ:
#        val = os.environ['BREWPI_BACKUP_RUNONCE'] in ('1', 'True')
#    run_loop( runonce=val )
