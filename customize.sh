ui_print "*********************************"
ui_print " Swarm Resource Orchestrator"
ui_print "*********************************"
ui_print "NOTE: Interactive input is not supported in Magisk."
ui_print "Please configure your API key manually after reboot by editing:"
ui_print "/data/adb/modules/resource-orchestrator/system/etc/resource_config.sh"

mkdir -p "$MODPATH/system/etc"
echo 'export GEMINI_API_KEY="YOUR_KEY_HERE"' > "$MODPATH/system/etc/resource_config.sh"

ui_print "*********************************"
ui_print " Installing Dashboard Dependencies"
ui_print "*********************************"
TERMUX_PREFIX=/data/data/com.termux/files/usr
if [ -d "$TERMUX_PREFIX" ]; then
    export PATH=$TERMUX_PREFIX/bin:$PATH
    export LD_LIBRARY_PATH=$TERMUX_PREFIX/lib
    
    ui_print "- Installing Python..."
    $TERMUX_PREFIX/bin/pkg install -y python
    
    ui_print "- Installing Rich library..."
    $TERMUX_PREFIX/bin/pip install rich
    
    ui_print "- Dashboard dependencies installed!"
else
    ui_print "- Termux not detected. You will need to install python and rich manually to use the dashboard."
fi
