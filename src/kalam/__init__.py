import re
import click
from dataclasses import dataclass

class Tempo:
    def __init__(self, bpm):
        self.bpm = bpm

    @property
    def period(self):
        return 60/self.bpm

@dataclass
class TimeSig:
    # TODO: assumes quarter gets the beat lmao
    numerator: int

class BeatTs:
    def __init__(self, bar, beat, tick=0, pct=0, timesig: TimeSig = None):
        self.bar = bar
        self.beat = beat
        self.tick = tick
        self.pct = pct
        self.timesig = timesig or TimeSig(4)

    def to_time(self, tempo: Tempo):
        # ASSUME 16th TICKS AND QN BEATS
        beats = self.bar * self.timesig.numerator \
            + self.beat \
            + self.tick/4

        return beats * tempo.period

    @classmethod
    def from_string(cls, s: str):
        parts = [int(x.strip()) for x in s.strip().split('.')]
        # BAR.BEAT.TICK.%
        # DEFAULT TICK SIZE IS 16ths

        assert len(parts) <= 4

        bar = parts[0] - 1
        beat, tick, pct = (0, 0, 0)
        if len(parts) > 1:
            beat = parts[1] - 1
        if len(parts) > 2:
            tick = parts[2] - 1
        if len(parts) > 3:
            pct = parts[3] - 1

        return cls(bar, beat, tick, pct)

    def __repr__(self) -> str:
        return f'{self.bar+1}.{self.beat+1}.{self.tick+1}.{self.pct:02}'

@dataclass
class Lyric:
    start: BeatTs
    end: BeatTs
    text: str

    def __repr__(self) -> str:
        return f'[{start} → {end}] {text}'

class Klm:
    LYRIC_RE = re.compile(r'\[([\d.]+)\s+->\s+([\d.]+)]\s+(.*)')

    def __init__(self, lyrics: list[Lyric]):
        self.lyrics = lyrics

    @classmethod
    def parse(cls, i):
        lyrics = []
        for i, line in enumerate(i):
            if m := cls.LYRIC_RE.match(line):
                fr, to, text = m.groups()

                fr = BeatTs.from_string(fr)
                to = BeatTs.from_string(to)

                lyrics.append(Lyric(fr, to, text))
            else:
                raise Exception(f'parse error on line {i+1}')

        return cls(lyrics)

@click.command()
@click.argument('infiles', type=click.File('r'), nargs=-1)
def cli(infiles):
    for file in infiles:
        k = Klm.parse(file)
        print(k.lyrics)