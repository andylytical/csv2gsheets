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


def get_or_create_tsdb( name ):
    sheets_parms = {
        'parent': os.environ['GOOGLE_DRIVE_FOLDER_ID'],
        'pfx': name,
    }
    file_list = googl.get_sheet_by_name_prefix( **sheets_parms )
    if len(file_list) > 1:
        msg = "Found more than one file with name '{}' in google drive".format( name )
        raise UserWarning( msg )
    elif len( file_list ) < 1:
        # Create new file from template
        template_id = os.environ['GOOGLE_SHEETS_TEMPLATE_ID']
        file_id = googl.create_from_template( template_id, name )
    else:
        file_id = file_list[0]['id']
    tsdb_parms = {
        'sheets_service': googl.sheets,
        'file_id': file_id,
        'sheet_name': os.environ['GOOGLE_SHEETS_SHEET_NAME'],
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
        print( "Start new loop...\n find latest beerlog" )
        beer = get_latest_beerlog()
        print( "  get-or-create TSDB" )
        tsdb = get_or_create_tsdb( beer.name )
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
