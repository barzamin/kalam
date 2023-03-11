import re
import click
from dataclasses import dataclass
from queue import Queue
from functools import total_ordering
import pygame
import vidmaker


class Tempo:

    def __init__(self, bpm):
        self.bpm = bpm

    @property
    def period(self):
        return 60 / self.bpm


@dataclass
class TimeSig:
    # TODO: assumes quarter gets the beat lmao
    numerator: int


@total_ordering
class BeatTs:

    def __init__(self, bar, beat, tick=0, pct=0, timesig: TimeSig = None):
        self.bar = bar
        self.beat = beat
        self.tick = tick
        self.pct = pct
        self.timesig = timesig or TimeSig(4)

    @classmethod
    def from_time(cls, t: float, tempo: Tempo, timesig: TimeSig = None):
        timesig = timesig or TimeSig(4)
        # assume 16th ticks and qn beat
        ticks_per_beat = 4
        tick_period = tempo.period / ticks_per_beat
        ticks = t / tick_period
        pct = int((ticks % 1) * 100)
        ticks = int(ticks)

        # todo divmod

        beat = ticks // ticks_per_beat
        ticks = ticks % ticks_per_beat

        bar = beat // timesig.numerator
        beat = beat % timesig.numerator

        return BeatTs(bar, beat, ticks, pct, timesig)


    def to_time(self, tempo: Tempo):
        # ASSUME 16th TICKS AND QN BEATS
        beats = self.bar * self.timesig.numerator \
            + self.beat \
            + self.tick/4 \
            + self.pct/400

        return beats * tempo.period

    @property
    def ticks(self) -> float:
        # assume 16th ticks and qn beat
        ticks_per_beat = 4
        ticks =  self.bar * self.timesig.numerator * ticks_per_beat \
                    + self.beat * ticks_per_beat \
                    + self.tick \
                    + self.pct/100

        return ticks

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, BeatTs):
            return NotImplemented

        return (self.bar == o.bar) \
            and (self.beat == o.beat) \
            and (self.tick == o.tick) \
            and (self.pct == o.pct) \
            and (self.timesig == o.timesig)

    def __lt__(self, o: object) -> bool:
        if not isinstance(o, BeatTs):
            raise NotImplemented

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
            pct = parts[3]

        return cls(bar, beat, tick, pct)

    def __repr__(self) -> str:
        return f'{self.bar+1}.{self.beat+1}.{self.tick+1}.{self.pct:02}'


@dataclass
class Lyric:
    start: BeatTs
    end: BeatTs
    text: str

    def __repr__(self) -> str:
        return f'<Lyric [{self.start} → {self.end}]: "{self.text}">'


class Klm:
    LYRIC_RE = re.compile(r'\[([\d.]+)\s+->\s+([\d.]+)]\s+(\+?)(.*)')

    def __init__(self, lyrics: list[Lyric]):
        self.lyrics = lyrics

    @classmethod
    def parse(cls, i):
        lyrics = []
        for i, line in enumerate(i):
            if line == '': continue

            if m := cls.LYRIC_RE.match(line):
                fr, to, incr, text = m.groups()

                if incr == '+':
                    text = lyrics[-1].text + text

                if fr == '.':
                    fr = lyrics[-1].end
                else:
                    fr = BeatTs.from_string(fr)
                to = BeatTs.from_string(to)

                lyrics.append(Lyric(fr, to, text))

            else:
                raise Exception(f'parse error on line {i+1}')

        return cls(lyrics)


@click.command()
@click.option('-o', '--output', type=click.Path())
@click.option('-s', '--start')
@click.option('-e', '--until')
@click.argument('infiles', type=click.File('r'), nargs=-1)
def cli(infiles, output, start, until):
    tempo = Tempo(190)

    lyric_events = []
    currently_shown = []
    for i, file in enumerate(infiles):
        k = Klm.parse(file)
        lyric_events.extend((i, lyr) for lyr in k.lyrics)
    lyric_events = sorted(lyric_events, key=lambda e: e[1].start.to_time(tempo))
    for i, l in lyric_events:
        print(f'[{i:02}] {l}')

    pygame.init()
    size = width, height = (900, 500)
    screen = pygame.display.set_mode(size)
    if output:
        video = vidmaker.Video(output, fps=60, resolution=size)

    lyr_font = pygame.font.SysFont('MingLiU', 40)
    dbg_font = pygame.font.SysFont('PragmataPro Mono', 18)
    clock = pygame.time.Clock()
    # lyric_t = 120  # middle of "there's something irresistable"
    if start:
        lyric_t0 = BeatTs.from_string(start).to_time(tempo)
    else:
        lyric_t0 = lyric_events[0][1].start.to_time(tempo)-0.001 #BeatTs.from_string('98.1.1.00').to_time(tempo)-0.001
    if until:
        last_t = BeatTs.from_string(until).to_time(tempo)
    else:
        last_t = max(lyr.end.to_time(tempo) for tri, lyr in lyric_events)
    lyric_t = lyric_t0
    running = True
    while running:
        clock.tick()#60)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif not output and ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                lyric_t = lyric_t0
            elif not output and ev.type == pygame.KEYDOWN and ev.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                dt = 0.5 * (-1 if ev.key == pygame.K_LEFT else +1)
                lyric_t += dt

        # process current lyrics LOL THIS IS SHIT O(n)
        currently_shown = []
        for i, (tri, lyr) in enumerate(lyric_events):
            start_t = lyr.start.to_time(tempo)
            end_t = lyr.end.to_time(tempo)

            if start_t <= lyric_t and lyric_t <= end_t:
                currently_shown.append(i)

        screen.fill((0, 0, 0))
        if lyric_t > last_t:
            running = False

        for i in currently_shown:
            tri, lyric = lyric_events[i]
            dur = lyric.end.to_time(tempo) - lyric.start.to_time(tempo)
            text = lyr_font.render(f'{lyric.text}', True, (255, 255, 255))
            screen.blit(text, (10, 10 + tri * 70))

        beat_t = BeatTs.from_time(lyric_t, tempo)
        text = dbg_font.render(f't:{lyric_t:03.1f}/{beat_t} | dt:{clock.get_time()}ms',
                               True, (200, 0, 255))
        textpos = text.get_rect(topright=(width, 0))
        screen.blit(text, textpos)

        if output: # print with fixed dt
            lyric_t += 1./60
        else: # interactive run :)
            lyric_t += clock.get_time() / 1000.  # [ms -> s]

        if output:
            video.update(pygame.surfarray.pixels3d(screen).swapaxes(0, 1), inverted=False)
        pygame.display.flip()

    if output:
        video.export(verbose=True)