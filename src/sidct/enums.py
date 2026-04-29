"""Enumerações do sistema SIDCT."""
from enum import Enum, auto


class PhysicalRegime(str, Enum):
    PRESSURIZED_INCOMPRESSIBLE = "pressurized_incompressible"
    COMPRESSIBLE_GAS = "compressible_gas"
    GRAVITY_PARTIALLY_FULL = "gravity_partially_full"
    VACUUM_CONDUCTANCE = "vacuum_conductance"
    EXTERNAL_PRESSURE_CHECK = "external_pressure_check"
    FIRE_PROTECTION_SPECIAL = "fire_protection_special"


class Service(str, Enum):
    COMPRESSED_AIR = "compressed_air"
    NATURAL_GAS = "natural_gas"
    POTABLE_WATER = "potable_water"
    SERVICE_WATER = "service_water"
    OSMOTIZED_WATER = "osmotized_water"
    CHILLED_WATER = "chilled_water"
    CONDENSER_WATER = "condenser_water"
    VACUUM_UTILITY = "vacuum_utility"
    SANITARY_DRAINAGE = "sanitary_drainage"
    RAINWATER = "rainwater"
    FIRE_WATER = "fire_water"


class ProjectProfile(str, Enum):
    GLASS_FACTORY_EU = "glass_factory_industrial_eu"
    GLASS_FACTORY_US = "glass_factory_industrial_us"
    INDUSTRIAL_UTILITIES_EU = "industrial_utilities_eu"
    INDUSTRIAL_UTILITIES_BRAZIL = "industrial_utilities_brazil"
    DATACENTRE_EU = "datacentre_building_services_eu"
    DATACENTRE_US = "datacentre_building_services_us"
    FIRE_PROTECTION_EN = "fire_protection_en"
    FIRE_PROTECTION_US = "fire_protection_us"
    CUSTOM = "custom"


class DesignCode(str, Enum):
    ASME_B31_3 = "ASME_B31_3"
    ASME_B31_9 = "ASME_B31_9"
    EN_13480 = "EN_13480"
    EN_12845 = "EN_12845"
    NFPA_13 = "NFPA_13"


class DimensionalCatalog(str, Enum):
    ASME_B36_10M = "ASME_B36_10M"
    ASME_B36_19M = "ASME_B36_19M"
    NBR_5580 = "NBR_5580"
    PVC_EN1452 = "PVC_EN1452"
    PVC_ASTMD1785 = "PVC_ASTMD1785"


class MaterialFamily(str, Enum):
    CARBON_STEEL = "carbon_steel"
    LOW_ALLOY_STEEL = "low_alloy_steel"
    STAINLESS_STEEL = "stainless_steel"
    COPPER = "copper"
    PVC = "pvc"
    HDPE = "hdpe"


class CheckerStatus(str, Enum):
    APPROVED = "APPROVED"
    CONSERVATIVE = "CONSERVATIVE"
    INSUFFICIENT = "INSUFFICIENT"
    CRITICAL = "CRITICAL"
    CODE_MISMATCH = "CODE_MISMATCH"
    DATASET_MISSING = "DATASET_MISSING"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    WARNING = "WARNING"


class FlowRateBasis(str, Enum):
    MASS = "kg/s"
    VOLUMETRIC = "m3/s"
    VOLUMETRIC_M3H = "m3/h"
    VOLUMETRIC_LS = "L/s"
    VOLUMETRIC_GPM = "gpm"
    NORMAL_M3H = "Nm3/h"   # gases: caudal normal (0°C, 1 atm)
    STANDARD_M3H = "Sm3/h"  # gases: caudal standard (15°C / 60°F, 1 atm)


class OperationMode(str, Enum):
    CALCULATE_NEW = "calculate_new"
    CHECK_RECEIVED = "check_received"
    BATCH_CSV = "batch_csv"


class WeldJointType(str, Enum):
    SEAMLESS = "seamless"
    ERW = "erw"
    SAW = "saw"
    FURNACE_WELDED = "furnace_welded"


class Jurisdiction(str, Enum):
    EU = "EU"
    US = "US"
    BRAZIL = "Brazil"
    INTERNATIONAL = "international"
    CUSTOM = "custom"
