# Auto-start Lipi OS on the primary console after Live boot.
# Do NOT exec forever: when Lipi exits, drop to a real system shell.
if [ "$(id -u)" -eq 0 ]; then
  _tty="$(tty 2>/dev/null || true)"
  case "$_tty" in
    /dev/tty1|/dev/ttyS0|/dev/ttyAMA0|/dev/hvc0)
      if [ -z "${LIPI_SKIP_AUTOSTART:-}" ] && [ -x /usr/local/bin/lipi-os ]; then
        clear 2>/dev/null || true
        /usr/local/bin/lipi-os --cli || true
        echo
        echo "Lipi OS exited. You are in the system shell."
        echo "Restart Lipi:  lipi-os --cli"
        echo
      fi
      ;;
  esac
fi
