import json
import os
import csv
from datetime import date, timedelta

DATA_FILE = "plants_data.json"

# Icon categories a plant can be tagged with (matches the website version)
ICONS = {
    "1": ("Potted", "🪴"),
    "2": ("Cactus", "🌵"),
    "3": ("Herb", "🌿"),
    "4": ("Flower", "🌸"),
    "5": ("Succulent", "🍀"),
    "6": ("Sunflower", "🌻"),
    "7": ("Rose", "🌹"),
    "8": ("Tree", "🌴"),
}

LIGHT_OPTIONS = {"1": "Full sun", "2": "Partial sun", "3": "Shade", "4": ""}
DIFFICULTY_OPTIONS = {"1": "Easy", "2": "Moderate", "3": "Hard", "4": ""}


# ---------------------------------------------------------------------
# FILE HANDLING
# ---------------------------------------------------------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}, {"total_waterings": 0}

    with open(DATA_FILE, "r") as file:
        data = json.load(file)
    return data.get("plants", {}), data.get("stats", {"total_waterings": 0})


def save_data(plants, stats):
    with open(DATA_FILE, "w") as file:
        json.dump({"plants": plants, "stats": stats}, file, indent=2)


def export_csv(plants):
    with open("plants_export.csv", "w", newline="") as file:
        fieldnames = ["name", "category", "interval", "days_since_watered",
                      "notes", "room", "light", "difficulty", "favorite"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for name, p in plants.items():
            writer.writerow({
                "name": name,
                "category": p["category"],
                "interval": p["interval"],
                "days_since_watered": p["days_since_watered"],
                "notes": p["notes"],
                "room": p["room"],
                "light": p["light"],
                "difficulty": p["difficulty"],
                "favorite": p["favorite"],
            })
    print("Saved plants_export.csv\n")


def export_schedule(plants):
    lines = ["GREENHOUSE LOG - CARE SCHEDULE", "=" * 32, ""]
    for name, p in sorted(plants.items()):
        due = p["days_since_watered"] >= p["interval"]
        status = "NEEDS WATER" if due else f"{p['interval'] - p['days_since_watered']} day(s) left"
        lines.append(f"{p['icon']} {name} ({p['category']}) - every {p['interval']} days - {status}")
    with open("care_schedule.txt", "w") as file:
        file.write("\n".join(lines))
    print("Saved care_schedule.txt - open and print it like a page.\n")


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def is_due(plant):
    return plant["days_since_watered"] >= plant["interval"]


def next_watering_date(plant):
    days_left = plant["interval"] - plant["days_since_watered"]
    if days_left <= 0:
        return "Overdue"
    target = date.today() + timedelta(days=days_left)
    return target.strftime("%a, %b %d")


def garden_health(plants):
    if not plants:
        return 0
    ok_count = sum(1 for p in plants.values() if not is_due(p))
    return round((ok_count / len(plants)) * 100)


def check_alerts(plants):
    due_names = [name for name, p in plants.items() if is_due(p)]
    if due_names:
        print("\n" + "!" * 50)
        print(f"ALERT: {len(due_names)} plant(s) need water: {', '.join(due_names)}")
        print("!" * 50)
        print("\a", end="")  # terminal bell - the "sound" alert


def pick_from(options, prompt):
    for key, value in options.items():
        label = value[0] if isinstance(value, tuple) else value
        print(f"  {key}. {label if label else '(none)'}")
    choice = input(prompt).strip()
    return options.get(choice, options[list(options.keys())[-1]])


# ---------------------------------------------------------------------
# CORE FEATURES
# ---------------------------------------------------------------------

def show_plants(plants, filter_mode="all", sort_mode="urgent", search=""):
    items = [(name, p) for name, p in plants.items() if search.lower() in name.lower()
              or search.lower() in p["room"].lower()]

    if filter_mode == "due":
        items = [(n, p) for n, p in items if is_due(p)]
    elif filter_mode == "ok":
        items = [(n, p) for n, p in items if not is_due(p)]

    if sort_mode == "name":
        items.sort(key=lambda x: x[0].lower())
    elif sort_mode == "interval":
        items.sort(key=lambda x: x[1]["interval"])
    elif sort_mode == "favorite":
        items.sort(key=lambda x: not x[1]["favorite"])
    else:
        items.sort(key=lambda x: x[1]["days_since_watered"] - x[1]["interval"], reverse=True)

    if not items:
        print("\nNo plants match. Try adding one or changing your filter.\n")
        return

    print(f"\n----- YOUR PLANTS (garden health: {garden_health(plants)}%) -----")
    for name, p in items:
        star = "*" if p["favorite"] else " "
        due = is_due(p)
        status = "NEEDS WATER!" if due else f"OK - {p['interval'] - p['days_since_watered']} day(s) left"
        tags = []
        if p["room"]:
            tags.append(p["room"])
        if p["light"]:
            tags.append(p["light"])
        if p["difficulty"]:
            tags.append(p["difficulty"])
        tag_text = f" [{', '.join(tags)}]" if tags else ""

        print(f"{star} {p['icon']} {name} ({p['category']}){tag_text}")
        print(f"    watered {p['days_since_watered']} day(s) ago, every {p['interval']} days - {status}")
        print(f"    next watering: {next_watering_date(p)}  |  waterings logged: {len(p['history'])}")
        if p["notes"]:
            print(f"    note: {p['notes']}")
    print("-" * 50 + "\n")


def add_plant(plants):
    name = input("Plant name: ").strip()
    if name in plants:
        print(f"'{name}' already exists.\n")
        return

    print("Choose an icon:")
    category, icon = pick_from(ICONS, "Pick a number: ")

    interval = int(input("Water every how many days? "))
    notes = input("Notes (optional): ").strip()
    room = input("Room / location (optional): ").strip()

    print("Light needs:")
    light = pick_from(LIGHT_OPTIONS, "Pick a number (or 4 for none): ")

    print("Care difficulty:")
    difficulty = pick_from(DIFFICULTY_OPTIONS, "Pick a number (or 4 for none): ")

    plants[name] = {
        "icon": icon, "category": category, "interval": interval,
        "days_since_watered": 0, "notes": notes, "room": room,
        "light": light, "difficulty": difficulty, "favorite": False, "history": [],
    }
    print(f"'{name}' was added!\n")


def edit_plant(plants):
    name = input("Which plant do you want to edit? ").strip()
    if name not in plants:
        print("That plant is not in your list.\n")
        return
    p = plants[name]

    new_interval = input(f"Water every how many days? (currently {p['interval']}, press enter to keep) ").strip()
    if new_interval:
        p["interval"] = int(new_interval)

    new_notes = input(f"Notes (currently '{p['notes']}', press enter to keep): ").strip()
    if new_notes:
        p["notes"] = new_notes

    new_room = input(f"Room (currently '{p['room']}', press enter to keep): ").strip()
    if new_room:
        p["room"] = new_room

    print(f"'{name}' updated.\n")


def water_plant(plants, stats):
    name = input("Which plant did you water? ").strip()
    if name not in plants:
        print("That plant is not in your list.\n")
        return
    plants[name]["days_since_watered"] = 0
    plants[name]["history"].append(str(date.today()))
    stats["total_waterings"] += 1
    print(f"{name} has been watered.\n")


def water_all(plants, stats):
    if not plants:
        print("No plants to water yet.\n")
        return
    today = str(date.today())
    for p in plants.values():
        p["days_since_watered"] = 0
        p["history"].append(today)
    stats["total_waterings"] += len(plants)
    print("All plants have been watered.\n")


def remove_plant(plants):
    name = input("Which plant do you want to remove? ").strip()
    if name not in plants:
        print("That plant is not in your list.\n")
        return
    confirm = input(f"Type 'yes' to confirm removing {name}: ").strip().lower()
    if confirm == "yes":
        del plants[name]
        print(f"{name} was removed.\n")
    else:
        print("Cancelled.\n")


def duplicate_plant(plants):
    name = input("Which plant do you want to duplicate? ").strip()
    if name not in plants:
        print("That plant is not in your list.\n")
        return
    copy_name = name + " (copy)"
    p = plants[name]
    plants[copy_name] = {**p, "days_since_watered": 0, "favorite": False, "history": []}
    print(f"Created '{copy_name}'.\n")


def toggle_favorite(plants):
    name = input("Which plant do you want to favorite/unfavorite? ").strip()
    if name not in plants:
        print("That plant is not in your list.\n")
        return
    plants[name]["favorite"] = not plants[name]["favorite"]
    state = "favorited" if plants[name]["favorite"] else "unfavorited"
    print(f"{name} was {state}.\n")


def snooze_plant(plants):
    name = input("Which plant do you want to snooze? ").strip()
    if name not in plants:
        print("That plant is not in your list.\n")
        return
    plants[name]["days_since_watered"] = max(0, plants[name]["days_since_watered"] - 1)
    print(f"{name} snoozed for a day.\n")


def show_history(plants):
    name = input("Which plant's history do you want to see? ").strip()
    if name not in plants:
        print("That plant is not in your list.\n")
        return
    history = plants[name]["history"]
    if not history:
        print("No waterings logged yet.\n")
        return
    print(f"\nWatering history for {name}:")
    for entry in history[-5:][::-1]:
        print(f"  - {entry}")
    print()


def advance_day(plants):
    if not plants:
        print("No plants to update yet.\n")
        return
    for p in plants.values():
        p["days_since_watered"] += 1
    print("A day has passed for all plants.\n")


# ---------------------------------------------------------------------
# MENU
# ---------------------------------------------------------------------

def print_menu():
    print("1.  View plants")
    print("2.  Search / filter / sort plants")
    print("3.  Add a plant")
    print("4.  Edit a plant")
    print("5.  Water a plant")
    print("6.  Water all plants")
    print("7.  Remove a plant")
    print("8.  Duplicate a plant")
    print("9.  Favorite / unfavorite a plant")
    print("10. Snooze a plant (needs water -> tomorrow)")
    print("11. View watering history")
    print("12. Skip a day (for testing)")
    print("13. Export data to CSV")
    print("14. Save a printable care schedule")
    print("15. Save and exit")


def main():
    plants, stats = load_data()
    print("Welcome to the Greenhouse Log!")

    while True:
        check_alerts(plants)
        print_menu()
        choice = input("Choose an option (1-15): ").strip()

        if choice == "1":
            show_plants(plants)
        elif choice == "2":
            search = input("Search by name/room (press enter to skip): ").strip()
            print("Filter: 1) All  2) Needs water  3) On schedule")
            filter_map = {"1": "all", "2": "due", "3": "ok"}
            filter_mode = filter_map.get(input("Pick a number: ").strip(), "all")
            print("Sort: 1) Needs water first  2) Name A-Z  3) Interval  4) Favorites first")
            sort_map = {"1": "urgent", "2": "name", "3": "interval", "4": "favorite"}
            sort_mode = sort_map.get(input("Pick a number: ").strip(), "urgent")
            show_plants(plants, filter_mode, sort_mode, search)
        elif choice == "3":
            add_plant(plants)
        elif choice == "4":
            edit_plant(plants)
        elif choice == "5":
            water_plant(plants, stats)
        elif choice == "6":
            water_all(plants, stats)
        elif choice == "7":
            remove_plant(plants)
        elif choice == "8":
            duplicate_plant(plants)
        elif choice == "9":
            toggle_favorite(plants)
        elif choice == "10":
            snooze_plant(plants)
        elif choice == "11":
            show_history(plants)
        elif choice == "12":
            advance_day(plants)
        elif choice == "13":
            export_csv(plants)
        elif choice == "14":
            export_schedule(plants)
        elif choice == "15":
            save_data(plants, stats)
            print("Saved. Bye!")
            break
        else:
            print("Please choose a number from 1 to 15.\n")


if __name__ == "__main__":
    main()