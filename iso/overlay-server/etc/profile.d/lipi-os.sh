# Auto-start Lipi OS Server on the primary console after Live boot.
# Without exec: exiting Lipi drops to the system shell.
if [ "$(id -u)" -eq 0 ]; then
  _tty="$(tty 2>/dev/null || true)"
  case "$_tty" in
    /dev/tty1|/dev/ttyS0|/dev/ttyAMA0|/dev/hvc0)
      if [ -z "${LIPI_SKIP_AUTOSTART:-}" ] && [ -x /usr/local/bin/lipi-os ]; then
        clear 2>/dev/null || true
        /usr/local/bin/lipi-os --cli || true
        echo
        echo "Lipi OS Server exited. You are in the system shell."
        echo "Restart: lipi-os --cli   |   SSH: root / lipi"
        echo
      fi
      ;;
  esac
fi
