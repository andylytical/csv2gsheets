#!/usr/bin/env python3

from simplegoogledrive import SimpleGoogleDrive
from timeseriesdb import TimeSeriesDB
import argparse
import bisect
import collections
import datetime
import csv
import os
import pathlib
import signal
import time

import pprint

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


def get_csv_data( filter_headers, timestamp_key='datetime' ):
    ''' Read data from CSV file into custom data structure as:
        csvdata = { 'headers': [ String, ... ],
                    'timestamps': [ datetime, ... ],
                    'values': [ dict, ... ]
                  }
        filter_headers is a map where:
            key = (String) header name
            val = (String) python native type, convert to this type (optional)
                  If val is not present, type defaults to string (no conversion)
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
        tgt_headers = filter_headers.keys()
        for row in csv_handle:
            # create a list of values converted to native Pyton type
            filtered_row = []
            for k in row:
                if k in tgt_headers:
                    converted_val = str2py( row[k], filter_headers[k] )
                    filtered_row.append( converted_val )
                    if k == timestamp_key:
                        # save the timestamp for this row
                        timestamps.append( converted_val )
            # append the list of values as a new row of data
            values.append( filtered_row )
        data[ 'headers' ] = filter_headers
    data[ 'timestamps' ] = timestamps
    data[ 'values' ] = values
    return data


def str2py( val, typ ):
    ''' Convert a string to a native Python datatype
    '''
    newval = val
    if typ == 'datetime':
        newval = datetime.datetime.strptime( val, '%Y-%m-%d %H:%M:%S.%f' )
    return newval


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
        print( f"Start='{start}'" )
        print( f"local data row count='{len(local['timestamps'])}'" )
        print( f"Nothing to do" )


def run_loop( runonce=False ):
    global _events
    pause = int( os.environ['CLOUD_BACKUP_INTERVAL_SECONDS'] )
    while True:
        print( "Start new loop" )
        print( "  ...get TSDB" )
        tsdb = get_tsdb()
        print( "  ...open csv infile" )
        headers_to_keep = { k:None for k in tsdb.headers() }
        headers_to_keep[ 'datetime' ] = 'datetime' #convert datetime to a Python datetime
        csv_data = get_csv_data( filter_headers=headers_to_keep )
        print( "  ...update cloud data" )
        update_cloud( csv_data, tsdb )
        if runonce:
            print( "  end" )
            break
        print( "  pause {}".format( pause ) )
        time.sleep( pause )


if __name__ == '__main__':
    pprint.pprint( __name__ )
    _parse_cmdline()
    googl = SimpleGoogleDrive()
    run_loop()
