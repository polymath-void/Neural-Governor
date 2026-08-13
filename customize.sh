ui_print "*********************************"
ui_print " Swarm Resource Orchestrator"
ui_print "*********************************"
ui_print "NOTE: Interactive input is not supported in Magisk."
ui_print "Please configure your API key manually after reboot by editing:"
ui_print "/data/adb/modules/resource-orchestrator/system/etc/resource_config.sh"

mkdir -p "$MODPATH/system/etc"
echo 'export GEMINI_API_KEY="YOUR_KEY_HERE"' > "$MODPATH/system/etc/resource_config.sh"

ui_print "*********************************"
ui_print " Dashboard dependencies will automatically install"
ui_print " the first time you run 'neural-dashboard' in Termux."
ui_print "*********************************"
