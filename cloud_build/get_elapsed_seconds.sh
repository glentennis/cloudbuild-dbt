echo 'seconds since job began:'
echo $(($(date +%s) - $(cat start_time.txt)))
