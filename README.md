# DFPlayerMini micropython Driver

A python driver for the [DFPlayer Mini](https://www.dfrobot.com/index.php?route=product/product&product_id=1121), intended as a low-level alternative driver including device status and feedback processing.

The driver is based directly on the [Official DFPlayer C/C++ driver](https://github.com/DFRobot/DFRobotDFPlayerMini) and best-fit supports the same interface. 

## Getting Started

Import and instantiate the driver as follows:

```python
from dfplayer_mini import DFPlayerMini

player = DFPlayerMini(tx_pin=1, rx_pin=2)

player.begin()
player.play_track(1)
```

## Methods

### Initialisation
* begin()

### Basic Commands
* play_track(track_number)
* play_next()
* play_previous()
* set_volume(volume)
* volume_up()
* volume_down()
* pause()
* resume()
* stop()

### Status & Feedback Commands
* get_status()
* poll_feedback()

### Advanced Commands
* repeat_track(track_number)
* play_from_folder(folder_number, track_number)
* shuffle_play()

### Utility Commands
* reset()
* sleep()
* wake_up()
* set_playback_source(source)
* set_equalizer(eq_mode)
* set_volume_adjustment(gain)
* repeat_play(enable)

### Low-Level Commands
* wait_for_ready()
* send_command(command, parameter=0)
* calculate_checksum(command, param_high, param_low)

## Constants

DFPlayerMini includes all relevant constants (commands, statuses, etc). Please see the [source code](dfplayer_mini.py) for details.

## Tests

Please see [test_dfplayer_mini.py](test_dfplayer_mini.py) for tests ([unittest](https://docs.python.org/3/library/unittest.html)).

## License

DFPlayerMini is licensed under the [MIT License](https://en.wikipedia.org/wiki/MIT_License). See [LICENSE](LICENSE.txt) for details.

## References

* [DFPlayer Mini Product Page](https://www.dfrobot.com/index.php?route=product/product&product_id=1121)
* [DFPlayer Mini Documentation](https://picaxe.com/docs/spe033.pdf)
* [DFPlayer Mini Micropython driver](https://github.com/lavron/micropython-dfplayermini)
* [Official DFPlayer C/C++ driver](https://github.com/DFRobot/DFRobotDFPlayerMini)