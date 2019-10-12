#!/usr/bin/env python3

from simplegoogledrive import SimpleGoogleDrive
from timeseriesdb import TimeSeriesDB
import argparse
import bisect
import collections
import csv
import os
import pathlib
import signal
import time

import pprint

#needed?
#import sys

#module level paramter settings
_params = {}
#_events = queue.SimpleQueue()

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
    return _get_param( 'CSV2GSHEETS_INFILE', pathlib.Path )

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
    return _get_param( 'GOOGLE_SHEETS_SHEETNAME' )


def _parse_cmdline():
    arg_defaults = {
        'GOOGLE_SHEETS_FILENAME': '',
        'CSV2GSHEETS_INFILE': '',
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
        dest = 'CSV2GSHEETS_INFILE',
        help = ( 'CSV input file ' ),
        )
    namespace = parser.parse_args()
    cmdline_args = { k:v for k,v in vars(namespace).items() if v }
    combined = collections.ChainMap( cmdline_args, os.environ, arg_defaults )
    pprint.pprint( combined )
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
        'sheet_name': _get_google_sheetname(),
    }
    return TimeSeriesDB( **tsdb_parms )


def get_csv_data( timestamp_key='datetime', filter_headers=[] ):
    ''' Read data from CSV file into custom data structure as:
        csvdata = { 'headers': [ String, ... ],
                    'timestamps': [ datetime, ... ],
                    'values': [ dict, ... ]
                  }
        If filter_headers is supplied, keep only those headers that match.
        If a header in filter_headers does not exist in CSV data, None will be
        inserted as the a value for the header.
    '''
    fn = _get_csv_filename()
    data = {}
    timestamps = []
    values = []
    with fn.open( newline='' ) as fh:
        csv_handle = csv.DictReader( fh )
        csv_headers = csv_handle.fieldnames
        tgt_headers = filter_headers
        if not filter_headers: #if list is empty, keep all headers from CSV
            tgt_headers = csv_headers[:] #explicit copy of list
        for row in csv_handle:
            #filtered_row = { k:row[k] for k in row if k in tgt_headers }
            filtered_row = [ row[k] for k in row if k in tgt_headers ]
            values.append( filtered_row )
            timestamps.append( row[ timestamp_key ] )
        data[ 'headers' ] = filter_headers
    data[ 'timestamps' ] = timestamps
    data[ 'values' ] = values
    return data




def update_cloud( local, cloud ):
    # Find local timestamps that are newer than cloud data
    timestamps = sorted( cloud.timestamps() )
    start = 0
    if len(timestamps) > 0:
        start = bisect.bisect( local['timestamps'], timestamps[-1] )
    if start < len(local['values']) :
        #APPEND
        print( f"Start index into local data is '{start}'" )
        num_rows_added = cloud.append( local['values'][start:] )
        print( f'Added {num_rows_added} new rows' )
    else :
        print( f"Start='{start}' >= " )
        print( f"local data row count='{len(local.data['values'])}'" )
        print( f"Nothing to do" )


#def process_events():
#    global _events
#    continue_ok = True
#    while continue_ok:
#        try:
#            sig = _events.get_noblock()
#        except ( queue.EMPTY) as e:
#            continue_ok = False
#            continue
#        os.kill( os.getpid(), sig ) #resend signal to this process
#
#
#def hold_signal( signum, stack ):
#    global _events
#    _events.put( signum )
#
#
#def clean_exit( signum, stack ):
#    sys.exit()

def run_loop( runonce=False ):
    global _events
    pause = int( os.environ['CLOUD_BACKUP_INTERVAL_SECONDS'] )
    while True:
#        signal.signal( signal.SIGTERM, hold_signal )
        print( "Start new loop" )
        print( "  ...get TSDB" )
        tsdb = get_tsdb()
#        print( "  TSDB headers..." )
#        pprint.pprint( tsdb.headers() )
        print( "  ...open csv infile" )
        csv_data = get_csv_data( filter_headers=tsdb.headers() )
#        pprint.pprint( csv_data )
#        raise SystemExit
        print( "  ...update cloud data" )
        update_cloud( csv_data, tsdb )
#        signal.signal( signal.SIGTERM, clean_exit )
#        process_events()
        if runonce:
            print( "  end" )
            break
        print( "  pause {}".format( pause ) )
        time.sleep( pause )


if __name__ == '__main__':
    pprint.pprint( __name__ )
#    signal.signal( signal.SIGTERM, clean_exit )
    _parse_cmdline()
    googl = SimpleGoogleDrive()
    run_loop()
