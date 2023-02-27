from pytest import approx
from kalam import Tempo, TimeSig, BeatTs

def test_beat_timing():
    tempo = Tempo(190)
    ts = BeatTs(57, 0)
    t = ts.to_time(tempo)
    assert t == approx(72) # 01:12.000
