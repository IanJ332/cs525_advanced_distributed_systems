#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
readonly ROLLBACK_TIME=60

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $*"; }
warn() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: $*" >&2; }
error() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2; exit 1; }

usage() { cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS]

Inject network faults for GrayPulse evaluation with automatic rollback.

Options:
    -h, --help      Show help
    -v, --verbose   Verbose output
    -a, --action    Action to perform: 'delay', 'loss', or 'clean'

Examples:
    $SCRIPT_NAME -a delay   # Inject 200ms delay & 20ms jitter on primary interface
    $SCRIPT_NAME -a loss    # Inject 5% packet loss on primary interface
    $SCRIPT_NAME -a clean   # Manually remove any applied faults
EOF
}

get_primary_interface() {
    local iface
    iface=$(ip route | awk '/default/ {print $5}' | head -n 1)
    if [[ -z "$iface" ]]; then
        error "Could not determine primary network interface."
    fi
    echo "$iface"
}

check_dependencies() {
    if ! command -v tc &> /dev/null; then
        error "'tc' (iproute2) binary is not installed or not in PATH."
    fi
    if ! command -v ip &> /dev/null; then
        error "'ip' (iproute2) binary is not installed or not in PATH."
    fi
}

clean_qdisc() {
    local iface="$1"
    log "Cleaning up existing tc qdisc on $iface..."
    # Suppress errors in case there's no qdisc to delete
    tc qdisc del dev "$iface" root &>/dev/null || true
    log "Cleanup complete on $iface."
}

schedule_rollback() {
    local iface="$1"
    log "Scheduling strict non-blocking rollback in $ROLLBACK_TIME seconds on $iface."
    # Fork a subshell to run in the background. Redirecting all standard streams
    # ensures Ansible "ansible script / command" modules do not hang waiting for it.
    (
        sleep "$ROLLBACK_TIME"
        tc qdisc del dev "$iface" root &>/dev/null || true
    ) </dev/null &>/dev/null &
    disown
}

inject_delay() {
    local iface="$1"
    clean_qdisc "$iface"
    log "Injecting 200ms delay with 20ms jitter on $iface..."
    tc qdisc add dev "$iface" root netem delay 200ms 20ms distribution normal
    schedule_rollback "$iface"
}

inject_loss() {
    local iface="$1"
    clean_qdisc "$iface"
    log "Injecting 5% packet loss on $iface..."
    tc qdisc add dev "$iface" root netem loss 5%
    schedule_rollback "$iface"
}

main() {
    local action=""
    local verbose=0

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                verbose=1
                set -x
                shift
                ;;
            -a|--action)
                if [[ -z "${2:-}" ]]; then
                    error "Missing value for --action"
                fi
                action="$2"
                shift 2
                ;;
            *)
                error "Unknown parameter passed: $1"
                ;;
        esac
    done

    if [[ -z "$action" ]]; then
        usage
        error "Action argument (--action) is required."
    fi

    # Must run as root to interact with tc qdisc
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (or via sudo/Ansible become)."
    fi

    check_dependencies
    
    local iface
    iface=$(get_primary_interface)
    log "Detected dynamic primary interface: $iface"

    case "$action" in
        delay)
            inject_delay "$iface"
            ;;
        loss)
            inject_loss "$iface"
            ;;
        clean)
            clean_qdisc "$iface"
            ;;
        *)
            error "Unknown action: $action. Valid actions are 'delay', 'loss', 'clean'."
            ;;
    esac

    log "Script execution completed successfully."
}

main "$@"
