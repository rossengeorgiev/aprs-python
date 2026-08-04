"""
APRS Digipeater Path Analysis utility.

Analyzes the digipeater path from a parsed APRS packet header,
providing hop count, q-construct info, and IGate detection.
"""
import re

__all__ = ['analyze_path']


def analyze_path(path_list):
    """
    Analyze an APRS digipeater path.
    
    Args:
        path_list: List of path elements from parsed header (e.g., ['WIDE1-1', 'qAR', 'IGATE1'])
    
    Returns:
        Dict with path analysis results.
    """
    result = {
        'hops_consumed': 0,
        'hops_remaining': 0,
        'digipeaters': [],
        'is_internet': False,
        'q_construct': None,
        'igate': None,
        'no_gate': False,
    }
    
    i = 0
    while i < len(path_list):
        element = path_list[i]
        
        # Check for q-construct (qAR, qAC, qAo, etc.)
        if re.match(r'^q[A-Za-z]{2}$', element):
            result['q_construct'] = element
            result['is_internet'] = True
            # Next element after q-construct is the IGate
            if i + 1 < len(path_list):
                result['igate'] = path_list[i + 1]
            break  # q-construct is always at the end
        
        # Check for NOGATE/RFONLY
        if element.upper() in ('NOGATE', 'RFONLY'):
            result['no_gate'] = True
            i += 1
            continue
        
        # Check for TCPIP* (internet source)
        if element.upper() in ('TCPIP', 'TCPIP*'):
            result['is_internet'] = True
            i += 1
            continue
        
        # Check for has-been-digipeated marker
        used = element.endswith('*')
        call = element.rstrip('*')
        
        # Check for WIDEn-N / TRACEn-N pattern
        wide_match = re.match(r'^(WIDE|TRACE|RELAY)(\d)(?:-(\d))?$', call, re.I)
        if wide_match:
            n = int(wide_match.group(2))
            remaining = int(wide_match.group(3)) if wide_match.group(3) is not None else 0
            if used:
                # Fully consumed
                result['hops_consumed'] += n
            else:
                result['hops_remaining'] += remaining
        elif used:
            # A specific digi callsign with * = it digipeated
            result['hops_consumed'] += 1
            result['digipeaters'].append(call)
        
        i += 1
    
    result['total_hops'] = result['hops_consumed'] + result['hops_remaining']
    
    return result
