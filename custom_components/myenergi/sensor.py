"""Sensor platform for myenergi."""
import operator

from homeassistant.const import DEVICE_CLASS_ENERGY
from homeassistant.const import DEVICE_CLASS_POWER
from homeassistant.const import ENERGY_KILO_WATT_HOUR
from homeassistant.const import ENERGY_WATT_HOUR
from homeassistant.const import POWER_WATT
from pymyenergi import CT_BATTERY
from pymyenergi import CT_LOAD

from .const import DOMAIN
from .entity import MyenergiEntity
from .entity import MyenergiHub


def create_meta(
    name, prop_name, device_class=None, unit=None, icon=None, state_class=None
):
    """Create metadata for entity"""
    return {
        "name": name,
        "prop_name": prop_name,
        "device_class": device_class,
        "unit": unit,
        "icon": icon,
        "state_class": state_class,
        "attrs": {},
    }


def create_power_meta(name, prop_name):
    return {
        "name": name,
        "prop_name": prop_name,
        "device_class": DEVICE_CLASS_POWER,
        "unit": POWER_WATT,
        "icon": "mdi:flash",
        "attrs": {"state_class": "measurement"},
    }


def create_energy_meta(name, prop_name):
    return {
        "name": name,
        "prop_name": prop_name,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
        "icon": None,
        "attrs": {"state_class": "total_increasing"},
    }


def create_energy_meta_wh(name, prop_name):
    return {
        "name": name,
        "prop_name": prop_name,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_WATT_HOUR,
        "icon": None,
        "attrs": {"state_class": "total_increasing"},
    }


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []
    # Don't cause a refresh when fetching sensors
    all_devices = await coordinator.client.get_devices("all", False)
    sensors.append(
        MyenergiHubSensor(
            coordinator,
            entry,
            create_power_meta(
                "Power grid",
                "power_grid",
            ),
        )
    )
    sensors.append(
        MyenergiHubSensor(
            coordinator,
            entry,
            create_energy_meta_wh(
                "Grid import today",
                "energy_imported",
            ),
        )
    )
    sensors.append(
        MyenergiHubSensor(
            coordinator,
            entry,
            create_energy_meta_wh(
                "Grid export today",
                "energy_exported",
            ),
        )
    )
    sensors.append(
        MyenergiHubSensor(
            coordinator,
            entry,
            create_energy_meta_wh(
                "Diverted today",
                "energy_diverted",
            ),
        )
    )
    sensors.append(
        MyenergiHubSensor(
            coordinator,
            entry,
            create_energy_meta_wh(
                "Generated today",
                "energy_generated",
            ),
        )
    )
    sensors.append(
        MyenergiHubSensor(
            coordinator,
            entry,
            create_power_meta(
                "Power generation",
                "power_generation",
            ),
        )
    )
    totals = coordinator.client.get_power_totals()
    if totals.get(CT_LOAD, None) is not None:
        sensors.append(
            MyenergiHubSensor(
                coordinator,
                entry,
                create_power_meta(
                    "Power charging",
                    "power_charging",
                ),
            )
        )
    if totals.get(CT_BATTERY, None) is not None:
        sensors.append(
            MyenergiHubSensor(
                coordinator,
                entry,
                create_power_meta(
                    "Power battery",
                    "power_battery",
                ),
            )
        )
    sensors.append(
        MyenergiHubSensor(
            coordinator,
            entry,
            create_power_meta(
                "Home honsumption",
                "consumption_home",
            ),
        )
    )
    for device in all_devices:
        # Sensors available in all devices
        sensors.append(
            MyenergiSensor(
                coordinator,
                device,
                entry,
                create_power_meta(
                    f"{device.ct1.name} CT1",
                    "ct1.power",
                ),
            )
        )
        sensors.append(
            MyenergiSensor(
                coordinator,
                device,
                entry,
                create_power_meta(
                    f"{device.ct2.name} CT2",
                    "ct2.power",
                ),
            )
        )
        sensors.append(
            MyenergiSensor(
                coordinator,
                device,
                entry,
                create_power_meta(
                    f"{device.ct3.name} CT3",
                    "ct3.power",
                ),
            )
        )

        # Sensors common to Zapi and Eddi
        if device.kind in ["zappi", "eddi"]:
            sensors.append(
                MyenergiSensor(
                    coordinator, device, entry, create_meta("Status", "status")
                )
            )
            sensors.append(
                MyenergiSensor(
                    coordinator,
                    device,
                    entry,
                    create_energy_meta_wh("Energy used today", "energy_total"),
                )
            )
            sensors.append(
                MyenergiSensor(
                    coordinator,
                    device,
                    entry,
                    create_energy_meta_wh("Energy diverted today", "energy_diverted"),
                )
            )
            for key in device.ct_keys:
                sensors.append(MyenergiCTEnergySensor(coordinator, device, entry, key))
        # Zappi only sensors
        if device.kind == "zappi":
            sensors.append(
                MyenergiSensor(
                    coordinator,
                    device,
                    entry,
                    create_energy_meta("Charge added session", "charge_added"),
                )
            )
            sensors.append(
                MyenergiSensor(
                    coordinator,
                    device,
                    entry,
                    create_meta("Plug status", "plug_status"),
                )
            )

            if device.ct4.name != "None":
                sensors.append(
                    MyenergiSensor(
                        coordinator,
                        device,
                        entry,
                        create_power_meta(
                            f"{device.ct4.name} CT4",
                            "ct4.power",
                        ),
                    )
                )
            if device.ct5.name != "None":
                sensors.append(
                    MyenergiSensor(
                        coordinator,
                        device,
                        entry,
                        create_power_meta(
                            f"{device.ct5.name} CT5",
                            "ct5.power",
                        ),
                    )
                )
            if device.ct6.name != "None":
                sensors.append(
                    MyenergiSensor(
                        coordinator,
                        device,
                        entry,
                        create_power_meta(
                            f"{device.ct6.name} CT6",
                            "ct6.power",
                        ),
                    )
                )

        elif device.kind == "eddi":
            # Eddi specifc sensors
            sensors.append(
                MyenergiSensor(
                    coordinator,
                    device,
                    entry,
                    create_energy_meta("Energy diverted session", "diverted_session"),
                )
            )
    async_add_devices(sensors)


class MyenergiHubSensor(MyenergiHub):
    """myenergi Sensor class."""

    def __init__(self, coordinator, config_entry, meta):
        super().__init__(coordinator, config_entry, meta)

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}-{self.coordinator.client.serial_number}-{self.meta['prop_name']}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"myenergi {self.coordinator.client.site_name} {self.meta['name']}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return operator.attrgetter(self.meta["prop_name"])(self.coordinator.client)

    @property
    def unit_of_measurement(self):
        return self.meta["unit"]

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self.meta["icon"]

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return self.meta["device_class"]


class MyenergiSensor(MyenergiEntity):
    """myenergi Sensor class."""

    def __init__(self, coordinator, device, config_entry, meta):
        super().__init__(coordinator, device, config_entry, meta)

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}-{self.device.serial_number}-{self.meta['prop_name']}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"myenergi {self.device.name} {self.meta['name']}"

    @property
    def state(self):
        """Return the state of the sensor."""
        value = operator.attrgetter(self.meta["prop_name"])(self.device)
        if value is None:
            return None
        return value

    @property
    def unit_of_measurement(self):
        return self.meta["unit"]

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self.meta["icon"]

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return self.meta["device_class"]


class MyenergiCTEnergySensor(MyenergiEntity):
    """myenergi CT Energy sensor class"""

    def __init__(self, coordinator, device, config_entry, key):
        meta = {
            "name": f"{key.replace('_', ' ')} today",
            "prop_name": key,
            "device_class": DEVICE_CLASS_ENERGY,
            "unit": ENERGY_WATT_HOUR,
            "icon": None,
            "attrs": {"state_class": "total_increasing"},
        }
        self.key = key
        super().__init__(coordinator, device, config_entry, meta)

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}-{self.device.serial_number}-{self.meta['prop_name']}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"myenergi {self.device.name} {self.meta['name']}"

    @property
    def state(self):
        """Return the state of the sensor."""
        value = self.device.history_data.get(self.key, None)
        if value is None:
            return None
        return value

    @property
    def unit_of_measurement(self):
        return self.meta["unit"]

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self.meta["icon"]

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return self.meta["device_class"]
