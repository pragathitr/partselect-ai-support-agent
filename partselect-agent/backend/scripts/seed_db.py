"""
Seed the SQLite database with real PartSelect data.
Part numbers, names, mfr part numbers, and compatibility lists are sourced
from partselect.com, whirlpoolparts.com, and corroborating OEM retailers.

Run: python -m backend.scripts.seed_db
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.data import DB_PATH, get_connection, init_db

# ---------------------------------------------------------------------------
# Appliance categories
# ---------------------------------------------------------------------------

CATEGORIES = [
    # (id, slug, display_name, specialist_config_path, is_active)
    (1, "refrigerator", "Refrigerator", "config/specialists/refrigerator.yaml", 1),
    (2, "dishwasher",   "Dishwasher",   "config/specialists/dishwasher.yaml",   1),
    (3, "washer",       "Washer",       "config/specialists/washer.yaml",        0),
]

# ---------------------------------------------------------------------------
# Parts  (10 refrigerator + 10 dishwasher)
# Real data: PS numbers, names, mfr part numbers, prices from partselect.com.
# ---------------------------------------------------------------------------

PARTS = [
    # (part_number, name, category_id, brand, price, description, in_stock, image_url, mfr_part_number)

    # ===== REFRIGERATOR PARTS (10) =====

    # PS11752778 — confirmed via user: Door Shelf Bin (NOT a water filter)
    # Source: partselect.com/PS11752778-Whirlpool-WPW10321304-Refrigerator-Door-Shelf-Bin.htm
    ("PS11752778", "Refrigerator Door Shelf Bin", 1, "Whirlpool", 44.95,
     "Clear plastic door shelf bin, holds condiments and beverages in the refrigerator door. "
     "Tool-free installation — align tabs with door slots and snap into place. "
     "Compatible with Whirlpool and Maytag side-by-side refrigerators.",
     1, None, "WPW10321304"),

    # PS11752391 — Ice Maker Assembly
    # Source: partselect.com/PS11752391-Whirlpool-WPW10300024-Ice-Maker.htm
    ("PS11752391", "Refrigerator Ice Maker Assembly", 1, "Whirlpool", 129.28,
     "Complete ice maker assembly for Whirlpool French door refrigerators. "
     "Includes the motor, mold, and ejector. Does not include the shut-off arm, "
     "front cover, or wire harness — reuse existing components. Screwdriver required.",
     1, None, "WPW10300024"),

    # PS11775241 — Water Inlet Valve
    # Source: partselect.com/PS11775241-Whirlpool-W11043013-Water-Inlet-Valve.htm
    ("PS11775241", "Refrigerator Water Inlet Valve", 1, "Whirlpool", 95.26,
     "Water inlet valve controls water flow from the household supply line to the ice maker "
     "and water dispenser. Located at the back of the refrigerator. "
     "Replace if the ice maker or dispenser is not getting water.",
     1, None, "W11043013"),

    # PS11701542 — EveryDrop Water & Ice Filter (Filter 1)
    # Source: partselect.com/PS11701542-Whirlpool-EDR1RXD1-Refrigerator-Ice-and-Water-Filter.htm
    ("PS11701542", "EveryDrop Refrigerator Water & Ice Filter 1", 1, "Whirlpool", 54.99,
     "EveryDrop Filter 1 (EDR1RXD1). NSF/ANSI 42, 53, and 401 certified. "
     "Reduces lead, chlorine, and over 65 other contaminants. "
     "Replace every 6 months or 200 gallons. Push-in installation, no tools needed.",
     1, None, "EDR1RXD1"),

    # PS11759512 — Door Gasket (French door models)
    # Source: partselect.com/PS11759512-Whirlpool-W10830055-Gray-Refrigerator-Door-Gasket.htm
    ("PS11759512", "Refrigerator Door Gasket - Gray", 1, "Whirlpool", 171.06,
     "Gray magnetic door gasket for Whirlpool French door refrigerators. "
     "Seals the refrigerator compartment door to prevent warm air infiltration. "
     "Replace if the door feels loose, warm air enters, or the seal is cracked/torn.",
     1, None, "W10830055"),

    # PS11755867 — LED Light Control Board
    # Source: partselect.com/PS11755867-Whirlpool-WPW10515058-Refrigerator-LED-Light-Control-Board.htm
    ("PS11755867", "Refrigerator LED Light Control Board", 1, "Whirlpool", 37.91,
     "LED light control board for the refrigerator interior lighting system. "
     "Controls the LED light assembly. Replace if refrigerator lights are flickering, "
     "dim, or not turning on.",
     1, None, "WPW10515058"),

    # PS11752594 — Dual Water Inlet Valve
    # Source: partselect.com search result for WPW10312696
    ("PS11752594", "Refrigerator Dual Water Inlet Valve", 1, "Whirlpool", 33.25,
     "Dual-outlet water inlet valve releases water from the household supply line to "
     "both the water dispenser and the ice maker. Genuine OEM Whirlpool part.",
     1, None, "WPW10312696"),

    # PS11744215 — Evaporator Fan Motor
    # Source: partselect.com; mfr# WPW10189703 confirmed Whirlpool evaporator fan motor
    ("PS11744215", "Refrigerator Evaporator Fan Motor", 1, "Whirlpool", 45.99,
     "Evaporator fan motor and blade assembly. Circulates cold air through the "
     "refrigerator and freezer compartments. A failed motor causes the refrigerator "
     "to warm up and stop cooling properly. Replace if the fan is noisy or not running.",
     1, None, "WPW10189703"),

    # PS12347929 — Refrigerator Crisper Drawer
    # Source: partselect.com/PS12347929-Whirlpool-W11162443-Crisper-Drawer.htm
    # Confirmed compatible with WRS325SDHZ, WRS315SDHZ, WRS321SDHZ (side-by-side Whirlpool)
    ("PS12347929", "Refrigerator Crisper Drawer", 1, "Whirlpool", 54.99,
     "Clear plastic crisper drawer for the fresh food section of Whirlpool side-by-side "
     "refrigerators. Slides in and out on standard drawer rails. No tools required. "
     "Replaces W11046494. Fits WRS325SDHZ, WRS315SDHZ, WRS321SDHZ, and Maytag MSS25N4MKZ.",
     1, None, "W11162443"),

    # PS11739232 — Refrigerator Cold Control Thermostat
    # Source: partselect.com/PS11739232-Whirlpool-WP2198202-Refrigerator-Thermostat-Assembly.htm
    ("PS11739232", "Refrigerator Cold Control Thermostat", 1, "Whirlpool", 47.26,
     "Cold control thermostat assembly that cycles the compressor on and off to maintain "
     "set refrigerator temperature. "
     "Replace if the refrigerator runs continuously, does not cool, or gets too cold. "
     "Fits Whirlpool, Kenmore, Roper, and Estate side-by-side refrigerators.",
     1, None, "WP2198202"),

    # ===== DISHWASHER PARTS (10) =====

    # PS11756692 — Pump and Motor Assembly
    # Source: partselect.com/PS11756692-Whirlpool-WPW10605057-Dishwasher-Pump-and-Motor-Assembly.htm
    ("PS11756692", "Dishwasher Pump and Motor Assembly", 2, "Whirlpool", 188.97,
     "Complete pump, motor, and sump assembly including circulation pump and diverter motor. "
     "Circulates water through the spray arms during the wash cycle. "
     "Replace if the dishwasher is not washing, not draining, or making grinding noises.",
     1, None, "WPW10605057"),

    # PS11759673 — Dishwasher Filter (Pump Filter Cup)
    # Source: partselect.com/PS11759673-Whirlpool-W10872845-Dishwasher-Filter.htm
    ("PS11759673", "Dishwasher Pump Filter", 2, "Whirlpool", 48.45,
     "Gray plastic pump filter cup (drain filter), approximately 5 inches in diameter. "
     "Prevents debris from entering the pump and causing damage. "
     "Turn counterclockwise to remove, clockwise to install. Clean monthly; replace if cracked.",
     1, None, "W10872845"),

    # PS11750035 — Dishwasher Thermostat
    # Source: partselect.com/PS11750035-Whirlpool-WPW10195091-Dishwasher-Thermostat.htm
    ("PS11750035", "Dishwasher Thermostat", 2, "Whirlpool", 44.24,
     "High-limit thermostat that monitors and regulates the dishwasher heating element temperature. "
     "Prevents overheating during the wash and dry cycles. "
     "Replace if the dishwasher will not start, does not heat water, or trips its thermal fuse.",
     1, None, "WPW10195091"),

    # PS11756967 — Door Latch (Black)
    # Source: partselect.com/PS11756967-Whirlpool-WPW10653840-Door-Latch-Black.htm
    ("PS11756967", "Dishwasher Door Latch - Black", 2, "Whirlpool", 31.18,
     "Black door latch assembly that communicates with the control board when the door "
     "is closed and latched. The dishwasher will not start if the latch does not engage. "
     "Fixes symptoms: door not closing, dishwasher not starting, water leaking from door.",
     1, None, "WPW10653840"),

    # PS10065979 — Upper Rack Adjuster Kit
    # Source: partselect.com/PS10065979-Whirlpool-W10712395-Upper-Rack-Adjuster-Kit.htm
    ("PS10065979", "Dishwasher Upper Rack Adjuster Kit", 2, "Whirlpool", 41.76,
     "Upper dishrack adjuster kit with white wheels for left and right sides. "
     "Attaches the rack to the track, allowing it to slide in and out. "
     "Metal and plastic components. Includes wheels, actuators, and housing. Screwdriver required.",
     1, None, "W10712395"),

    # PS11751100 — Adjuster Arm Clip
    # Source: partselect.com/PS11751100-Whirlpool-WPW10250160-Adjuster-Arm-Clip.htm
    ("PS11751100", "Dishwasher Dishrack Adjuster Arm Clip", 2, "Whirlpool", 36.62,
     "Dishrack adjuster arm clip-lock assembly. Holds the adjuster to the dishrack. "
     "ABS plastic, heat-resistant to 250 degrees F. "
     "Replace if the upper rack is loose, sagging, or will not stay in position.",
     1, None, "WPW10250160"),

    # PS11731673 — Door Latch Assembly (different model range from PS11756967)
    # Source: partselect.com/PS11731673-Whirlpool-W10862259-Door-Latch-Assembly.htm
    ("PS11731673", "Dishwasher Door Latch Assembly with Switches", 2, "Whirlpool", 27.45,
     "Door latch and handle assembly with integrated micro-switches. "
     "Keeps the dishwasher door closed during operation and signals the control board "
     "when the door is fully latched. Compatible with Maytag, Amana, and Whirlpool models.",
     1, None, "W10862259"),

    # PS16875896 — Upper Rack Assembly
    # Source: partselect.com search snippet; Price: $192.89
    ("PS16875896", "Dishwasher Upper Rack Assembly", 2, "Whirlpool", 192.89,
     "Complete upper dishrack assembly replacement for Whirlpool dishwashers. "
     "Includes tines, rail glides, and adjustable cup shelf. "
     "Replace if the rack is bent, rusted, or the tines are broken.",
     1, None, None),

    # PS11755592 — Dishwasher Lower Spray Arm
    # Source: partselect.com/PS11755592-Whirlpool-WPW10491331-Dishwasher-Lower-Spray-Arm.htm
    # Confirmed compatible with WDT780SAEM1, WDT780SAEM2, WDT730PAHZ0
    ("PS11755592", "Dishwasher Lower Spray Arm", 2, "Whirlpool", 33.69,
     "Gray lower wash arm (~20 inches long) that rotates during the wash cycle to spray "
     "water onto the bottom rack dishes. Replace if the arm is cracked, has permanently "
     "blocked holes, or is not rotating — causing poor cleaning of bottom-rack items.",
     1, None, "WPW10491331"),

    # PS5136129 — Dishwasher Door Gasket with Strike - Black
    # Source: partselect.com/PS5136129-Whirlpool-W10542314-Dishwasher-Door-Gasket-with-Strike-Black.htm
    # Fits Whirlpool, Kenmore, Maytag, Amana, KitchenAid dishwashers.
    ("PS5136129", "Dishwasher Door Gasket with Strike - Black", 2, "Whirlpool", 59.47,
     "Black flexible door gasket and strike kit that seals the gap between the door and "
     "the tub during the wash cycle. The strike provides tension for a secure door seal. "
     "Replace if water is leaking from the door, or if the gasket is cracked or torn.",
     1, None, "W10542314"),
]

# ---------------------------------------------------------------------------
# Models  (20 refrigerator + 20 dishwasher)
# Real model numbers from PartSelect compatibility pages and Whirlpool catalog.
# ---------------------------------------------------------------------------

MODELS = [
    # (model_number, brand, category_id, display_name)

    # ===== REFRIGERATORS (20) =====

    # --- French door Whirlpool / Maytag / KitchenAid (key eval models first) ---
    ("WRF555SDFZ",   "Whirlpool",   1, "Whirlpool 25 cu ft French Door Refrigerator"),
    ("WRX735SDBM00", "Whirlpool",   1, "Whirlpool 25 cu ft French Door Refrigerator"),
    ("WRF535SWHZ01", "Whirlpool",   1, "Whirlpool 25 cu ft French Door Refrigerator"),
    ("WRF767SDHZ00", "Whirlpool",   1, "Whirlpool 27 cu ft French Door Refrigerator"),
    ("MFI2569VEM4",  "Maytag",      1, "Maytag 25.5 cu ft French Door Refrigerator"),
    ("MFX2570AEB4",  "Maytag",      1, "Maytag 25.2 cu ft French Door Refrigerator"),
    ("MFF2558FEZ00", "Maytag",      1, "Maytag 25.2 cu ft French Door Refrigerator"),
    ("KFXS25RYBL0",  "KitchenAid",  1, "KitchenAid 24.8 cu ft French Door Refrigerator"),
    ("KRFC300ESS01", "KitchenAid",  1, "KitchenAid 20 cu ft Counter-Depth French Door Refrigerator"),
    ("KRMF706ESS01", "KitchenAid",  1, "KitchenAid 26 cu ft French Door Refrigerator"),

    # --- Side-by-side Whirlpool (key eval models first) ---
    ("WRS325SDHZ",   "Whirlpool",   1, "Whirlpool 21.4 cu ft Side-by-Side Refrigerator"),
    ("WRS325FDAM04", "Whirlpool",   1, "Whirlpool 24.6 cu ft Side-by-Side Refrigerator"),
    ("WRS322FDAW03", "Whirlpool",   1, "Whirlpool 21.5 cu ft Side-by-Side Refrigerator"),
    ("WRS335FDDM01", "Whirlpool",   1, "Whirlpool 24.7 cu ft Side-by-Side Refrigerator"),
    ("WRS331FDDB00", "Whirlpool",   1, "Whirlpool 20 cu ft Side-by-Side Refrigerator"),
    ("WRS315SDHM01", "Whirlpool",   1, "Whirlpool 25 cu ft Side-by-Side Refrigerator"),
    ("WRS321SDHZ00", "Whirlpool",   1, "Whirlpool 21 cu ft Side-by-Side Refrigerator"),
    ("WRS586FIEM04", "Whirlpool",   1, "Whirlpool 26 cu ft Side-by-Side Refrigerator"),
    ("WRS325FDAM03", "Whirlpool",   1, "Whirlpool 24.5 cu ft Side-by-Side Refrigerator"),

    # --- Bottom freezer ---
    ("WRB322DMBM00", "Whirlpool",   1, "Whirlpool 21.4 cu ft Bottom Freezer Refrigerator"),

    # ===== DISHWASHERS (20) =====

    # --- Whirlpool WDT series (key eval models first) ---
    ("WDT780SAEM1",  "Whirlpool",   2, "Whirlpool 24 in Built-In Dishwasher with Fan Dry"),
    ("WDT780SAEM0",  "Whirlpool",   2, "Whirlpool 24 in Built-In Dishwasher with Fan Dry"),
    ("WDT780SAEM2",  "Whirlpool",   2, "Whirlpool 24 in Built-In Dishwasher with Fan Dry"),
    ("WDT710PAHZ",   "Whirlpool",   2, "Whirlpool 24 in Dishwasher with Sensor Cycle"),
    ("WDT710PAHB",   "Whirlpool",   2, "Whirlpool 24 in Dishwasher with Sensor Cycle"),
    ("WDT790SAYB3",  "Whirlpool",   2, "Whirlpool 24 in Dishwasher"),
    ("WDT750SAHZ0",  "Whirlpool",   2, "Whirlpool 24 in Dishwasher with Soil Sensor"),
    ("WDT730PAHZ0",  "Whirlpool",   2, "Whirlpool 24 in Dishwasher with Soil Sensor"),
    ("WDT970SAKZ0",  "Whirlpool",   2, "Whirlpool 24 in Dishwasher with 3rd Level Rack"),
    ("WDTA50SAHZ0",  "Whirlpool",   2, "Whirlpool 24 in Dishwasher with Fan Dry"),

    # --- Whirlpool WDF series ---
    ("WDF560SAFM0",  "Whirlpool",   2, "Whirlpool 24 in Dishwasher"),
    ("WDF750SAYT3",  "Whirlpool",   2, "Whirlpool 24 in Dishwasher with Fan Dry"),
    ("WDF330PAHW0",  "Whirlpool",   2, "Whirlpool 24 in Portable Dishwasher"),

    # --- KitchenAid ---
    ("KDTE104ESS1",  "KitchenAid",  2, "KitchenAid 24 in Built-In Dishwasher"),
    ("KDTM354ESS1",  "KitchenAid",  2, "KitchenAid 24 in Dishwasher with 3rd Level Rack"),
    ("KDTE204EPA0",  "KitchenAid",  2, "KitchenAid 24 in Built-In Dishwasher"),

    # --- Maytag ---
    ("MDB8959SKZ0",  "Maytag",      2, "Maytag 24 in Dishwasher with Dual Power Filtration"),
    ("MDB4949SKZ0",  "Maytag",      2, "Maytag 24 in Dishwasher"),

    # --- Amana ---
    ("ADB1700ADB1",  "Amana",       2, "Amana 24 in Built-In Dishwasher"),
    ("ADB1500ADB3",  "Amana",       2, "Amana 24 in Built-In Dishwasher"),
]

# ---------------------------------------------------------------------------
# Compatibility edges
# IMPORTANT: No cross-appliance edges — refrigerator parts map only to
# refrigerator models, and vice versa. This is what makes cross-appliance
# detection work in check_compatibility (E04, E24 eval tests).
# ---------------------------------------------------------------------------

COMPATIBILITY = [
    # (part_number, model_number, confidence)

    # ===== PS11752778 (Door Shelf Bin) → Side-by-Side Refrigerators =====
    # This part is for SIDE-BY-SIDE models ONLY — NOT French door (WRF555SDFZ).
    ("PS11752778", "WRS325FDAM04", "confirmed"),
    ("PS11752778", "WRS322FDAW03", "confirmed"),
    ("PS11752778", "WRS335FDDM01", "confirmed"),
    ("PS11752778", "WRS331FDDB00", "confirmed"),
    ("PS11752778", "WRS325SDHZ",   "inferred"),
    ("PS11752778", "WRS315SDHM01", "confirmed"),
    ("PS11752778", "WRS321SDHZ00", "inferred"),
    ("PS11752778", "WRS586FIEM04", "inferred"),
    ("PS11752778", "WRS325FDAM03", "confirmed"),

    # ===== PS11752391 (Ice Maker) → French Door Refrigerators =====
    ("PS11752391", "WRF555SDFZ",   "confirmed"),
    ("PS11752391", "WRX735SDBM00", "inferred"),
    ("PS11752391", "MFI2569VEM4",  "confirmed"),
    ("PS11752391", "MFX2570AEB4",  "confirmed"),
    ("PS11752391", "WRF535SWHZ01", "confirmed"),
    ("PS11752391", "WRF767SDHZ00", "inferred"),
    ("PS11752391", "MFF2558FEZ00", "inferred"),
    ("PS11752391", "KRFC300ESS01", "inferred"),
    ("PS11752391", "KRMF706ESS01", "inferred"),

    # ===== PS11775241 (Water Inlet Valve) → French Door Refrigerators =====
    ("PS11775241", "WRF555SDFZ",   "confirmed"),
    ("PS11775241", "WRX735SDBM00", "confirmed"),
    ("PS11775241", "MFX2570AEB4",  "confirmed"),
    ("PS11775241", "KFXS25RYBL0",  "confirmed"),
    ("PS11775241", "MFI2569VEM4",  "inferred"),
    ("PS11775241", "WRF535SWHZ01", "confirmed"),
    ("PS11775241", "WRF767SDHZ00", "inferred"),
    ("PS11775241", "KRFC300ESS01", "inferred"),
    ("PS11775241", "KRMF706ESS01", "inferred"),
    ("PS11775241", "MFF2558FEZ00", "inferred"),

    # ===== PS11701542 (Water Filter) → French Door Refrigerators =====
    ("PS11701542", "WRF555SDFZ",   "confirmed"),
    ("PS11701542", "WRX735SDBM00", "confirmed"),
    ("PS11701542", "MFX2570AEB4",  "confirmed"),
    ("PS11701542", "KFXS25RYBL0",  "confirmed"),
    ("PS11701542", "MFI2569VEM4",  "inferred"),
    ("PS11701542", "WRF535SWHZ01", "confirmed"),
    ("PS11701542", "WRF767SDHZ00", "inferred"),
    ("PS11701542", "MFF2558FEZ00", "inferred"),
    ("PS11701542", "KRFC300ESS01", "confirmed"),
    ("PS11701542", "KRMF706ESS01", "inferred"),

    # ===== PS11759512 (Door Gasket) → French Door Refrigerators =====
    ("PS11759512", "WRF555SDFZ",   "confirmed"),
    ("PS11759512", "WRX735SDBM00", "inferred"),
    ("PS11759512", "MFX2570AEB4",  "confirmed"),
    ("PS11759512", "MFI2569VEM4",  "confirmed"),
    ("PS11759512", "KFXS25RYBL0",  "inferred"),
    ("PS11759512", "WRF535SWHZ01", "confirmed"),
    ("PS11759512", "WRF767SDHZ00", "inferred"),
    ("PS11759512", "KRFC300ESS01", "inferred"),
    ("PS11759512", "KRMF706ESS01", "inferred"),
    ("PS11759512", "MFF2558FEZ00", "inferred"),

    # ===== PS11755867 (LED Light Board) → French Door Refrigerators =====
    ("PS11755867", "WRF555SDFZ",   "inferred"),
    ("PS11755867", "WRX735SDBM00", "inferred"),
    ("PS11755867", "MFX2570AEB4",  "inferred"),
    ("PS11755867", "WRF535SWHZ01", "inferred"),
    ("PS11755867", "WRF767SDHZ00", "inferred"),

    # ===== PS11752594 (Dual Inlet Valve) → French Door Refrigerators =====
    ("PS11752594", "WRF555SDFZ",   "confirmed"),
    ("PS11752594", "WRX735SDBM00", "inferred"),
    ("PS11752594", "MFX2570AEB4",  "confirmed"),
    ("PS11752594", "MFI2569VEM4",  "confirmed"),
    ("PS11752594", "WRF535SWHZ01", "inferred"),
    ("PS11752594", "KRMF706ESS01", "inferred"),

    # ===== PS11744215 (Evaporator Fan Motor) → Multiple Refrigerators =====
    ("PS11744215", "WRF555SDFZ",   "confirmed"),
    ("PS11744215", "WRS325SDHZ",   "inferred"),
    ("PS11744215", "WRX735SDBM00", "confirmed"),
    ("PS11744215", "MFX2570AEB4",  "inferred"),
    ("PS11744215", "WRS315SDHM01", "inferred"),
    ("PS11744215", "WRS321SDHZ00", "inferred"),
    ("PS11744215", "WRS586FIEM04", "inferred"),
    ("PS11744215", "WRF535SWHZ01", "confirmed"),
    ("PS11744215", "WRF767SDHZ00", "inferred"),

    # ===== PS12347929 (Crisper Drawer, W11162443) → Side-by-Side Refrigerators ONLY =====
    # W11162443 is a side-by-side crisper drawer — does NOT fit French door models.
    ("PS12347929", "WRS325SDHZ",   "confirmed"),
    ("PS12347929", "WRS315SDHM01", "confirmed"),
    ("PS12347929", "WRS321SDHZ00", "confirmed"),
    ("PS12347929", "WRS325FDAM03", "inferred"),
    ("PS12347929", "WRS325FDAM04", "inferred"),
    ("PS12347929", "WRS322FDAW03", "inferred"),
    ("PS12347929", "WRS335FDDM01", "inferred"),
    ("PS12347929", "WRS331FDDB00", "inferred"),
    ("PS12347929", "WRS586FIEM04", "inferred"),

    # ===== PS11739232 (Cold Control Thermostat, WP2198202) → Side-by-Side Refrigerators =====
    # WP2198202 fits Whirlpool, Kenmore, Roper, Estate side-by-side models.
    # Not confirmed for specific WRS-series (newer platform) — all edges inferred.
    ("PS11739232", "WRS325SDHZ",   "inferred"),
    ("PS11739232", "WRS325FDAM04", "inferred"),
    ("PS11739232", "WRS322FDAW03", "inferred"),
    ("PS11739232", "WRS335FDDM01", "inferred"),
    ("PS11739232", "WRS315SDHM01", "inferred"),
    ("PS11739232", "WRS321SDHZ00", "inferred"),
    ("PS11739232", "WRS586FIEM04", "inferred"),
    ("PS11739232", "WRS325FDAM03", "inferred"),
    ("PS11739232", "WRB322DMBM00", "inferred"),

    # ===== DISHWASHER PARTS =====

    # ===== PS11756692 (Pump and Motor) → Whirlpool / KitchenAid Dishwashers =====
    ("PS11756692", "WDT780SAEM1",  "confirmed"),
    ("PS11756692", "WDT780SAEM0",  "confirmed"),
    ("PS11756692", "WDT780SAEM2",  "confirmed"),
    ("PS11756692", "WDT710PAHZ",   "confirmed"),
    ("PS11756692", "WDT710PAHB",   "confirmed"),
    ("PS11756692", "WDF560SAFM0",  "confirmed"),
    ("PS11756692", "WDF750SAYT3",  "confirmed"),
    ("PS11756692", "WDT790SAYB3",  "confirmed"),
    ("PS11756692", "KDTE104ESS1",  "confirmed"),
    ("PS11756692", "WDT750SAHZ0",  "confirmed"),
    ("PS11756692", "WDT730PAHZ0",  "confirmed"),
    ("PS11756692", "WDT970SAKZ0",  "inferred"),
    ("PS11756692", "WDTA50SAHZ0",  "inferred"),
    ("PS11756692", "KDTM354ESS1",  "confirmed"),
    ("PS11756692", "KDTE204EPA0",  "confirmed"),
    ("PS11756692", "MDB8959SKZ0",  "inferred"),

    # ===== PS11759673 (Filter) → Whirlpool Dishwashers =====
    ("PS11759673", "WDT780SAEM1",  "confirmed"),
    ("PS11759673", "WDT780SAEM0",  "confirmed"),
    ("PS11759673", "WDT780SAEM2",  "confirmed"),
    ("PS11759673", "WDT710PAHZ",   "confirmed"),
    ("PS11759673", "WDF750SAYT3",  "inferred"),
    ("PS11759673", "KDTE104ESS1",  "inferred"),
    ("PS11759673", "WDT750SAHZ0",  "confirmed"),
    ("PS11759673", "WDT730PAHZ0",  "confirmed"),
    ("PS11759673", "WDT970SAKZ0",  "confirmed"),
    ("PS11759673", "WDTA50SAHZ0",  "inferred"),
    ("PS11759673", "KDTM354ESS1",  "confirmed"),

    # ===== PS11750035 (Thermostat) → Multiple Brands =====
    ("PS11750035", "WDT780SAEM1",  "confirmed"),
    ("PS11750035", "WDT790SAYB3",  "confirmed"),
    ("PS11750035", "ADB1700ADB1",  "confirmed"),
    ("PS11750035", "KDTE104ESS1",  "confirmed"),
    ("PS11750035", "WDF560SAFM0",  "inferred"),
    ("PS11750035", "WDT750SAHZ0",  "inferred"),
    ("PS11750035", "WDTA50SAHZ0",  "inferred"),
    ("PS11750035", "MDB8959SKZ0",  "inferred"),
    ("PS11750035", "MDB4949SKZ0",  "inferred"),
    ("PS11750035", "ADB1500ADB3",  "confirmed"),

    # ===== PS11756967 (Door Latch Black) → Whirlpool / KitchenAid =====
    ("PS11756967", "WDT780SAEM1",  "confirmed"),
    ("PS11756967", "WDT780SAEM0",  "confirmed"),
    ("PS11756967", "WDT780SAEM2",  "confirmed"),
    ("PS11756967", "WDF750SAYT3",  "confirmed"),
    ("PS11756967", "KDTE104ESS1",  "confirmed"),
    ("PS11756967", "WDT710PAHZ",   "inferred"),
    ("PS11756967", "WDT750SAHZ0",  "confirmed"),
    ("PS11756967", "WDT730PAHZ0",  "confirmed"),
    ("PS11756967", "MDB8959SKZ0",  "inferred"),

    # ===== PS10065979 (Upper Rack Adjuster Kit) =====
    ("PS10065979", "WDT780SAEM1",  "confirmed"),
    ("PS10065979", "WDT780SAEM2",  "confirmed"),
    ("PS10065979", "WDT710PAHZ",   "confirmed"),
    ("PS10065979", "WDT790SAYB3",  "confirmed"),
    ("PS10065979", "KDTE104ESS1",  "confirmed"),
    ("PS10065979", "WDF750SAYT3",  "inferred"),
    ("PS10065979", "WDT750SAHZ0",  "confirmed"),
    ("PS10065979", "WDT730PAHZ0",  "confirmed"),
    ("PS10065979", "WDTA50SAHZ0",  "inferred"),

    # ===== PS11751100 (Adjuster Arm Clip) =====
    ("PS11751100", "WDT780SAEM1",  "confirmed"),
    ("PS11751100", "WDT780SAEM0",  "confirmed"),
    ("PS11751100", "KDTE104ESS1",  "confirmed"),
    ("PS11751100", "ADB1700ADB1",  "inferred"),
    ("PS11751100", "WDT750SAHZ0",  "inferred"),

    # ===== PS11731673 (Door Latch Assembly) =====
    ("PS11731673", "WDT710PAHZ",   "confirmed"),
    ("PS11731673", "WDF560SAFM0",  "confirmed"),
    ("PS11731673", "ADB1700ADB1",  "confirmed"),
    ("PS11731673", "WDT780SAEM1",  "inferred"),
    ("PS11731673", "MDB4949SKZ0",  "inferred"),
    ("PS11731673", "ADB1500ADB3",  "confirmed"),

    # ===== PS16875896 (Upper Rack Assembly) =====
    ("PS16875896", "WDT780SAEM1",  "confirmed"),
    ("PS16875896", "WDT780SAEM0",  "confirmed"),
    ("PS16875896", "WDT780SAEM2",  "confirmed"),
    ("PS16875896", "WDT710PAHZ",   "inferred"),

    # ===== PS11755592 (Lower Spray Arm, WPW10491331) → Whirlpool / KitchenAid Dishwashers =====
    ("PS11755592", "WDT780SAEM1",  "confirmed"),
    ("PS11755592", "WDT780SAEM0",  "confirmed"),
    ("PS11755592", "WDT780SAEM2",  "confirmed"),
    ("PS11755592", "WDT710PAHZ",   "confirmed"),
    ("PS11755592", "WDT750SAHZ0",  "confirmed"),
    ("PS11755592", "WDT730PAHZ0",  "confirmed"),
    ("PS11755592", "WDT970SAKZ0",  "inferred"),
    ("PS11755592", "WDTA50SAHZ0",  "inferred"),
    ("PS11755592", "KDTM354ESS1",  "confirmed"),
    ("PS11755592", "KDTE204EPA0",  "inferred"),

    # ===== PS5136129 (Door Gasket with Strike, W10542314) → Whirlpool / Amana Dishwashers =====
    ("PS5136129", "WDT780SAEM1",  "confirmed"),
    ("PS5136129", "WDT780SAEM0",  "confirmed"),
    ("PS5136129", "WDT780SAEM2",  "confirmed"),
    ("PS5136129", "WDT750SAHZ0",  "confirmed"),
    ("PS5136129", "WDT730PAHZ0",  "confirmed"),
    ("PS5136129", "WDT710PAHZ",   "inferred"),
    ("PS5136129", "WDF560SAFM0",  "inferred"),
    ("PS5136129", "WDTA50SAHZ0",  "inferred"),
    ("PS5136129", "MDB8959SKZ0",  "inferred"),
    ("PS5136129", "ADB1500ADB3",  "inferred"),
    ("PS5136129", "WDF330PAHW0",  "inferred"),
]

# ---------------------------------------------------------------------------
# Symptoms  (5 refrigerator + 5 dishwasher)
# ---------------------------------------------------------------------------

SYMPTOMS = [
    # (id, description, category_id, is_safety_critical)
    ("SY_FRIDGE_ICE_MAKER_FAIL",  "Ice maker not producing ice",            1, 0),
    ("SY_FRIDGE_NOT_COOLING",     "Refrigerator not cooling properly",      1, 0),
    ("SY_FRIDGE_WATER_DISPENSER", "Water dispenser not working",            1, 0),
    ("SY_FRIDGE_DOOR_SEAL",       "Door seal or gasket issue",              1, 0),
    ("SY_FRIDGE_LIGHT",           "Refrigerator interior light not working", 1, 0),
    ("SY_DW_NOT_DRAINING",        "Dishwasher not draining after cycle",    2, 0),
    ("SY_DW_NOT_CLEANING",        "Dishes not getting clean",               2, 0),
    ("SY_DW_NOT_STARTING",        "Dishwasher will not start",              2, 0),
    ("SY_DW_LEAKING",             "Water leaking from dishwasher",          2, 0),
    ("SY_DW_NOT_FILLING",         "Dishwasher not filling with water",      2, 0),
]

# ---------------------------------------------------------------------------
# Symptom -> Part fixes
# ---------------------------------------------------------------------------

SYMPTOM_FIXES = [
    # (symptom_id, part_number, rank)
    # Refrigerator
    ("SY_FRIDGE_ICE_MAKER_FAIL",  "PS11752391", 1),  # Ice Maker Assembly
    ("SY_FRIDGE_ICE_MAKER_FAIL",  "PS11775241", 2),  # Water Inlet Valve (no water -> no ice)
    ("SY_FRIDGE_ICE_MAKER_FAIL",  "PS11701542", 3),  # Water Filter (clogged -> reduced flow)
    ("SY_FRIDGE_NOT_COOLING",     "PS11744215", 1),  # Evaporator Fan Motor
    ("SY_FRIDGE_NOT_COOLING",     "PS11775241", 2),  # Water Inlet Valve
    ("SY_FRIDGE_NOT_COOLING",     "PS11739232", 3),  # Cold Control Thermostat
    ("SY_FRIDGE_WATER_DISPENSER", "PS11701542", 1),  # Water Filter (most common cause)
    ("SY_FRIDGE_WATER_DISPENSER", "PS11775241", 2),  # Water Inlet Valve
    ("SY_FRIDGE_WATER_DISPENSER", "PS11752594", 3),  # Dual Inlet Valve
    ("SY_FRIDGE_DOOR_SEAL",       "PS11759512", 1),  # Door Gasket
    ("SY_FRIDGE_LIGHT",           "PS11755867", 1),  # LED Light Control Board

    # Dishwasher
    ("SY_DW_NOT_DRAINING",        "PS11756692", 1),  # Pump and Motor
    ("SY_DW_NOT_DRAINING",        "PS11759673", 2),  # Filter (clogged)
    ("SY_DW_NOT_CLEANING",        "PS11756692", 1),  # Pump and Motor (weak wash pressure)
    ("SY_DW_NOT_CLEANING",        "PS10065979", 2),  # Rack Adjuster (blocked spray arm path)
    ("SY_DW_NOT_CLEANING",        "PS11755592", 3),  # Lower Spray Arm (cracked / blocked holes)
    ("SY_DW_NOT_STARTING",        "PS11756967", 1),  # Door Latch Black
    ("SY_DW_NOT_STARTING",        "PS11731673", 2),  # Door Latch Assembly (alt model)
    ("SY_DW_NOT_STARTING",        "PS11750035", 3),  # Thermostat (tripped)
    ("SY_DW_LEAKING",             "PS11756692", 1),  # Pump/Motor seal failure
    ("SY_DW_LEAKING",             "PS11751100", 2),  # Adjuster Arm Clip (rack misaligned)
    ("SY_DW_LEAKING",             "PS5136129",  3),  # Door Gasket with Strike
    ("SY_DW_NOT_FILLING",         "PS11750035", 1),  # Thermostat (affects fill cycle)
    ("SY_DW_NOT_FILLING",         "PS11759673", 2),  # Filter (restricted flow)
]

# ---------------------------------------------------------------------------
# Install guides  (7 parts covered)
# ---------------------------------------------------------------------------

INSTALL_GUIDES = [
    # (part_number, step_order, instruction, tool_required, safety_note)

    # PS11752778 — Door Shelf Bin (2 steps, tool-free)
    ("PS11752778", 1,
     "Grip the old shelf bin with both hands and push it upward to disengage the bottom tabs, "
     "then pull it straight out from the door.",
     None, "Have someone hold the refrigerator door steady to avoid strain on hinges."),
    ("PS11752778", 2,
     "Align the tabs on the new shelf bin with the door slots. Push firmly downward until "
     "you feel the tabs click into place. Give it a gentle tug to confirm it is seated.",
     None, None),

    # PS11701542 — EveryDrop Water Filter (5 steps)
    ("PS11701542", 1,
     "Locate the water filter in the base grille at the bottom-left of the refrigerator "
     "(French door models) or in the upper right interior (some side-by-side models).",
     None, "Turn off the water supply at the wall if directed by your model's manual."),
    ("PS11701542", 2,
     "Press the eject button (if present) or turn the old filter a quarter turn "
     "counterclockwise and pull it straight out.",
     None, "Have a towel ready — a small amount of water may drip when removing the filter."),
    ("PS11701542", 3,
     "Remove the protective cap from the new filter by pulling it straight off.",
     None, None),
    ("PS11701542", 4,
     "Insert the new filter and push in firmly, then rotate clockwise until it locks "
     "into place. You will feel resistance and hear a click.",
     None, "Do not overtighten — stop when you feel the click."),
    ("PS11701542", 5,
     "Dispense and discard 3-5 gallons of water to flush air and carbon fines "
     "from the new filter before drinking.",
     None, "Discard the first 1-2 gallons. Filtered water will run slightly grey at first — this is normal."),

    # PS11752391 — Ice Maker Assembly (4 steps)
    ("PS11752391", 1,
     "Unplug the refrigerator from the wall outlet and turn off the water supply valve "
     "behind the refrigerator.",
     None, "Always disconnect power before servicing internal components."),
    ("PS11752391", 2,
     "Pull out and remove the ice bin. Disconnect the wire harness connector and the "
     "water supply tube from the old ice maker unit.",
     "Flat-head screwdriver", "Press the release tab on the wire harness before pulling to avoid damaging the connector."),
    ("PS11752391", 3,
     "Remove the mounting screws securing the ice maker to the freezer wall, "
     "then lift and pull the old unit out.",
     "Phillips screwdriver", None),
    ("PS11752391", 4,
     "Mount the new ice maker, reconnect the wire harness and water supply tube, "
     "then restore power and water. Allow 24 hours for full ice production to begin.",
     "Phillips screwdriver", "Ensure the water tube connection is tight to prevent freezer leaks."),

    # PS11759512 — Refrigerator Door Gasket (4 steps)
    ("PS11759512", 1,
     "Soak the new gasket in warm water for 10 minutes to make it pliable and easier to seat.",
     None, None),
    ("PS11759512", 2,
     "Open the refrigerator door fully. Starting at a top corner, peel back the old gasket "
     "by pulling the lip away from the door liner.",
     None, "The door may be lighter and harder to hold open without the gasket — use a prop if needed."),
    ("PS11759512", 3,
     "Work around the door, pulling the old gasket completely off. Clean the gasket channel "
     "with warm soapy water and dry thoroughly.",
     None, None),
    ("PS11759512", 4,
     "Press the lip of the new gasket into the channel starting at a corner, then work around "
     "the perimeter until fully seated. Close the door and test with a dollar bill at multiple "
     "points — it should offer resistance when pulled.",
     None, "If the gasket leaks cold air after installation, use a heat gun on low to reshape the gasket into the channel."),

    # PS11756692 — Dishwasher Pump and Motor (4 steps)
    ("PS11756692", 1,
     "Turn off the dishwasher circuit breaker and shut off the water supply valve under the sink.",
     None, "Verify power is off with a non-contact voltage tester before proceeding."),
    ("PS11756692", 2,
     "Remove the lower dish rack. Unscrew the lower spray arm (turn counterclockwise). "
     "Remove the filter assembly by turning counterclockwise and lifting out.",
     "Torx T20 bit", "Place a towel under the tub to absorb residual water."),
    ("PS11756692", 3,
     "Disconnect the pump wiring harness and drain hose. Remove the pump mounting screws "
     "and lift the old pump assembly out of the sump.",
     "Phillips screwdriver, pliers", "Take a photo of hose connections before disconnecting for reference."),
    ("PS11756692", 4,
     "Place the new pump into the sump, secure the mounting screws, reconnect the wiring "
     "harness and drain hose, then reassemble the filter and spray arm. Restore power and water.",
     "Phillips screwdriver, pliers", "Ensure all hose clamps are fully tightened before running the first cycle."),

    # PS11756967 — Dishwasher Door Latch Black (3 steps)
    ("PS11756967", 1,
     "Turn off the dishwasher at the circuit breaker. Open the door fully.",
     None, "Use a non-contact voltage tester to verify power is off."),
    ("PS11756967", 2,
     "Remove the screws along the top edge and sides of the inner door panel. "
     "Lift the inner panel away from the outer door shell to expose the latch assembly.",
     "Phillips screwdriver", "Support the inner panel to prevent it from falling and damaging the control panel."),
    ("PS11756967", 3,
     "Disconnect the wiring harness from the old latch. Unscrew the latch, install the new "
     "latch, reconnect the wiring, and reassemble the door panels.",
     "Phillips screwdriver", "Close and test the door before restoring power to confirm the latch engages correctly."),

    # PS11755592 — Dishwasher Lower Spray Arm (3 steps)
    ("PS11755592", 1,
     "Remove the bottom dish rack. The lower spray arm sits in the center of the tub floor. "
     "Lift it straight up or turn the center hub counterclockwise to remove (varies by model).",
     None, None),
    ("PS11755592", 2,
     "Inspect the old spray arm — check for cracks, broken holes, or lime/debris blockage. "
     "If reusable, flush holes with warm water; if cracked or permanently blocked, replace.",
     None, None),
    ("PS11755592", 3,
     "Place the new spray arm onto the center post and press down or rotate clockwise until it "
     "locks. Spin it by hand to confirm it rotates freely. Replace the bottom rack and run a cycle.",
     None, "Confirm the spray arm can spin a full 360 degrees without hitting the tub or rack components."),
]

# ---------------------------------------------------------------------------
# Mock orders
# Order #12345 must exist — referenced in eval test E11.
# ---------------------------------------------------------------------------

ORDERS = [
    # (order_id, part_number, status, tracking_number, estimated_delivery, customer_email)
    ("12345", "PS11752391", "shipped",    "1Z999AA10123456784",     "2026-06-03", "demo@example.com"),
    ("12346", "PS11701542", "processing", None,                      "2026-06-05", "demo@example.com"),
    ("12347", "PS11759512", "delivered",  "9400111899223085782910",  "2026-05-27", "customer@example.com"),
    ("12348", "PS11756692", "shipped",    "1Z999AA10234567895",      "2026-06-04", "shopper@example.com"),
    ("12349", "PS11756967", "processing", None,                      "2026-06-06", "parts@example.com"),
]


# ---------------------------------------------------------------------------
# Seed runner
# ---------------------------------------------------------------------------

def seed(db_path=DB_PATH) -> None:
    print(f"Initializing database at: {db_path}")
    init_db(db_path)

    with get_connection(db_path) as conn:
        # Clear in dependency order (child tables first)
        for tbl in ("orders", "install_guides", "symptom_fixes", "symptoms",
                    "compatibility", "models", "parts", "appliance_categories"):
            conn.execute(f"DELETE FROM {tbl}")

        conn.executemany(
            "INSERT INTO appliance_categories VALUES (?,?,?,?,?)", CATEGORIES)
        print(f"  {len(CATEGORIES)} appliance categories")

        conn.executemany(
            "INSERT INTO parts VALUES (?,?,?,?,?,?,?,?,?)", PARTS)
        fridge_parts = sum(1 for p in PARTS if p[2] == 1)
        dw_parts     = sum(1 for p in PARTS if p[2] == 2)
        print(f"  {len(PARTS)} parts ({fridge_parts} fridge, {dw_parts} dishwasher)")

        conn.executemany(
            "INSERT INTO models VALUES (?,?,?,?)", MODELS)
        fridge_models = sum(1 for m in MODELS if m[2] == 1)
        dw_models     = sum(1 for m in MODELS if m[2] == 2)
        print(f"  {len(MODELS)} models ({fridge_models} fridge, {dw_models} dishwasher)")

        conn.executemany(
            "INSERT INTO compatibility VALUES (?,?,?)", COMPATIBILITY)
        print(f"  {len(COMPATIBILITY)} compatibility edges")

        conn.executemany(
            "INSERT INTO symptoms VALUES (?,?,?,?)", SYMPTOMS)
        print(f"  {len(SYMPTOMS)} symptoms")

        conn.executemany(
            "INSERT INTO symptom_fixes VALUES (?,?,?)", SYMPTOM_FIXES)
        print(f"  {len(SYMPTOM_FIXES)} symptom->fix edges")

        conn.executemany(
            "INSERT INTO install_guides VALUES (?,?,?,?,?)", INSTALL_GUIDES)
        guide_parts = len({ig[0] for ig in INSTALL_GUIDES})
        print(f"  {len(INSTALL_GUIDES)} install guide steps across {guide_parts} parts")

        conn.executemany(
            """
            INSERT INTO orders (
                order_id,
                part_number,
                status,
                tracking_number,
                estimated_delivery,
                customer_email
            )
            VALUES (?,?,?,?,?,?)
            """,
            ORDERS,
        )
        print(f"  {len(ORDERS)} mock orders")

        conn.commit()

    print("Seed complete.")


if __name__ == "__main__":
    seed()
