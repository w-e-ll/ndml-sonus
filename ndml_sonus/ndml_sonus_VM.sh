#!/bin/bash

BASEDIR=os.path.realpath(os.path.join(os.path.dirname(__file__), ''))

$BASEDIR/bin/getdata_production_VM_psx.sh &
$BASEDIR/bin/getdata_production_VM_marais.sh &
$BASEDIR/bin/getdata_production_VM_paille.sh &
#echo `date` - Waiting for getdata to finish
wait
#echo `date` - getdata finished
$BASEDIR/bin/parsedata_production_VM_psx.sh &
$BASEDIR/bin/parsedata_production_VM_marais.sh &
$BASEDIR/bin/parsedata_production_VM_paille.sh &
#echo `date` - Waiting for parsing to finish
wait
#echo `date` - parsing finished starting load
$BASEDIR/loader_generic/bin/copy_and_load_prod.sh
wait
#echo `date` - load finished
