#!/usr/bin/env python3
import re
import sys
import time
import csv
import requests
import concurrent.futures
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich import box
from rich.text import Text

console = Console()

# Default Google Maps API Endpoints
ENDPOINTS = [
    ("PlacesATM", "https://maps.googleapis.com/maps/api/place/textsearch/json?query=atm+near+melbourne&key={key}"),
    ("Geocoding", "https://maps.googleapis.com/maps/api/geocode/json?address=New+York&key={key}"),
    ("ReverseGeocoding", "https://maps.googleapis.com/maps/api/geocode/json?latlng=40.7128,-74.0060&key={key}"),
    ("PlacesNearby", "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=40.7128,-74.0060&radius=500&type=restaurant&key={key}"),
    ("PlacesTextSearch", "https://maps.googleapis.com/maps/api/place/textsearch/json?query=pizza+in+New+York&key={key}"),
    ("PlacesDetails", "https://maps.googleapis.com/maps/api/place/details/json?place_id=ChIJOwg_06VPwokRYv534QaPC8g&key={key}"),
    ("Directions", "https://maps.googleapis.com/maps/api/directions/json?origin=New+York,NY&destination=Boston,MA&key={key}"),
    ("DistanceMatrix", "https://maps.googleapis.com/maps/api/distancematrix/json?origins=New+York,NY&destinations=Boston,MA&key={key}"),
    ("TimeZone", "https://maps.googleapis.com/maps/api/timezone/json?location=40.7128,-74.0060&timestamp=1458000000&key={key}"),
    ("Elevation", "https://maps.googleapis.com/maps/api/elevation/json?locations=40.714728,-73.998672&key={key}"),
    ("StaticMap", "https://maps.googleapis.com/maps/api/staticmap?center=New+York,NY&zoom=13&size=600x300&maptype=roadmap&key={key}"),
    ("StreetView", "https://maps.googleapis.com/maps/api/streetview?size=600x300&location=40.720032,-73.988354&heading=151.78&pitch=-0.76&key={key}"),
    ("Autocomplete", "https://maps.googleapis.com/maps/api/place/autocomplete/json?input=Empire%20State&key={key}")
]

HELP_TEXT = """
[bold cyan]Google Maps API Key Tester[/bold cyan]

Usage:
  python google_maps_key_tester_pro.py <API_KEY|file.txt> [--csv]

Arguments:
  <API_KEY>           Single Google Maps API key starting with 'AIza'
  <file.txt>          Text file containing one or more API keys to test

Options:
  --csv               Export results to CSV files
  -h, --help          Show this help message and exit

Description:
  This tool tests Google Maps API keys by calling multiple endpoints
  to check which services are enabled or denied.

Examples:
  python google_maps_key_tester_pro.py AIzaSyDxxxxx1234567890abcdefg
  python google_maps_key_tester_pro.py keys.txt --csv
"""

def print_help():
    console.print(HELP_TEXT)

def test_key(key, export_csv=False):
    console.rule(f"[bold cyan]Testing API Key[/bold cyan] [yellow]{key}[/yellow]")

    table = Table(title="Google Maps API Test Results", box=box.SIMPLE_HEAVY, show_lines=True)
    table.add_column("Endpoint", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Response Time (s)", style="magenta")
    table.add_column("Preview", style="dim", overflow="fold")

    enabled_count = disabled_count = 0
    results = []

    for name, url in track(ENDPOINTS, description=f"[cyan]Testing endpoints for key {key[:10]}...[/cyan]"):
        start_time = time.time()
        try:
            r = requests.get(url.format(key=key), timeout=6)
            elapsed = round(time.time() - start_time, 2)
            data = r.json()
            status = data.get("status", "ERROR")
            preview = str(data)[:70].replace("\n", " ")

            if status in ("OK", "ZERO_RESULTS"):
                table.add_row(name, "[green]✅ ENABLED[/green]", str(elapsed), preview)
                enabled_count += 1
            elif status == "REQUEST_DENIED":
                table.add_row(name, "[red]⛔ DENIED[/red]", str(elapsed), status)
                disabled_count += 1
            elif status == "OVER_QUERY_LIMIT":
                table.add_row(name, "[yellow]⚠ RATE LIMITED[/yellow]", str(elapsed), status)
                disabled_count += 1
            else:
                table.add_row(name, "[red]❌ DISABLED[/red]", str(elapsed), status)
                disabled_count += 1

            results.append([key, name, status, elapsed])
        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            table.add_row(name, "[red]❌ ERROR[/red]", str(elapsed), str(e)[:70])
            disabled_count += 1
            results.append([key, name, "ERROR", elapsed])

    console.print(table)

    # Summary
    color = "green" if enabled_count > 0 else "red"
    console.print(Panel.fit(
        f"[{color}]{'VALID' if enabled_count > 0 else 'INVALID'} KEY[/] "
        f"({enabled_count} enabled, {disabled_count} disabled)",
        title="Summary", border_style=color
    ))

    # CSV Export
    if export_csv:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"maps_key_results_{key[:8]}_{timestamp}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["API Key", "Endpoint", "Status", "Response Time (s)"])
            writer.writerows(results)
        console.print(f"[cyan]Results saved to[/cyan] {filename}")

def extract_keys_from_file(filename):
    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return sorted(set(re.findall(r"AIza[0-9A-Za-z_\-]{35}", text)))

def run_tests(keys, export_csv):
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(test_key, key, export_csv) for key in keys]
        for _ in concurrent.futures.as_completed(futures):
            pass

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_help()
        sys.exit(0)

    arg = sys.argv[1]
    export_csv = "--csv" in sys.argv

    if re.match(r"^AIza[0-9A-Za-z_\-]{35}$", arg):
        test_key(arg, export_csv=export_csv)
    elif arg.endswith(".txt"):
        keys = extract_keys_from_file(arg)
        if not keys:
            console.print("[red]No valid API keys found in file.[/red]")
            sys.exit(1)
        run_tests(keys, export_csv)
    else:
        console.print("[red]Invalid input. Provide an API key or a file containing keys.[/red]")
