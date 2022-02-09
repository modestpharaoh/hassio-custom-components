# Hass.io Custom Component - Islamic Prayer Times -IE
This custom component is a forklift of the built-in Home Assistant Islamic Prayer Times component,
but includes prayers times calculated by [Islamic Cultural Centre of Ireland: ICCI](https://islamireland.ie/)
along with other calculation methods ignored in the built-in one such as Egypt, France ...etc.

## Install
* Copy the islamic_prayer_times_ie directory into the custom_components directory of home assistant.
* Reboot your Home assistant.
* Go to Integration section in home assistant.
* Press Add Integration, search for "Islamic Prayer Times - IE".
* The default prayer method is ICCI, you can change it to other, if you wish.
* The component will create 7 time sensors includes the 5 prayer times, sunrise time and midnight time,
* these sensors will be updated to new values at each midnight

## Credits
* Orignal Maintainer of the built-in component[engrbm87](https://github.com/engrbm87)
* Modifier by [modestpharaoh](https://github.com/modestpharaoh)
