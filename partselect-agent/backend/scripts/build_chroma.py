"""
Build the Chroma vector store from hardcoded repair articles.
Run: python -m backend.scripts.build_chroma

Requires OPENAI_API_KEY in environment (text-embedding-3-small).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from backend.data.chroma import get_client, COLLECTION_NAME

REPAIR_ARTICLES = [
    {
        "id": "RA01",
        "content": (
            "How to fix an ice maker that has stopped making ice on a Whirlpool refrigerator. "
            "Common causes include a faulty ice maker assembly (PS11752391, OEM WPW10300024), "
            "a clogged or expired water filter (PS11701542, EveryDrop Filter 1), "
            "or a defective water inlet valve (PS11775241, W11043013). "
            "Start by replacing the water filter if it has been more than 6 months. "
            "Verify the ice maker switch is on. "
            "If ice production does not resume, the ice maker assembly itself likely needs replacement. "
            "Part PS11752391 is compatible with Whirlpool WRF555SDFZ and other French door models."
        ),
        "metadata": {"appliance_type": "refrigerator", "symptom": "ice_maker_fail"},
    },
    {
        "id": "RA02",
        "content": (
            "Whirlpool refrigerator water filter replacement guide. The EveryDrop Filter 1 "
            "(PS11701542, OEM EDR1RXD1) is NSF 42/53/401 certified and should be replaced every "
            "6 months or 200 gallons. Located in the base grille (French door) or upper interior "
            "(some side-by-side models). Push in and rotate clockwise to install. "
            "Flush 3–5 gallons of water before drinking. "
            "Compatible with WRF555SDFZ, WRX735SDBM00, and many other Whirlpool French door refrigerators. "
            "Note: PS11752778 (WPW10321304) is a door shelf bin, not a water filter."
        ),
        "metadata": {"appliance_type": "refrigerator", "symptom": "water_filter"},
    },
    {
        "id": "RA03",
        "content": (
            "Refrigerator not cooling properly — troubleshooting guide. "
            "Start by checking the evaporator fan motor (PS11744215, WPW10189703). "
            "If the fan is not running, cold air cannot circulate and the refrigerator will warm up. "
            "Also check the water inlet valve (PS11775241) as a related supply component. "
            "Clean the condenser coils at the back or bottom of the refrigerator if dusty. "
            "Part PS11744215 fits Whirlpool WRF555SDFZ and WRX735SDBM00 models."
        ),
        "metadata": {"appliance_type": "refrigerator", "symptom": "not_cooling"},
    },
    {
        "id": "RA04",
        "content": (
            "Refrigerator water dispenser not working. The most common cause is a clogged or expired "
            "water filter — replace PS11701542 (EveryDrop Filter 1) first. "
            "If that does not fix it, the water inlet valve may be defective: "
            "PS11775241 (W11043013) controls water flow to both the dispenser and the ice maker, "
            "or PS11752594 (WPW10312696) for dual-outlet models. "
            "Verify household water pressure is at least 20 PSI. "
            "These valves are compatible with WRF555SDFZ, MFX2570AEB4, and KFXS25RYBL0."
        ),
        "metadata": {"appliance_type": "refrigerator", "symptom": "water_dispenser"},
    },
    {
        "id": "RA05",
        "content": (
            "Refrigerator door gasket and seal replacement guide. A worn gasket lets warm air in, "
            "causing the compressor to overwork. Test with a dollar bill — if it slips out easily, "
            "replace the gasket. Part PS11759512 (W10830055) is the gray door gasket for Whirlpool "
            "French door refrigerators including WRF555SDFZ, MFX2570AEB4, and MFI2569VEM4. "
            "Soak the new gasket in warm water 10 minutes before installing. "
            "Note: PS11752778 is a door shelf bin (not related to door sealing)."
        ),
        "metadata": {"appliance_type": "refrigerator", "symptom": "door_seal"},
    },
    {
        "id": "RA06",
        "content": (
            "Dishwasher not draining after the wash cycle. Standing water is caused by a clogged "
            "pump filter, blocked drain hose, or faulty pump and motor assembly. "
            "Start by cleaning the pump filter (PS11759673, W10872845) — turn counterclockwise to remove. "
            "If the filter is clean, the pump and motor assembly (PS11756692, WPW10605057) may have failed. "
            "A faulty pump prevents draining regardless of the filter. "
            "PS11756692 fits WDT780SAEM1, WDT710PAHZ, WDF750SAYT3, and KDTE104ESS1."
        ),
        "metadata": {"appliance_type": "dishwasher", "symptom": "not_draining"},
    },
    {
        "id": "RA07",
        "content": (
            "Dishwasher will not start — troubleshooting guide. If pressing Start does nothing, "
            "check the door latch first. The dishwasher control board only starts the cycle when "
            "it detects the door is fully latched. "
            "PS11756967 (WPW10653840, black latch) fits WDT780SAEM1, WDF750SAYT3, and KDTE104ESS1. "
            "PS11731673 (W10862259, latch assembly with switches) fits WDT710PAHZ and Amana models. "
            "A tripped thermostat (PS11750035, WPW10195091) can also block startup. "
            "Verify the child lock is off and check the circuit breaker."
        ),
        "metadata": {"appliance_type": "dishwasher", "symptom": "not_starting"},
    },
    {
        "id": "RA08",
        "content": (
            "How to fix a dishwasher that is not cleaning dishes properly. "
            "Poor cleaning is most often caused by a weak pump or clogged spray arm path. "
            "Inspect and clean the pump filter (PS11759673). "
            "If the pump motor (PS11756692, WPW10605057) is failing, water pressure to the spray arms "
            "is reduced and dishes will not clean. "
            "Also check the upper rack adjuster kit (PS10065979, W10712395) — a misaligned rack can "
            "block the spray arm from rotating. "
            "Confirm water temperature at the tap is at least 120 degrees F."
        ),
        "metadata": {"appliance_type": "dishwasher", "symptom": "not_cleaning"},
    },
    {
        "id": "RA09",
        "content": (
            "Dishwasher leaking water — diagnosis and repair. Leaks from the door front usually mean "
            "a damaged door latch (PS11756967 or PS11731673) allowing the door to flex. "
            "Leaks from underneath often come from a failed pump seal in the pump and motor assembly "
            "(PS11756692, WPW10605057). Check all hose clamps under the dishwasher. "
            "A misaligned upper rack caused by a broken adjuster arm clip (PS11751100, WPW10250160) "
            "can also redirect water incorrectly. PS11756692 fits WDT780SAEM1 and WDT710PAHZ."
        ),
        "metadata": {"appliance_type": "dishwasher", "symptom": "leaking"},
    },
    {
        "id": "RA10",
        "content": (
            "Dishwasher not filling with water. If the dishwasher runs but the tub stays empty, "
            "the thermostat (PS11750035, WPW10195091) may have tripped and is blocking the fill cycle — "
            "it fits WDT780SAEM1, ADB1700ADB1, and KDTE104ESS1. "
            "Also check the pump filter (PS11759673) for clogs that restrict incoming flow. "
            "Verify the water supply valve under the sink is fully open. "
            "If the dishwasher still does not fill, the water inlet valve or control board may need testing."
        ),
        "metadata": {"appliance_type": "dishwasher", "symptom": "not_filling"},
    },
]


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set. Set it in your .env file.", file=sys.stderr)
        sys.exit(1)

    ef = OpenAIEmbeddingFunction(api_key=api_key, model_name="text-embedding-3-small")
    client = get_client()

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing '{COLLECTION_NAME}' collection.")
    except Exception:
        pass

    collection = client.create_collection(name=COLLECTION_NAME, embedding_function=ef)

    collection.add(
        documents=[a["content"]  for a in REPAIR_ARTICLES],
        metadatas=[a["metadata"] for a in REPAIR_ARTICLES],
        ids=[a["id"]             for a in REPAIR_ARTICLES],
    )

    print(f"Built Chroma collection '{COLLECTION_NAME}' with {len(REPAIR_ARTICLES)} repair articles.")
    from backend.data.chroma import CHROMA_PATH
    print(f"Persisted to: {CHROMA_PATH}")


if __name__ == "__main__":
    main()
