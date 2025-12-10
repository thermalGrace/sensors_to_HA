from machine import UART, Pin
import time
import math

# Enable to print decoded targets and frame issues to the console for tuning.
DEBUG = True

class Target:
    def __init__(self, x, y, speed, pixel_distance):
        self.x = x                  # mm
        self.y = y                  # mm
        self.speed = speed          # cm/s
        self.pixel_distance = pixel_distance  # mm
        self.distance = math.sqrt(x**2 + y**2)
        self.angle = math.degrees(math.atan2(x, y))

    def __str__(self):
        return ('Target(x={}mm, y={}mm, speed={}cm/s, pixel_dist={}mm, '
                'distance={:.1f}mm, angle={:.1f}°)').format(
                self.x, self.y, self.speed, self.pixel_distance, self.distance, self.angle)

class RD03D:
    SINGLE_TARGET_CMD = bytes([0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0x80, 0x00, 0x04, 0x03, 0x02, 0x01])
    MULTI_TARGET_CMD  = bytes([0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0x90, 0x00, 0x04, 0x03, 0x02, 0x01])

    def __init__(self, uart_id=0, tx_pin=0, rx_pin=1, multi_mode=True):
        self.uart = UART(uart_id, baudrate=256000, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.targets = []  # Stores up to 3 targets per module capability
        self._rx_buf = bytearray()
        time.sleep(0.2)
        self.set_multi_mode(multi_mode)

    def set_multi_mode(self, multi_mode=True):
        """Set Radar mode: True=Multi-target (max 3 targets), False=Single-target."""
        cmd = self.MULTI_TARGET_CMD if multi_mode else self.SINGLE_TARGET_CMD
        self.uart.write(cmd)
        time.sleep(0.2)
        self.uart.read()  # Clear buffer after switching
        self.multi_mode = multi_mode

    @staticmethod
    def parse_signed16(high, low):
        """Two's-complement 16-bit to Python int."""
        raw = (high << 8) | low
        return raw - 0x10000 if raw & 0x8000 else raw

    @staticmethod
    def parse_signmag15(high, low):
        """Sign bit in MSB, magnitude in lower 15 bits (as some docs/commenters suggest)."""
        raw = (high << 8) | low
        mag = raw & 0x7FFF
        return -mag if (raw & 0x8000) else mag

    def _decode_frame(self, data):
        """Decode one 30-byte frame into up to 3 targets."""
        targets = []
        if len(data) != 30 or data[0] != 0xAA or data[1] != 0xFF or data[-2] != 0x55 or data[-1] != 0xCC:
            return targets

        count = min(max(data[2], 0), 3)  # reported targets, capped to 3
        if count == 0:
            return targets

        for i in range(count):
            base = 4 + i * 8
            x = self.parse_signmag15(data[base + 1], data[base])
            y = self.parse_signmag15(data[base + 3], data[base + 2])
            speed = self.parse_signmag15(data[base + 5], data[base + 4])
            pixel_dist = data[base + 6] + (data[base + 7] << 8)
            tgt = Target(x, y, speed, pixel_dist)

            if x == 0 and y == 0:
                continue
            targets.append(tgt)

        if DEBUG:
            print("RD03D frame decoded targets:", [str(t) for t in targets])
        return targets

    def update(self):
        """Poll UART for a valid frame; update targets when one is found."""
        timeout = time.ticks_ms() + 120
        FRAME_LEN = 30

        while time.ticks_ms() < timeout:
            if self.uart.any():
                self._rx_buf.extend(self.uart.read())

            # Trim leading noise until header AA FF is aligned (Micropython-safe slicing)
            while len(self._rx_buf) >= 2 and not (self._rx_buf[0] == 0xAA and self._rx_buf[1] == 0xFF):
                self._rx_buf = self._rx_buf[1:]

            if len(self._rx_buf) >= FRAME_LEN:
                frame = bytes(self._rx_buf[:FRAME_LEN])
                self._rx_buf = self._rx_buf[FRAME_LEN:]
                decoded = self._decode_frame(frame)
                if decoded:
                    self.targets = decoded
                    return True
                elif DEBUG:
                    print("RD03D invalid frame:", frame)
                # if invalid, continue scanning (buffer already trimmed)

            time.sleep(0.01)

        return False  # No valid frame within timeout

    def get_target(self, target_number=1):
        """Get a target by number (1-based index)."""
        if 1 <= target_number <= len(self.targets):
            return self.targets[target_number - 1]
        return None  # No such target
