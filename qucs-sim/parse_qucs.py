import cmath
import re
import sys

def parse_qucs_dat(filename):
    with open(filename, 'r') as f:
        content = f.read()

    freqs = []
    m_freq = re.search(r'<indep frequency \d+>\s*(.*?)\s*</indep>', content, re.DOTALL)
    if m_freq:
        for val in m_freq.group(1).strip().split():
            freqs.append(float(val))

    data = {}
    pattern = r'<dep\s+([\w\[\],\.]+)\s+frequency>\s*(.*?)\s*</dep>'
    for m in re.finditer(pattern, content, re.DOTALL):
        var = m.group(1)
        vals = []
        for line in m.group(2).strip().split():
            line = line.strip()
            if '+j' in line:
                p = line.split('+j')
                c = complex(float(p[0]), float(p[1]))
            elif '-j' in line:
                p = line.split('-j')
                c = complex(float(p[0]), -float(p[1]))
            else:
                c = complex(float(line), 0.0)
            vals.append(c)
        data[var] = vals

    return freqs, data

if __name__ == '__main__':
    fn = sys.argv[1] if len(sys.argv) > 1 else 'test_sp_bce.dat'
    freqs, data = parse_qucs_dat(fn)
    idx = freqs.index(9.8e7) if 9.8e7 in freqs else 0
    print(f'=== QUCS Simulation Results at {freqs[idx]/1e6:.1f} MHz ===')
    for p in ['S[1,1]', 'S[2,1]', 'S[1,2]', 'S[2,2]']:
        if p in data:
            v = data[p][idx]
            db = 20 * cmath.log10(abs(v)).real
            deg = cmath.phase(v) * 180 / 3.141592653589793
            print(f'{p:8s}: {db:+7.2f} dB (mag={abs(v):.4f}, phase={deg:+6.1f} deg)')
