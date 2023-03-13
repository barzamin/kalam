export class Bundle {
    tempo: Tempo;
    tracks: Track[];

    constructor(tempo: Tempo, tracks: Track[]) {
        this.tempo = tempo;
        this.tracks = tracks;
    }
}

export class Tempo {
    bpm: number;
    period: number;
    constructor(bpm: number) {
        this.bpm = bpm;
        this.period = 60/bpm;
    }
}


export class TimeSig {
    // TODO lmao assumes qn gets beat
    numerator: number;

    constructor(numerator: number, _denominator: number) {
        this.numerator = numerator;
    }
}
const FOUR_FOUR = new TimeSig(4,4)

export class BeatTs {
    bar: number;
    beat: number;
    tick: number;
    pct: number;
    timeSig: TimeSig;

    constructor(bar: number, beat: number, tick: number, pct: number, timeSig: TimeSig = null) {
        this.bar = bar;
        this.beat = beat;
        this.tick = tick;
        this.pct = pct;
        this.timeSig = timeSig || FOUR_FOUR;
    }

    static fromString(str: string) {
        const parts = str.trim().split('.').map(Number);

        const bar = parts[0] - 1;
        let [beat, tick, pct] = [0, 0, 0];
        if (parts.length > 1) {
            beat = parts[1] - 1;
        }
        if (parts.length > 2) {
            tick = parts[2] - 1;
        }
        if (parts.length > 3) {
            pct = parts[3];
        }

        return new BeatTs(bar, beat, tick, pct);
    }

    // toString(): string {
    //     return `${this.bar+1}.${this.beat+1}.${this.tick+1}.${this.pct.toString().padStart(2, ' ')}`;
    // }

    toTime(tempo: Tempo) {
        // TODO: ASSUMES 16th TICKS AND QN BEATS
        const beats = this.bar * this.timeSig.numerator
            + this.beat
            + this.tick/4
            + this.pct/400;

        return beats * tempo.period;
    }

    static fromTime(t: number, tempo: Tempo, timeSig: TimeSig = null) {
        const ts = timeSig || FOUR_FOUR;

        // TODO: ASSUMES 16th TICKS AND QN BEATS
        const ticksPerBeat = 4;
        const tickPeriod = tempo.period / ticksPerBeat;
        let ticks = t / tickPeriod;
        const pct = ((ticks % 1) * 100) << 0;
        ticks = ticks << 0;

        let beat = (ticks / ticksPerBeat) << 0;
        ticks = ticks % ticksPerBeat;

        const bar = (beat / ts.numerator) << 0;
        beat = beat % ts.numerator;

        return new BeatTs(bar, beat, ticks, pct, ts);
    }
}

export class Lyric {
    start: BeatTs;
    end: BeatTs;
    text: string;

    constructor(start: BeatTs, end: BeatTs, text: string) {
        this.start = start;
        this.end = end;
        this.text = text;
    }
}

export class Track {
    static readonly LYRIC_RE = /\[([\d.]+)\s+->\s+([\d.]+)]\s+(\+?)(.*)/;

    lyrics: Lyric[];

    constructor(lyrics: Lyric[]) {
        this.lyrics = lyrics;
    }

    static parse(text: string) {
        const lines = text.split('\n');

        let lyrics = [];
        for (let line of lines) {
            line = line.trim();
            if (line.length == 0) continue; // skip whitespace lines

            const prevLyric = lyrics[lyrics.length - 1];

            const groups = line.match(Track.LYRIC_RE);
            let text = groups[4];
            const incr = groups[3];
            if (incr == '+')
                text = prevLyric.text + text;

            const fr = (groups[1] == '.') ? prevLyric.end : BeatTs.fromString(groups[1]);
            const to = BeatTs.fromString(groups[2]);

            lyrics.push(new Lyric(fr, to, text));
        }

        return new Track(lyrics);
    }
}
