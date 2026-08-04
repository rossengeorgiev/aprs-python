#!/usr/bin/env python3
"""
APRS-IS Live Packet Monitor — Tests new parsing features against real traffic.

Connects to APRS-IS (read-only, no callsign needed) and parses every packet,
tracking which format types and new features are being exercised.

Usage:
    python3 tests/live_monitor.py [--filter FILTER] [--duration SECONDS] [--verbose]

Examples:
    # Monitor all traffic worldwide for 60 seconds
    python3 tests/live_monitor.py --duration 60

    # Monitor specific area (50km around San Francisco)
    python3 tests/live_monitor.py --filter "r/37.77/-122.42/50" --duration 120

    # Verbose mode - print every packet with new feature hits
    python3 tests/live_monitor.py --filter "r/37.77/-122.42/200" --verbose

    # Monitor weather stations only
    python3 tests/live_monitor.py --filter "t/w" --duration 60

    # Monitor messages only
    python3 tests/live_monitor.py --filter "t/m" --duration 60

Requires: This must be run from the aprs-python repo root (or aprslib on PYTHONPATH).
"""

import sys
import os
import time
import argparse
import signal
from collections import defaultdict, Counter

# Add the repo to the path so we use the local aprslib with new features
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aprslib
from aprslib.exceptions import ParseError, UnknownFormat
from aprslib.path import analyze_path
from aprslib.symbols import decode_symbol


class LiveMonitor:
    """Connects to APRS-IS and monitors parsing results in real-time."""

    def __init__(self, aprs_filter=None, verbose=False, duration=None):
        self.aprs_filter = aprs_filter or "r/0/0/25000"  # default: worldwide
        self.verbose = verbose
        self.duration = duration
        self.start_time = None
        self.running = True

        # Statistics
        self.total_packets = 0
        self.total_parsed = 0
        self.total_errors = 0
        self.format_counts = Counter()
        self.error_types = Counter()
        self.new_feature_hits = defaultdict(list)

        # Track new features specifically
        self.new_features = {
            'query': 0,
            'peet-bros-weather': 0,
            'area_object': 0,
            'nws_alert': 0,
            'signpost': 0,
            'df_signal': 0,
            'frequency': 0,
            'tone': 0,
            'offset': 0,
            'device': 0,  # Mic-E device type
            'item-in-message': 0,
            'radiation': 0,  # Weather extension
            'water_level': 0,
            'battery': 0,  # Weather voltage
            'directed-query': 0,
        }

        # Path analysis stats
        self.path_stats = {
            'internet': 0,
            'rf_only': 0,
            'no_gate': 0,
            'q_constructs': Counter(),
        }

    def process_packet(self, raw_packet):
        """Process a single raw APRS-IS packet."""
        self.total_packets += 1

        # Ensure we're working with a string
        if isinstance(raw_packet, bytes):
            try:
                raw_packet = raw_packet.decode('utf-8')
            except UnicodeDecodeError:
                raw_packet = raw_packet.decode('latin-1')

        # Skip server messages
        if raw_packet.startswith('#'):
            return

        try:
            parsed = aprslib.parse(raw_packet)
            self.total_parsed += 1

            # Track format type
            fmt = parsed.get('format', 'unknown')
            self.format_counts[fmt] += 1

            # Check for new feature hits
            self._check_new_features(parsed, raw_packet)

            # Analyze path
            self._analyze_path(parsed)

            # Verbose output
            if self.verbose:
                self._print_packet(parsed, raw_packet)

        except (ParseError, UnknownFormat) as e:
            self.total_errors += 1
            error_key = type(e).__name__
            self.error_types[error_key] += 1

            if self.verbose and isinstance(e, UnknownFormat):
                print(f"  [{error_key}] {str(e)[:80]}")

        except Exception as e:
            self.total_errors += 1
            self.error_types[f"Exception:{type(e).__name__}"] += 1
            if self.verbose:
                print(f"  [CRASH] {type(e).__name__}: {e}")
                print(f"          Packet: {raw_packet[:100]}")

    def _check_new_features(self, parsed, raw_packet):
        """Check if any new parsing features were exercised."""
        fmt = parsed.get('format', '')

        # Query packets
        if fmt == 'query':
            self.new_features['query'] += 1
            self._log_hit('query', parsed, raw_packet)
        elif fmt == 'directed-query':
            self.new_features['directed-query'] += 1
            self._log_hit('directed-query', parsed, raw_packet)

        # Peet Bros weather
        if fmt == 'peet-bros-weather':
            self.new_features['peet-bros-weather'] += 1
            self._log_hit('peet-bros-weather', parsed, raw_packet)

        # Area objects
        if 'area_object' in parsed:
            self.new_features['area_object'] += 1
            self._log_hit('area_object', parsed, raw_packet)

        # NWS alerts
        if 'nws_alert' in parsed:
            self.new_features['nws_alert'] += 1
            self._log_hit('nws_alert', parsed, raw_packet)

        # Signpost
        if 'signpost' in parsed:
            self.new_features['signpost'] += 1
            self._log_hit('signpost', parsed, raw_packet)

        # DF reports
        if 'df_signal' in parsed:
            self.new_features['df_signal'] += 1
            self._log_hit('df_signal', parsed, raw_packet)

        # Frequency/tone
        if 'frequency' in parsed:
            self.new_features['frequency'] += 1
            self._log_hit('frequency', parsed, raw_packet)
        if 'tone' in parsed:
            self.new_features['tone'] += 1
        if 'offset' in parsed:
            self.new_features['offset'] += 1

        # Mic-E device type
        if 'device' in parsed:
            self.new_features['device'] += 1
            self._log_hit('device', parsed, raw_packet)

        # Item-in-message
        if fmt == 'item-in-message':
            self.new_features['item-in-message'] += 1
            self._log_hit('item-in-message', parsed, raw_packet)

        # Weather extensions (APRS 1.2)
        weather = parsed.get('weather', {})
        if 'radiation' in weather:
            self.new_features['radiation'] += 1
            self._log_hit('radiation', parsed, raw_packet)
        if 'water_level' in weather:
            self.new_features['water_level'] += 1
            self._log_hit('water_level', parsed, raw_packet)
        if 'battery' in weather:
            self.new_features['battery'] += 1
            self._log_hit('battery', parsed, raw_packet)

    def _analyze_path(self, parsed):
        """Run path analysis on parsed packet."""
        path = parsed.get('path', [])
        if path:
            info = analyze_path(path)
            if info['is_internet']:
                self.path_stats['internet'] += 1
                if info['q_construct']:
                    self.path_stats['q_constructs'][info['q_construct']] += 1
            else:
                self.path_stats['rf_only'] += 1
            if info['no_gate']:
                self.path_stats['no_gate'] += 1

    def _log_hit(self, feature, parsed, raw_packet):
        """Log a new feature hit (keep first 5 examples)."""
        if len(self.new_feature_hits[feature]) < 5:
            self.new_feature_hits[feature].append({
                'raw': raw_packet[:200],
                'parsed_keys': list(parsed.keys()),
                'format': parsed.get('format'),
            })

    def _print_packet(self, parsed, raw_packet):
        """Print a parsed packet in verbose mode (only interesting ones)."""
        # Only print packets that hit new features
        fmt = parsed.get('format', '')
        new_feature_keys = [  # noqa: F841
            'query', 'directed-query', 'peet-bros-weather', 'area_object',
            'nws_alert', 'signpost', 'df_signal', 'frequency', 'device',
            'item-in-message',
        ]

        is_interesting = (
            fmt in ('query', 'directed-query', 'peet-bros-weather', 'item-in-message') or
            any(k in parsed for k in ('area_object', 'nws_alert', 'signpost',
                                       'df_signal', 'frequency', 'device'))
        )

        if is_interesting:
            print(f"\n{'='*80}")
            print(f"  NEW FEATURE HIT: {fmt}")
            print(f"  Raw: {raw_packet[:120]}")
            print(f"  From: {parsed.get('from', '?')} → {parsed.get('to', '?')}")

            # Print relevant new fields
            for key in ('query_type', 'frequency', 'tone', 'offset', 'device',
                        'df_signal', 'df_height', 'df_gain', 'df_directivity',
                        'area_object', 'nws_alert', 'signpost'):
                if key in parsed:
                    print(f"  {key}: {parsed[key]}")

            # Symbol decoding
            if 'symbol' in parsed and 'symbol_table' in parsed:
                sym_info = decode_symbol(parsed['symbol_table'], parsed['symbol'])
                print(f"  Symbol: {sym_info['description']}", end='')
                if 'overlay' in sym_info:
                    print(f" (overlay: {sym_info['overlay']})", end='')
                print()

            print(f"{'='*80}")

    def print_stats(self):
        """Print final statistics."""
        elapsed = time.time() - self.start_time
        rate = self.total_packets / elapsed if elapsed > 0 else 0

        print("\n")
        print("=" * 80)
        print("  APRS-IS LIVE MONITOR — RESULTS")
        print(f"  Duration: {elapsed:.1f}s | Filter: {self.aprs_filter}")
        print("=" * 80)

        print("\n  TOTALS:")
        print(f"    Packets received:  {self.total_packets}")
        print(f"    Successfully parsed: {self.total_parsed}")
        print(f"    Parse errors:      {self.total_errors}")
        print(f"    Rate:              {rate:.1f} packets/sec")
        print(f"    Success rate:      {self.total_parsed/(self.total_packets or 1)*100:.1f}%")

        print("\n  FORMAT DISTRIBUTION:")
        for fmt, count in self.format_counts.most_common(20):
            pct = count / (self.total_parsed or 1) * 100
            bar = '█' * int(pct / 2)
            print(f"    {fmt:24s} {count:6d} ({pct:5.1f}%) {bar}")

        print("\n  NEW FEATURE HITS:")
        any_hits = False
        for feature, count in sorted(self.new_features.items(), key=lambda x: -x[1]):
            if count > 0:
                any_hits = True
                print(f"    ✓ {feature:24s} {count:6d}")
        if not any_hits:
            print("    (none yet — try a broader filter or longer duration)")

        if self.new_feature_hits:
            print("\n  EXAMPLE PACKETS (new features):")
            for feature, examples in self.new_feature_hits.items():
                if examples:
                    print(f"\n    [{feature}] ({len(examples)} examples)")
                    for ex in examples[:3]:
                        print(f"      {ex['raw'][:100]}")

        print("\n  PATH ANALYSIS:")
        print(f"    Internet (APRS-IS): {self.path_stats['internet']}")
        print(f"    RF-only:            {self.path_stats['rf_only']}")
        print(f"    NOGATE/RFONLY:       {self.path_stats['no_gate']}")
        if self.path_stats['q_constructs']:
            print("    q-constructs:")
            for qc, count in self.path_stats['q_constructs'].most_common(10):
                print(f"      {qc}: {count}")

        if self.error_types:
            print("\n  ERROR BREAKDOWN:")
            for err, count in self.error_types.most_common(10):
                print(f"    {err:40s} {count:6d}")

        print("\n" + "=" * 80)

    def run(self):
        """Connect to APRS-IS and start monitoring."""
        self.start_time = time.time()

        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            self.running = False
            print("\n\n  Stopping... (printing stats)")

        signal.signal(signal.SIGINT, signal_handler)

        print("=" * 80)
        print("  APRS-IS Live Packet Monitor")
        print(f"  Filter: {self.aprs_filter}")
        print(f"  Duration: {'unlimited' if not self.duration else f'{self.duration}s'}")
        print(f"  Verbose: {self.verbose}")
        print(f"  Using aprslib from: {os.path.dirname(aprslib.__file__)}")
        print("=" * 80)
        print("  Connecting to APRS-IS (rotate.aprs2.net:14580)...")

        # Connect to APRS-IS
        # Default to read-only access; set APRS_LOGIN/APRS_PASSWORD env vars
        # for authenticated use with your own callsign
        callsign = os.environ.get("APRS_LOGIN", "N0CALL")
        passwd = os.environ.get("APRS_PASSWORD", "-1")
        host = os.environ.get("APRS_HOST", "rotate.aprs2.net")
        ais = aprslib.IS(callsign, passwd=passwd, host=host, port=14580)

        try:
            ais.connect()
            ais.set_filter(self.aprs_filter)
            print("  Connected! Monitoring packets...\n")

            if self.duration:
                # Use non-blocking consumer with timeout
                end_time = self.start_time + self.duration
                while self.running and time.time() < end_time:
                    try:
                        ais.consumer(self.process_packet, blocking=False, immortal=False, raw=True)
                    except aprslib.ConnectionDrop:
                        print("  Connection dropped, reconnecting...")
                        time.sleep(2)
                        ais.connect()
                        ais.set_filter(self.aprs_filter)
                    except aprslib.ConnectionError:
                        print("  Connection error, retrying...")
                        time.sleep(5)
                        ais.connect()
                        ais.set_filter(self.aprs_filter)

                    # Print progress every 10 seconds
                    elapsed = time.time() - self.start_time
                    if int(elapsed) % 10 == 0 and self.total_packets > 0:
                        hits = sum(v for v in self.new_features.values())
                        sys.stdout.write(
                            f"\r  [{elapsed:.0f}s] {self.total_packets} pkts | "
                            f"{self.total_parsed} parsed | "
                            f"{hits} new-feature hits | "
                            f"{self.total_errors} errors"
                        )
                        sys.stdout.flush()
            else:
                # Unlimited duration - use blocking consumer
                while self.running:
                    try:
                        ais.consumer(self.process_packet, blocking=False, immortal=False, raw=True)
                    except aprslib.ConnectionDrop:
                        if not self.running:
                            break
                        print("  Connection dropped, reconnecting...")
                        time.sleep(2)
                        ais.connect()
                        ais.set_filter(self.aprs_filter)
                    except aprslib.ConnectionError:
                        if not self.running:
                            break
                        print("  Connection error, retrying...")
                        time.sleep(5)
                        ais.connect()
                        ais.set_filter(self.aprs_filter)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"\n  Fatal error: {type(e).__name__}: {e}")
        finally:
            try:
                ais.close()
            except Exception:
                pass

        self.print_stats()


def main():
    parser = argparse.ArgumentParser(
        description="APRS-IS Live Packet Monitor — Tests new parsing features",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Filter examples:
  r/37.77/-122.42/200   Range: 200km around San Francisco
  r/0/0/25000           Worldwide (all traffic)
  t/poimqstunw          All types
  t/w                   Weather only
  t/m                   Messages only
  t/p                   Position reports only
  b/N0CALL/W1ABC        Specific callsigns (budlist)
  p/CW/N0               Prefix filter (callsigns starting with CW or N0)
        """,
    )
    parser.add_argument(
        "--filter", "-f",
        default="r/0/0/25000",
        help="APRS-IS server-side filter (default: worldwide)",
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=None,
        help="Duration in seconds (default: unlimited, Ctrl+C to stop)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print details of every new-feature packet hit",
    )

    args = parser.parse_args()

    monitor = LiveMonitor(
        aprs_filter=args.filter,
        verbose=args.verbose,
        duration=args.duration,
    )
    monitor.run()


if __name__ == "__main__":
    main()
