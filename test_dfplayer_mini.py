import machine
import unittest
from unittest.mock import MagicMock
from dfplayer_mini import DFPlayerMini

# Test Class
class TestDFPlayerMini(unittest.TestCase):

    def setUp(self):
        # Mock machine.UART
        machine.UART = MagicMock()
        self.tx_pin = 1
        self.rx_pin = 2
        self.dfplayer = DFPlayerMini(self.tx_pin, self.rx_pin)

    # Test initialisation

    def test_initialization(self):
        # Test that UART is initialized with correct parameters
        machine.UART.assert_called_with(1, baudrate=9600, tx=self.tx_pin, rx=self.rx_pin)

    def test_begin(self):
        # Test the begin method
        self.dfplayer.uart.any.return_value = False
        self.dfplayer.begin()
        self.assertTrue(self.dfplayer.uart.write.called)  # Ensure UART write is called

    def test_wait_for_ready(self):
        # Test wait_for_ready method
        self.dfplayer.wait_for_ready()
        self.assertTrue(self.dfplayer.uart.any.called)  # Ensure UART any is called

    # Test cases for send_command
    def test_send_command(self):
        test_cases = [
            (DFPlayerMini.CMD_NEXT, 0),                        # Command without parameter
            (DFPlayerMini.CMD_PLAY_TRACK, 1),                  # Play specific track
            (DFPlayerMini.CMD_SET_VOLUME, 30),                 # Set volume to 30
            (DFPlayerMini.CMD_PLAY_FOLDER_FILE, (1 << 8) | 1), # Play file 1 in folder 1 (0x0101)
            (DFPlayerMini.CMD_REPEAT_PLAY, 0)                  # Repeat play
        ]

        for command, parameter in test_cases:
            with self.subTest(command=command, parameter=parameter):
                self.dfplayer.send_command(command, parameter)
                # Expected calculation
                param_high = parameter >> 8
                param_low = parameter & 0xFF
                checksum = -(0xFF + 0x06 + command + 0x00 + param_high + param_low) & 0xFFFF
                checksum_high = checksum >> 8
                checksum_low = checksum & 0xFF
                expected_bytes = bytearray([0x7E, 0xFF, 0x06, command, 0x00, param_high, param_low, checksum_high, checksum_low, 0xEF])
                self.dfplayer.uart.write.assert_called_with(expected_bytes)

    # Test cases for calculate_checksum
    def test_calculate_checksum(self):
        test_cases = [
            (0x01, 0x00, 0x00),  # Command without parameter
            (0x03, 0x00, 0x01),  # Play specific track
            (0x06, 0x00, 0x1E),  # Set volume to 30
            (0x0F, 0x01, 0x01),  # Play file 1 in folder 1
            (0x11, 0x00, 0x00)   # Repeat play
        ]

        for command, param_high, param_low in test_cases:
            with self.subTest(command=command, param_high=param_high, param_low=param_low):
                calculated_checksum = self.dfplayer.calculate_checksum(command, param_high, param_low)
                expected_checksum = -(0xFF + 0x06 + command + 0x00 + param_high + param_low) & 0xFFFF
                self.assertEqual(calculated_checksum, expected_checksum)

class TestDFPlayerMiniPlayback(unittest.TestCase):

    def setUp(self):
        self.dfplayer = DFPlayerMini(tx_pin=1, rx_pin=2)
        self.dfplayer.send_command = MagicMock()

    # Test play_track method
    def test_play_track(self):
        test_cases = [1, 10, 100, 255, 300]  # Example track numbers

        for track_number in test_cases:
            with self.subTest(track_number=track_number):
                self.dfplayer.play_track(track_number)
                self.dfplayer.send_command.assert_called_with(0x03, track_number)

    # Test play_next method
    def test_play_next(self):
        self.dfplayer.play_next()
        self.dfplayer.send_command.assert_called_with(0x01, 0)

    # Test play_previous method
    def test_play_previous(self):
        self.dfplayer.play_previous()
        self.dfplayer.send_command.assert_called_with(0x02, 0)


    # Test set_volume method
    def test_set_volume(self):
        test_volumes = [0, 10, 15, 25, 30]  # Example volume levels

        for volume in test_volumes:
            with self.subTest(volume=volume):
                self.dfplayer.set_volume(volume)
                self.dfplayer.send_command.assert_called_with(0x06, volume)

    # Test volume_up method
    def test_volume_up(self):
        self.dfplayer.volume_up()
        self.dfplayer.send_command.assert_called_with(0x04, 0)

    # Test volume_down method
    def test_volume_down(self):
        self.dfplayer.volume_down()
        self.dfplayer.send_command.assert_called_with(0x05, 0)

    # Test pause method
    def test_pause(self):
        self.dfplayer.pause()
        self.dfplayer.send_command.assert_called_with(0x0E, 0)

    # Test resume method
    def test_resume(self):
        self.dfplayer.resume()
        self.dfplayer.send_command.assert_called_with(0x0D, 0)

    # Test stop method
    def test_stop(self):
        self.dfplayer.stop()
        self.dfplayer.send_command.assert_called_with(0x16, 0)

class TestDFPlayerMiniGetStatus(unittest.TestCase):

    def setUp(self):
        self.dfplayer = DFPlayerMini(tx_pin=1, rx_pin=2)
        self.dfplayer.send_command = MagicMock()
        self.dfplayer.uart = MagicMock()

    def make_response_packet(self, status, valid_checksum=True):
        response = bytearray([0x7E, 0xFF, 0x06, 0x42, 0x00, 0x00, status, 0x00, 0x00, 0xEF])
        if valid_checksum:
            checksum = self.dfplayer.calculate_checksum(0x42, 0x00, status)
            response[7] = checksum >> 8
            response[8] = checksum & 0xFF
        return response

    def test_get_status_checksum_error(self):
        self.dfplayer.uart.any.return_value = True
        self.dfplayer.uart.read.return_value = self.make_response_packet(0x02, valid_checksum=False)
        status = self.dfplayer.get_status()
        self.assertEqual(status, "Checksum Error")

    def test_get_status_invalid_packet(self):
        self.dfplayer.uart.any.return_value = True
        self.dfplayer.uart.read.return_value = bytearray(10)  # Invalid packet
        status = self.dfplayer.get_status()
        self.assertEqual(status, "Invalid Response")

    def test_get_status_no_response(self):
        self.dfplayer.uart.any.return_value = False
        status = self.dfplayer.get_status()
        self.assertIsNone(status)

    def test_get_status_valid_response_1(self):
        self.dfplayer.uart.any.return_value = True
        self.dfplayer.uart.read.return_value = self.make_response_packet(0x02)  # Example status code
        status = self.dfplayer.get_status()
        self.assertEqual(status, 0x02)

    def test_get_status_valid_response_2(self):
        self.dfplayer.uart.any.return_value = True
        self.dfplayer.uart.read.return_value = self.make_response_packet(0x03)  # Another example status code
        status = self.dfplayer.get_status()
        self.assertEqual(status, 0x03)

class TestDFPlayerMiniPollFeedback(unittest.TestCase):

    def setUp(self):
        self.dfplayer = DFPlayerMini(tx_pin=1, rx_pin=2)
        self.dfplayer.uart = MagicMock()

    def make_feedback_packet(self, feedback_type, parameter, valid_checksum=True):
        response = bytearray([0x7E, 0xFF, 0x06, feedback_type, 0x00, 0x00, parameter, 0x00, 0x00, 0xEF])
        if valid_checksum:
            checksum = self.dfplayer.calculate_checksum(feedback_type, 0x00, parameter)
            response[7] = checksum >> 8
            response[8] = checksum & 0xFF
        return response

    def test_poll_feedback_checksum_error(self):
        self.dfplayer.uart.any.return_value = True
        self.dfplayer.uart.read.return_value = self.make_feedback_packet(0x41, 0x01, valid_checksum=False)
        feedback = self.dfplayer.poll_feedback()
        self.assertEqual(feedback, "Checksum Error")

    def test_poll_feedback_invalid_packet(self):
        self.dfplayer.uart.any.return_value = True
        self.dfplayer.uart.read.return_value = bytearray(10)  # Invalid packet
        feedback = self.dfplayer.poll_feedback()
        self.assertEqual(feedback, "Invalid Response")

    def test_poll_feedback_valid_response_1(self):
        self.dfplayer.uart.any.return_value = True
        self.dfplayer.uart.read.return_value = self.make_feedback_packet(0x3C, 0x01)  # Example feedback: Track Finished
        feedback = self.dfplayer.poll_feedback()
        self.assertEqual(feedback, (0x3C, 0x01))

    def test_poll_feedback_valid_response_2(self):
        self.dfplayer.uart.any.return_value = True
        self.dfplayer.uart.read.return_value = self.make_feedback_packet(0x40, 0x02)  # Another example feedback: Error
        feedback = self.dfplayer.poll_feedback()
        self.assertEqual(feedback, (0x40, 0x02))

class TestDFPlayerMiniAdvancedPlaybackAndUtilities(unittest.TestCase):

    def setUp(self):
        self.dfplayer = DFPlayerMini(tx_pin=1, rx_pin=2)
        self.dfplayer.send_command = MagicMock()

    # Test repeat_track method
    def test_repeat_track(self):
        self.dfplayer.repeat_track(5)
        self.dfplayer.send_command.assert_called_with(0x08, 5)

    # Test play_from_folder method
    def test_play_from_folder(self):
        self.dfplayer.play_from_folder(1, 10)
        parameter = (1 << 8) | 10
        self.dfplayer.send_command.assert_called_with(0x0F, parameter)

    # Test shuffle_play method
    def test_shuffle_play(self):
        self.dfplayer.shuffle_play()
        self.dfplayer.send_command.assert_called_with(0x18, 0)

    # Test reset method
    def test_reset(self):
        self.dfplayer.reset()
        self.dfplayer.send_command.assert_called_with(0x0C, 0)

    # Test sleep method
    def test_sleep(self):
        self.dfplayer.sleep()
        self.dfplayer.send_command.assert_called_with(0x0A, 0)

    # Test wake_up method
    def test_wake_up(self):
        self.dfplayer.wake_up()
        self.dfplayer.send_command.assert_called_with(0x0B, 0)

    # Test set_playback_source method
    def test_set_playback_source(self):
        self.dfplayer.set_playback_source(2)  # Example: SD card
        self.dfplayer.send_command.assert_called_with(0x09, 2)

    # Test set_equalizer method
    def test_set_equalizer(self):
        self.dfplayer.set_equalizer(3)  # Example: Jazz mode
        self.dfplayer.send_command.assert_called_with(0x07, 3)

    # Test set_volume_adjustment method
    def test_set_volume_adjustment(self):
        self.dfplayer.set_volume_adjustment(10)  # Example gain value
        self.dfplayer.send_command.assert_called_with(0x10, 10)

    # Test repeat_play method
    def test_repeat_play(self):
        self.dfplayer.repeat_play(True)
        self.dfplayer.send_command.assert_called_with(0x11, 0x01)
        self.dfplayer.repeat_play(False)
        self.dfplayer.send_command.assert_called_with(0x11, 0x00)

if __name__ == '__main__':
    unittest.main()
