from machine import PWM, Pin, ADC
import utime

melody_str = "Melody:b=116,o=4,d=4:e,8b,8p,8b,8a,8b,e,8b,8p,8b,8p,8a,b,d5,8c5,8p,8c5,8b,8c5,e,8c5,8p,8c5,8p,8b,c5,d5"

buzzer = PWM(Pin(12))
potentiometer = ADC(Pin(27))
button = Pin(3, Pin.IN, Pin.PULL_UP)

NOTES = {
    'c': 261.63, 'c#': 277.18, 'd': 293.66, 'd#': 311.13, 'e': 329.63,
    'f': 349.23, 'f#': 369.99, 'g': 392.00, 'g#': 415.30, 'a': 440.00,
    'a#': 466.16, 'b': 493.88, 'p': 0
}

def get_volume():
    return potentiometer.read_u16() // 2 

def parse_rtttl(rtttl_str):
    parts = rtttl_str.split(':')
    header = parts[1].split(',')
    notes_data = parts[2].split(',')

    bpm = 116
    default_duration = 4
    default_octave = 4

    for h in header:
        if h.startswith('b='): bpm = int(h[2:])
        if h.startswith('d='): default_duration = int(h[2:])
        if h.startswith('o='): default_octave = int(h[2:])

    wholenote = (60 * 1000 / bpm) * 4
    parsed_notes = []

    for n in notes_data:
        n = n.strip()
        if not n: continue

        i = 0
        duration = ""
        while i < len(n) and n[i].isdigit():
            duration += n[i]
            i += 1

        note_duration = int(duration) if duration else default_duration

        note_name = ""
        while i < len(n) and not n[i].isdigit():
            note_name += n[i]
            i += 1

        octave = int(n[i:]) if i < len(n) else default_octave

        freq = 0
        if note_name in NOTES:
            freq = NOTES[note_name]
            if freq > 0:
                freq *= (2 ** (octave - 4))

        ms_duration = wholenote / note_duration
        parsed_notes.append((freq, ms_duration))

    return parsed_notes

melody_notes = parse_rtttl(melody_str)

is_paused = False
last_button_state = 1

try:
    while True: 
        
        for freq, ms_duration in melody_notes:
            
            active_ms = int(ms_duration * 0.9)
            pause_ms = int(ms_duration * 0.1)
            
            for stage in ("play", "silence"):
                duration = active_ms if stage == "play" else pause_ms
                
                if stage == "play" and freq > 0:
                    buzzer.freq(int(freq))
                    buzzer.duty_u16(get_volume())
                else:
                    buzzer.duty_u16(0)
                    
                start_ticks = utime.ticks_ms()
                
                while utime.ticks_diff(utime.ticks_ms(), start_ticks) < duration:
                    current_state = button.value()
                    
                    if current_state == 0 and last_button_state == 1:
                        is_paused = not is_paused
                        utime.sleep_ms(50) 
                        
                        if not is_paused and stage == "play" and freq > 0:
                            buzzer.freq(int(freq))
                            buzzer.duty_u16(get_volume())
                            
                    last_button_state = current_state
                    
                    if is_paused:
                        buzzer.duty_u16(0) 
                        start_ticks = utime.ticks_add(start_ticks, 10)
                        utime.sleep_ms(10)
                    else:
                        if stage == "play" and freq > 0:
                            buzzer.duty_u16(get_volume())
                        utime.sleep_ms(1)
        utime.sleep_ms(500)

finally:
    buzzer.duty_u16(0)