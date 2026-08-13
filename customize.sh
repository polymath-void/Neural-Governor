# Ask for API Key
ui_print "*********************************"
ui_print " Swarm Resource Orchestrator"
ui_print "*********************************"
ui_print "Please enter your Gemini API Key:"
read -r API_KEY
echo "export GEMINI_API_KEY=$API_KEY" >> /data/adb/modules/resource-orchestrator/system/etc/resource_config.sh
ui_print "API Key configured."
