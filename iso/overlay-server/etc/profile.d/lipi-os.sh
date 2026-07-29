# Auto-start Lipi OS Server shell on primary console.
if [ "$(id -u)" -eq 0 ]; then
  _tty="$(tty 2>/dev/null || true)"
  case "$_tty" in
    /dev/tty1|/dev/ttyS0|/dev/ttyAMA0|/dev/hvc0)
      if [ -z "${LIPI_SKIP_AUTOSTART:-}" ] && [ -x /usr/local/bin/lipi-os ]; then
        clear 2>/dev/null || true
        exec /usr/local/bin/lipi-os
      fi
      ;;
  esac
fi
