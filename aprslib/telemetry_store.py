"""
APRS Telemetry Store - Correlates telemetry configuration messages
with telemetry data reports and applies conversion coefficients.

Usage:
    store = TelemetryStore()
    
    # Feed parsed config messages:
    store.update_config('N3MIM', parsed_config_dict)
    
    # Apply coefficients to telemetry data:
    enhanced = store.apply('N3MIM', parsed_telemetry_dict)
"""


class TelemetryStore:
    """
    Stores telemetry configuration per station and applies
    coefficients to raw telemetry data.
    """
    
    def __init__(self):
        self._configs = {}  # callsign -> config dict
    
    def update_config(self, callsign, config):
        """
        Store telemetry config from a parsed telemetry-message packet.
        
        Args:
            callsign: Station callsign (e.g., 'N3MIM')
            config: Dict from parse result containing any of:
                    tPARM, tUNIT, tEQNS, tBITS, title
        """
        callsign = callsign.upper().strip()
        if callsign not in self._configs:
            self._configs[callsign] = {}
        
        # Only store telemetry-related keys
        for key in ('tPARM', 'tUNIT', 'tEQNS', 'tBITS', 'title'):
            if key in config:
                self._configs[callsign][key] = config[key]
    
    def get_config(self, callsign):
        """Get stored config for a callsign, or empty dict."""
        return self._configs.get(callsign.upper().strip(), {})
    
    def has_config(self, callsign):
        """Check if any config exists for a callsign."""
        return callsign.upper().strip() in self._configs
    
    def clear(self, callsign=None):
        """Clear config for a specific callsign or all."""
        if callsign:
            self._configs.pop(callsign.upper().strip(), None)
        else:
            self._configs.clear()
    
    def apply(self, callsign, telemetry):
        """
        Apply stored coefficients to raw telemetry values.
        
        Args:
            callsign: Station callsign
            telemetry: Dict with keys 'seq', 'vals' (list of floats), 'bits' (str)
        
        Returns:
            Dict with:
                seq: sequence number
                channels: list of dicts with name, unit, raw, value
                digital: list of dicts with name, active, raw
                title: project title (if configured)
        """
        callsign = callsign.upper().strip()
        config = self._configs.get(callsign, {})
        
        eqns = config.get('tEQNS', [[0, 1, 0]] * 5)
        parms = config.get('tPARM', [''] * 13)
        units = config.get('tUNIT', [''] * 13)
        bits_sense = config.get('tBITS', '11111111')
        
        result = {
            'seq': telemetry.get('seq', 0),
            'channels': [],
            'digital': [],
        }
        
        # Process analog channels (up to 5)
        raw_vals = telemetry.get('vals', [])
        for i in range(min(len(raw_vals), 5)):
            raw_val = raw_vals[i]
            
            # Get equation coefficients (a, b, c)
            if i < len(eqns):
                a, b, c = eqns[i]
            else:
                a, b, c = 0, 1, 0
            
            # Apply: result = a * raw^2 + b * raw + c
            converted = a * (raw_val ** 2) + b * raw_val + c
            
            result['channels'].append({
                'name': parms[i] if i < len(parms) else '',
                'unit': units[i] if i < len(units) else '',
                'raw': raw_val,
                'value': converted,
            })
        
        # Process digital channels (up to 8)
        bits_data = telemetry.get('bits', '00000000')
        for i in range(8):
            sense = int(bits_sense[i]) if i < len(bits_sense) else 1
            value = int(bits_data[i]) if i < len(bits_data) else 0
            
            # Active when value matches the sense bit (APRS101 spec)
            active = (value == sense)
            
            result['digital'].append({
                'name': parms[5 + i] if (5 + i) < len(parms) else '',
                'active': active,
                'raw': value,
            })
        
        # Add title if configured
        if 'title' in config:
            result['title'] = config['title']
        
        return result
