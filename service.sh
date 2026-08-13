#!/system/bin/sh
# Neural-Governor Daemon Service
# Starts the sub-booster daemon in the background to snapshot data for the Brain.

MODDIR=${0%/*}

# Wait for boot to finish
until [ "$(getprop sys.boot_completed)" = "1" ]; do
    sleep 5
done

# We ensure our binary exists
if [ -f "$MODDIR/system/bin/resource-orchestrator" ]; then
    chmod +x "$MODDIR/system/bin/resource-orchestrator"
    
    # Start the daemon
    nohup "$MODDIR/system/bin/resource-orchestrator" --daemon > /dev/null 2>&1 &
fi
