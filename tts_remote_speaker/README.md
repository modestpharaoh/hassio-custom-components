# Hass.io Custom Component - Remote Speaker
This custom component is the API component that adds a media player which interact with 
my custom local media player add-on [Remote Speaker](https://github.com/modestpharaoh/hassio-addons/tree/master/remote_speaker).

## Install
* Copy the 
tts_remote_speaker directory into the custom_components directory of home assistant.
* Reboot your Home assistant.
* You can add remote speaker media player, by the following config in the main config:
  ```
  media_player:
    - platform: tts_remote_speaker
      name: Hass Local Speaker
      address: http://192.168.x.x:5005 # The IP should be the hass.io local IP or docker container IP, port should be whatever configured for the addon (Default is 5005)
      volume: 0.8
      repeat_num_for_tts: 1
      announcement_music: false
  ```
* Reboot your home assistant, you should have media player entity: media_player.hass_local_speaker

## Supported Features in the media player:
* Home assistant local media browser.
* Play local media.
* Play certain media come with the containers such as alarm sounds and azan prayer.
* Play, pause, seek and stop current audio selected.
* Volume set.

## Extra features:
[To DO]

## Credits
* Orignal Maintainer of the built-in component: [engrbm87](https://github.com/engrbm87)
* Modified by [modestpharaoh](https://github.com/modestpharaoh)
