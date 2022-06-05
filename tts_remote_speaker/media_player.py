"""
Support for Remote RESTAPI Speaker

"""
from collections.abc import Awaitable, Callable, Coroutine
from datetime import timedelta, datetime
import voluptuous as vol

from homeassistant import util
from homeassistant.components import media_source
from homeassistant.components.media_player.const import (
    DOMAIN,
    SUPPORT_BROWSE_MEDIA,
    MEDIA_TYPE_MUSIC,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_SEEK,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_STOP,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA,
    MediaPlayerEntity,
    async_process_play_media_url,
)
from homeassistant.const import (ATTR_ATTRIBUTION,
                                 ATTR_ENTITY_ID,
                                 CONF_NAME,
                                 STATE_OFF,
                                 STATE_ON,
                                 STATE_PLAYING,
                                 STATE_PAUSED,
                                 STATE_IDLE,
)
import homeassistant.util.dt as dt_util
import homeassistant.helpers.config_validation as cv

import json
import logging
import os
import re
import requests
import shlex
import subprocess
import sys
import time



DEFAULT_NAME = 'TTS Remote Speaker'
DEFAULT_VOLUME = 0.5
DEFAULT_CACHE_DIR = "tts"
DEFAULT_ADDRESS = ''

# Remote media player supports rpeating the messages for a number of times, this
# will be extra repeats, means if it is 2 times, then total repeats will be 3.
# NOTED THAT:
# There is a bug with pygame, and 1 repeats doesn't work
DEFAULT_REPEAT_NUM_FOR_TTS = 2

# Remote media player supports an announcement music to be played before each
# audio to play. This is for fun and to alert listner that there will be an
# important message to be played/
DEFAULT_ANNOUNCEMENT_MUSIC = True

# Each media to play must have a priority from 0 to 100, where Lower number is lower priority
# Media player will compare the priority of the new media against the current 
#running media. Only if the new media has higher or equal priority, the new
# media will preempt the current one.
# Suggested Priority Categories #
# 0  - 10   : Low Priority Notifications
# 11 - 40   : Medium Priority Notifications
# 41 - 60   : High Priority Notifications
# 60 - 100  : Alerts
DEFAULT_MEDIA_PRIORITY = 5

SUPPORT_REMOTE_SPEAKER = (
    SUPPORT_BROWSE_MEDIA
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_PAUSE
    | SUPPORT_PLAY
    | SUPPORT_SELECT_SOURCE
    | SUPPORT_STOP
    | SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_STEP
)

SCAN_INTERVAL = timedelta(seconds=3)
MIN_TIME_BETWEEN_SCANS = timedelta(seconds=1)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(milliseconds=10)

CONF_ADDRESS = 'address'
CONF_VOLUME = 'volume'
CONF_CACHE_DIR = 'cache_dir'
CONF_REPEAT_NUM_FOR_TTS = 'repeat_num_for_tts'
CONF_ANNOUNCEMENT_MUSIC = 'announcement_music'
CONF_GET_SOURCES = "get_sources"


DEFAULT_GET_SOURCES = True


ATTRIBUTION = "Special attributes"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_ADDRESS, default=DEFAULT_ADDRESS): cv.string,
    vol.Optional(CONF_GET_SOURCES, default=DEFAULT_GET_SOURCES): cv.boolean,
    vol.Optional(CONF_VOLUME, default=DEFAULT_VOLUME):
        vol.All(vol.Coerce(float), vol.Range(min=0, max=1)),
    vol.Optional(CONF_REPEAT_NUM_FOR_TTS, default=DEFAULT_REPEAT_NUM_FOR_TTS):
        vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    vol.Optional(CONF_ANNOUNCEMENT_MUSIC, default=DEFAULT_ANNOUNCEMENT_MUSIC): cv.boolean,
    vol.Optional(CONF_CACHE_DIR, default=DEFAULT_CACHE_DIR): cv.string,
})


COMPONENT_DOMAIN = 'tts_remote_speaker'
SERVICE_PLAY_AUDIO = "play_audio"
SERVICE_PLAY_AUDIO_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_id,
    vol.Required("media_id"): cv.string,
    vol.Optional(CONF_VOLUME, default=DEFAULT_VOLUME): cv.small_float,
    vol.Optional(CONF_ANNOUNCEMENT_MUSIC, default=DEFAULT_ANNOUNCEMENT_MUSIC): cv.boolean,
    vol.Optional("repeat_num", default=DEFAULT_REPEAT_NUM_FOR_TTS):cv.positive_int,
    vol.Optional("priority", default=DEFAULT_MEDIA_PRIORITY):cv.positive_int,
    }
)
SERVICE_UPDATE_ATTRIBUTES = "update_attributes"
SERVICE_UPDATE_ATTRIBUTES_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_id,
    vol.Optional(CONF_VOLUME, default=DEFAULT_VOLUME): cv.small_float,
    vol.Optional(CONF_ANNOUNCEMENT_MUSIC, default=DEFAULT_ANNOUNCEMENT_MUSIC): cv.boolean,
    vol.Optional("repeat_num", default=DEFAULT_REPEAT_NUM_FOR_TTS):cv.positive_int,
    }
)


googleTTSCachedFile = re.compile(r'^https:\/\/.*\/api\/tts_proxy\/.*google_translate.mp3')
audioURLFile = re.compile(r'^https?\:\/\/.*.(mp3|wav|MP3|WAV)')


_LOGGER = logging.getLogger(__name__)

def get_entity_from_domain(hass, domain, entity_id):
    component = hass.data.get(domain)
    if component is None:
        raise HomeAssistantError("{} component not set up".format(domain))

    entity = component.get_entity(entity_id)
    if entity is None:
        raise HomeAssistantError("{} not found".format(entity_id))

    return entity


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Bluetooth Speaker platform."""
    name = config.get(CONF_NAME)
    address = config.get(CONF_ADDRESS)
    volume = float(config.get(CONF_VOLUME))
    cache_dir = get_tts_cache_dir(hass, config.get(CONF_CACHE_DIR))
    repeat_num_for_tts = float(config.get(CONF_REPEAT_NUM_FOR_TTS))
    announcement_music = bool(config.get(CONF_ANNOUNCEMENT_MUSIC))
    get_sources = bool(config.get(CONF_GET_SOURCES))
    
    add_devices([RemoteSpeakerDevice(hass, name, address, volume, cache_dir, repeat_num_for_tts, announcement_music, get_sources)])

    def play_audio(call):
        """Call play audio."""
        entity_id = call.data[ATTR_ENTITY_ID]
        media_id = call.data['media_id']
        volume = call.data[CONF_VOLUME]
        announcement_music = call.data[CONF_ANNOUNCEMENT_MUSIC]
        repeat_num = call.data['repeat_num']
        priority = call.data['priority']
        speaker = get_entity_from_domain(hass, DOMAIN, entity_id)
        _LOGGER.debug('speaker:' + str(speaker)) 

        _LOGGER.debug('play_audio file:' + media_id)
        url = str(speaker.address) + '/playAudioFile'
        params = {'audioFile': media_id, 
            'volume': volume,
            'announcement_music': announcement_music,
            'repeatNum': repeat_num,
            'priority': priority
        }
        resp = get_http_resp('play_audio', url, params)
        speaker.update()

    def update_attributes(call):
        """Call update custom attributes."""
        entity_id = call.data[ATTR_ENTITY_ID]
        volume = call.data[CONF_VOLUME]
        announcement_music = call.data[CONF_ANNOUNCEMENT_MUSIC]
        repeat_num = call.data['repeat_num']
        speaker = get_entity_from_domain(hass, DOMAIN, entity_id)
        _LOGGER.debug('speaker:' + str(speaker))
        speaker.set_volume_level(volume)
        speaker.set_announcement_music(announcement_music)
        speaker.set_repeat_num_for_tts(repeat_num)

    hass.services.register(
        COMPONENT_DOMAIN, SERVICE_PLAY_AUDIO, play_audio, schema=SERVICE_PLAY_AUDIO_SCHEMA
    )

    hass.services.register(
        COMPONENT_DOMAIN, SERVICE_UPDATE_ATTRIBUTES, update_attributes, schema=SERVICE_UPDATE_ATTRIBUTES_SCHEMA
    )

    return True

def get_http_resp(requestName, url, params):
    if requestName == "update":
        _LOGGER.debug("Sending " + requestName + " http get request: " + url + " | parameters: " + str(params))
    else:
        _LOGGER.info("Sending " + requestName + " http get request: " + url + " | parameters: " + str(params))
    try:
        resp = requests.get(url=url, params = params)
        _LOGGER.debug('Received ' + requestName + ' response code: ' + str(resp.status_code))
        _LOGGER.debug('Received ' + requestName + ' text response: ' + resp.text)
        if requestName == "update":
            if resp.status_code != requests.codes.ok:
                _LOGGER.debug('Received ' + requestName + ' is failed')
            else:
                _LOGGER.debug('Received ' + requestName + ' is successful')
        else:
            if resp.status_code != requests.codes.ok:
                _LOGGER.info('Received ' + requestName + ' is failed')
            else:
                _LOGGER.info('Received ' + requestName + ' is successful')
        return resp
    except Exception as e:
        _LOGGER.info('Failed to initiate ' + requestName + ' request, got error:' + str(e))
        return None


def get_tts_cache_dir(hass, cache_dir):
    """Get cache folder."""
    if not os.path.isabs(cache_dir):
        cache_dir = hass.config.path(cache_dir)
    return cache_dir

class RemoteSpeakerDevice(MediaPlayerEntity):
    """Representation of a remote speaker on the network."""

#    def __init__(self, hass, name, address, volume, pre_silence_duration, post_silence_duration, cache_dir):
    def __init__(self, hass, name, address, volume, cache_dir, repeat_num_for_tts, announcement_music, get_sources):
        """Initialize the device."""
        self._hass = hass
        self._name = name
        self._is_standby = False
        self._current = None
        self._address = address
        self._volume_level = float(volume)
        self._cache_dir = self.get_tts_cache_dir(cache_dir)
        self._repeat_num_for_tts = repeat_num_for_tts
        self._announcement_music = announcement_music
        self._get_sources = get_sources
        self._media_title = None
        self._source_list = None
        self._current_source = None
        self._media_duration = 0.0
        self._media_position = 0.0
        self._media_position_updated_at = None
        self._current_priority = 0
        self.update()

    def get_tts_cache_dir(self, cache_dir):
        """Get cache folder."""
        if not os.path.isabs(cache_dir):
            cache_dir = hass.config.path(cache_dir)
        return cache_dir

    @property
    def name(self):
        """Return the name of the speaker."""
        return self._name

    @property
    def address(self):
        """Return the address of the speaker."""
        return self._address

    # MediaPlayerEntity properties and methods
    @property
    def state(self):
        """Return the state of the device."""
        _LOGGER.debug('State is updated')
        return self._current



    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        support = SUPPORT_REMOTE_SPEAKER
        if self._current == STATE_PLAYING or self._current == STATE_PAUSED:
            support |= SUPPORT_SEEK
        return support

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume_level

    @property
    def media_content_type(self) -> str:
        """Content type of current playing media."""
        return MEDIA_TYPE_MUSIC

    @property
    def media_duration(self):
        """Duration of current playing media in seconds."""
        return self._media_duration


    @property
    def media_position(self):
        """Position of current playing media in seconds."""
        return self._media_position


    @property
    def media_position_updated_at(self):
        """When was the position of the current playing media valid.
        Returns value from homeassistant.util.dt.utcnow().
        """
        return self._media_position_updated_at


    @property
    def media_title(self):
        """Title of current playing media."""
        return self._current_source


    @property
    def source(self):
        """Return the current app."""
        return self._current_source

    @property
    def source_list(self):
        """Return a list of running apps."""
        return self._source_list

    @property
    def repeat_num_for_tts(self):
        """return the number to repeat the TTS audio"""
        return self._repeat_num_for_tts

    @property
    def announcement_music(self):
        """Return if play_media for TTS will play announcement music before or not ."""
        return self._announcement_music

    @property
    def current_priority(self):
        """Return current source priority ."""
        return self._current_priority


    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "repeat_num_for_tts": self._repeat_num_for_tts,
            "announcement_music": self._announcement_music,
            "current_priority": self._current_priority,
        }

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        # self._vlc.audio_set_volume(int(volume * 100))
        url = self._address + '/setVolume'
        params = {'volume': volume}
        resp = get_http_resp('set_volume_level', url, params)
        if resp.text == "Volume set":
            self._volume_level = volume
        else:
            self.update()

    def media_seek(self, position):
        """Seek the media to a specific location."""
        if self._current == STATE_PLAYING or self._current == STATE_PAUSED:
            url = self._address + '/setPos'
            params = {'position': position}
            resp = get_http_resp('set_position', url, params)
            if resp.text == "Position set":
                self._media_position = position
                self._media_position_updated_at = dt_util.utcnow()
            else:
                self.update()


    def volume_up(self):
        """Send volume up command."""
        volume = float(self._volume_level) + 0.1
        if volume > 1.0:
            volume = 1.0
        self.set_volume_level(volume)

    def volume_down(self):
        """Send volume down command."""
        volume = float(self._volume_level) - 0.1
        if volume < 0.0:
            volume = 0.0
        self.set_volume_level(volume)

    def set_repeat_num_for_tts(self, repeatNum):
        """Set repeat_num_for_tts."""
        self._repeat_num_for_tts = repeatNum

    def set_announcement_music(self, announcementMusic):
        """Set announce_music."""
        self._announcement_music = announcementMusic

    def media_pause(self):
        """Send pause media command."""
        url = self._address + '/media_pause'
        resp = get_http_resp('media_pause', url, {})
        self._is_standby = False
        if resp.text == "successful":
            self._current = STATE_PAUSED
            self.update()
        else:
            self.update()

    def media_play(self):
        """Send play media command."""
        url = self._address + '/media_play'
        resp = get_http_resp('media_play', url, {})
        self._is_standby = False
        if resp.text == "successful":
            self._current = STATE_PLAYING
            self.update()
        else:
            self.update()

    def media_stop(self):
        """Send stop media command."""
        url = self._address + '/media_stop'
        resp = get_http_resp('media_stop', url, {})
        self._is_standby = False
        if resp.text == "successful":
            self._current = STATE_IDLE
        else:
            self.update()

    def select_source(self, source):
        """Select Source."""
        url = self._address + '/select_source'
        params = {'source': source}
        resp = get_http_resp('select_source', url, params)
        if resp.text == "successful":
            self._current_source = source
        else:
            self.update()

    async def async_play_media(self, media_type, media_id, **kwargs):
        """Send play commmand."""
        _LOGGER.info('play_media id: %s', media_id)
        _LOGGER.info('play_media type: %s', media_type)
        self._is_standby = False
        self.update()
        
        # Handle media_source
        if media_source.is_media_source_id(media_id):
            sourced_media = await media_source.async_resolve_media(self.hass, media_id)
            media_type = sourced_media.mime_type
            media_id = sourced_media.url
            _LOGGER.info('New play_media id: %s', media_id)
            _LOGGER.info('New play_media type: %s', media_type)
            #media_id = media_id.replace("media-source://media_source/local","/media")
            #media_type = MEDIA_TYPE_MUSIC
        # If media ID is a relative URL, we serve it from HA.
        media_id = async_process_play_media_url(self.hass, media_id)
        _LOGGER.info('New New play_media id: %s', media_id)

        # Handle Music Media
        if media_type == MEDIA_TYPE_MUSIC or media_type == "audio/mpeg":

            #if googleTTSCachedFile.match(media_id):
            #    _LOGGER.debug('play_media file matched Google TTS cached url.')
            #    mediaFile = media_id[media_id.rfind('/') + 1:]
            #    url = self._address + '/playHassTTS'
            #    params = {'audioFile': mediaFile, 
            #        'volume': self._volume_level,
            #        'announcement_music': self._announcement_music,
            #        'repeatNum': self._repeat_num_for_tts,
            #        'priority': DEFAULT_MEDIA_PRIORITY
            #    }
            #    resp = get_http_resp('media_media', url, params)
            #else:
            _LOGGER.debug('play_media file matched known audio file')
            url = self._address + '/playAudioFile'
            params = {'audioFile': media_id, 
                'volume': self._volume_level,
                'announcement_music': self._announcement_music,
                'repeatNum': self._repeat_num_for_tts,
                'priority': DEFAULT_MEDIA_PRIORITY
            }
            #resp = get_http_resp('media_media', url, params)
            resp =  await self.hass.async_add_executor_job(get_http_resp, 'media_media', url, params)
            if resp.text == "successful":
                self._current = STATE_PLAYING
            else:
                self.update()


    @util.Throttle(MIN_TIME_BETWEEN_SCANS, MIN_TIME_BETWEEN_FORCED_SCANS)
    def update(self):
        """ update the status of the speaker """
        _LOGGER.debug('Update status')
        url = self._address + '/getUpdate'
        params = {}
        resp = get_http_resp('update', url, params)
        try:
            if resp.json()['state'] == 'STATE_PLAYING':
                _LOGGER.debug('State is playing')
                self._current = STATE_PLAYING
            elif resp.json()['state'] == 'STATE_PAUSED':
                _LOGGER.debug('State is paused')
                self._current = STATE_PAUSED
            else:
                _LOGGER.debug('State is stopped')
                self._current = STATE_IDLE
        except:
            _LOGGER.debug('Failed to get state, state is stopped')
            self._current = STATE_IDLE
        try:
            self._volume_level = float(resp.json()['volume'])
        except:
            _LOGGER.debug('Failed to get the volume level')
        try:
            self._source_list = sorted(resp.json()['sources'])
        except:
            _LOGGER.debug('Failed to get the sources lists')
        try:
            self._current_source = resp.json()['current_source']
        except:
            _LOGGER.debug('Failed to get current source')
        try:
            self._current_priority = resp.json()['current_priority']
        except:
            self._current_priority = str(0)
            _LOGGER.debug('Failed to get priority of current source')
        if self._current == STATE_PLAYING or self._current == STATE_PAUSED:
            try:
                self._media_duration = float(resp.json()['duration'])
            except:
                self._media_duration = None
                _LOGGER.debug('Failed to get duration of current source')
        else:
            self._media_duration = None
        if self._current == STATE_PLAYING or self._current == STATE_PAUSED:
            try:
                self._media_position = float(resp.json()['position'])
                self._media_position_updated_at = dt_util.utcnow()
            except:
                self._media_position = None
                self._media_position_updated_at = None
                _LOGGER.debug('Failed to get position of the current source')
        else:
            self._media_position = None
            self._media_position_updated_at = None


    async def async_browse_media(self, media_content_type=None, media_content_id=None):
        """Implement the websocket media browsing helper."""
        return await media_source.async_browse_media(
            self.hass,
            media_content_id,
            content_filter=lambda item: item.media_content_type.startswith("audio/"),
        )



