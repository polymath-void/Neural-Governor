# Ask for API Key
ui_print "*********************************"
ui_print " Swarm Resource Orchestrator"
ui_print "*********************************"
ui_print "Please enter your Gemini API Key:"
read -r API_KEY
echo "export GEMINI_API_KEY=$API_KEY" >> /data/adb/modules/resource-orchestrator/system/etc/resource_config.sh
ui_print "API Key configured."

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
