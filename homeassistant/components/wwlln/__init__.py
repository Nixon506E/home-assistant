"""Support for World Wide Lightning Location Network."""
import logging

from aiowwlln import Client
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS, CONF_UNIT_SYSTEM,
    CONF_UNIT_SYSTEM_IMPERIAL, CONF_UNIT_SYSTEM_METRIC)
from homeassistant.helpers import aiohttp_client, config_validation as cv

from .config_flow import configured_instances
from .const import (
    CONF_WINDOW, DATA_CLIENT, DEFAULT_RADIUS, DEFAULT_WINDOW, DOMAIN)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_RADIUS, default=DEFAULT_RADIUS): cv.positive_int,
        vol.Optional(CONF_WINDOW, default=DEFAULT_WINDOW):
            vol.All(cv.time_period, cv.positive_timedelta)
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    """Set up the WWLLN component."""
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][DATA_CLIENT] = {}

    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    latitude = conf.get(CONF_LATITUDE, hass.config.latitude)
    longitude = conf.get(CONF_LONGITUDE, hass.config.longitude)

    identifier = '{0}, {1}'.format(latitude, longitude)
    if identifier in configured_instances(hass):
        return True

    if hass.config.units.name == CONF_UNIT_SYSTEM_IMPERIAL:
        unit_system = CONF_UNIT_SYSTEM_IMPERIAL
    else:
        unit_system = CONF_UNIT_SYSTEM_METRIC

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={'source': SOURCE_IMPORT},
            data={
                CONF_LATITUDE: latitude,
                CONF_LONGITUDE: longitude,
                CONF_RADIUS: conf[CONF_RADIUS],
                CONF_WINDOW: conf[CONF_WINDOW],
                CONF_UNIT_SYSTEM: unit_system,
            }))

    return True


async def async_setup_entry(hass, config_entry):
    """Set up the WWLLN as config entry."""
    websession = aiohttp_client.async_get_clientsession(hass)

    hass.data[DOMAIN][DATA_CLIENT][config_entry.entry_id] = Client(websession)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(
            config_entry, 'geo_location'))

    return True


async def async_unload_entry(hass, config_entry):
    """Unload an WWLLN config entry."""
    hass.data[DOMAIN][DATA_CLIENT].pop(config_entry.entry_id)

    await hass.config_entries.async_forward_entry_unload(
        config_entry, 'geo_location')

    return True
