from pytest import approx
from kalam import Tempo, TimeSig, BeatTs

def test_beat_timing():
    tempo = Tempo(190)
    ts = BeatTs(57, 0)
    assert ts.to_time(tempo) == approx(72) # 01:12.000

    ts = BeatTs(97, 3, 2, 00)
    assert ts.to_time(tempo) == approx(60*2 + 03.631, 1e-5) # 02:03.631

    ts = BeatTs(101, 2, 2, 30) # 102.3.3.30
    assert ts.to_time(tempo) == approx(60*2 + 08.392, 1e-5) # 02:08.392

def test_beat_parser():
    assert BeatTs.from_string('1') == BeatTs(bar=0, beat=0) # Bitwig starts beats at 1

def test_beat_from_time():
    tempo = Tempo(190)
    # dodgy precision but w/e, it's just for debug mostly
    assert BeatTs.from_time(60*2 + 03.632, tempo) == BeatTs(97, 3, 2, 00)
    assert BeatTs.from_time(60*2 + 08.3925, tempo) == BeatTs(101, 2, 2, 30) # 01:12.000
