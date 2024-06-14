from __future__ import annotations
from elliott_wave_analyzer.WavePattern import WavePattern
from elliott_wave_analyzer.WaveRules import Impulse, LeadingDiagonal, Correction
from elliott_wave_analyzer.WaveAnalyzer import WaveAnalyzer
from elliott_wave_analyzer.WaveOptions import WaveOptionsGenerator5, WaveOptionsGenerator3
from elliott_wave_analyzer.helpers import plot_pattern, plot_multiple_pattern
import pandas as pd
import numpy as np
import yfinance as yf


def describe_pattern(wave_pattern: WavePattern, wave_type: str):
    result = f'Found {wave_type} wave:\n'
    wave_count = 1
    if wave_type == 'impulse':
        range_max = 9
    else:
        range_max = 5
    for i in range(0, range_max, 2):
        result += f'Wave {wave_count} starts on {wave_pattern.dates[i]} at price {wave_pattern.values[i]} and ends on {wave_pattern.dates[i + 1]} at price {wave_pattern.values[i + 1]}\n'
        wave_count += 1
    print(f'{result}')


# Get data
end_date = pd.Timestamp.now()
start_date = end_date - pd.DateOffset(days=700)
df = yf.download('INTC', start=start_date, end=end_date).reset_index()

# Find lowest value to start calculating impulse UP wave
# TODO: It can also be impulse down! (second case)
idx_start = np.argmin(np.array(list(df['Low'])))

wa = WaveAnalyzer(df=df, verbose=False)
# generates WaveOptions up to [15, 15, 15, 15, 15]
wave_options_impulse = WaveOptionsGenerator5(up_to=15)
impulse = Impulse('impulse')
rules_to_check_impulse = [impulse]

wave_options_correction = WaveOptionsGenerator3(up_to=15)
correction = Correction('correction')
rules_to_check_correction = [correction]

print(f'Start at idx: {idx_start}')
print(f"will run up to {wave_options_impulse.number / 1e6}M combinations.")

wavepatterns_up = set()
wavepatterns_down = set()

# Find Impulse UP and correction DOWN
for new_option_impulse in wave_options_impulse.options_sorted:
    waves_up = wa.find_impulsive_wave(idx_start=idx_start, wave_config=new_option_impulse.values)
    if waves_up:
        wavepattern_up = WavePattern(waves_up, verbose=True)

        for rule in rules_to_check_impulse:

            if wavepattern_up.check_rule(rule):
                if wavepattern_up in wavepatterns_up:
                    continue
                else:
                    # found new impulse wave UP
                    wavepatterns_up.add(wavepattern_up)
                    print(f'{rule.name} found: {new_option_impulse.values}')
                    # describe_pattern(wavepattern_up, 'impulse')

                    # find correction after impulse
                    corrective_wave_found = False
                    for new_option_correction in wave_options_correction.options_sorted:
                        waves_down = wa.find_corrective_wave(
                            idx_start=wavepattern_up.idx_end,
                            wave_config=new_option_correction.values
                        )

                        if waves_down:
                            wavepattern_down = WavePattern(waves_down, verbose=True)

                            for rule_correction in rules_to_check_correction:

                                if wavepattern_down.check_rule(rule_correction):
                                    if wavepattern_down in wavepatterns_down:
                                        continue
                                    else:
                                        wavepatterns_down.add(wavepattern_down)
                                        print(f'{rule_correction.name} found: {new_option_correction.values}')
                                        describe_pattern(wavepattern_down, 'correction')
                                        describe_pattern(wavepattern_up, 'impulse')
                                        plot_multiple_pattern(
                                            df=df,
                                            wave_patterns=[wavepattern_up, wavepattern_down],
                                            title=str(new_option_correction)
                                        )
                                        corrective_wave_found = True

                    if not corrective_wave_found:
                        describe_pattern(wavepattern_up, 'impulse')
                        plot_pattern(df=df, wave_pattern=wavepattern_up, title=str(new_option_impulse))
