/// <reference types="types-for-adobe/AfterEffects/22.0"/>

import { BeatTs, Bundle, Track, Tempo } from './klm';

// -- polyfills
if (String.prototype.trim == null) {
    String.prototype.trim = function () {
        return this.replace(/(^[\s\n\r\t\x0B]+)|([\s\n\r\t\x0B]+$)/g, '')
    };
}
// -- end polyfills

function readTextSync(path: string): string {
    const f = new File(path);
    f.open('r');
    f.encoding = 'UTF-8';
    const data = f.read();
    f.close(); // TODO: check retn

    return data;
}

function loadBundle(bundleFolder: Folder): Bundle {
    const manifest = JSON.parse(readTextSync(bundleFolder.absoluteURI + '/song.json'));
    const trackfiles = bundleFolder.getFiles('*.kal');
    let tracks = [], trackNames = [];
    for (const trackfile of trackfiles) {
        if (trackfile instanceof Folder) continue;

        trackfile.open('r');
        tracks.push(Track.parse(trackfile.read()));
        trackNames.push(trackfile.name);
        trackfile.close();
    }

    return new Bundle(new Tempo(manifest['tempo']), tracks, trackNames);
}

const bundleFolder = Folder.selectDialog('select klm songfolder');
const bundle = loadBundle(bundleFolder);

function roundToFrame(t, fps) {
    return Math.floor(t * fps) / fps;
}

const comp = app.project.activeItem;
if (comp instanceof CompItem) {
    const fps = comp.frameRate;
    const tempo = bundle.tempo;

    app.beginUndoGroup('kalam_import');
    for (let i = 0; i < bundle.tracks.length; i++) {
        const track = bundle.tracks[i];
        const textLayer = comp.layers.addText('');
        textLayer.name = `KAL:${bundle.trackNames[i]}`;
        // TODO: figure out how to unfuck prop typing.
        (textLayer.property('Position') as any).setValue([10, 50 + i * 70]);

        track.lyrics.sort((a, b) => {
            return a.start.toTime(tempo) - b.start.toTime(tempo);
        });

        // insert an empty keyframe to avoid flickering/reading
        // the first content keyframe when the layer starts
        let textKfTimestamps = [0], textKfValues = [''];

        for (let i = 0; i < track.lyrics.length; i++) {
            const currLyric = track.lyrics[i];
            const roundedStart = roundToFrame(currLyric.start.toTime(tempo), fps);
            const roundedEnd = roundToFrame(currLyric.end.toTime(tempo), fps);

            textKfTimestamps.push(roundedStart);
            textKfValues.push(currLyric.text);

            const nextLyric = track.lyrics[i + 1];
            // dont keyframe out if the next text picks up on the same frame
            if (!(nextLyric && roundToFrame(nextLyric.start.toTime(tempo), fps) == roundedEnd)) {
                textKfTimestamps.push(roundedEnd);
                textKfValues.push('');
            }
        }
        const textProp = textLayer.property('ADBE Text Properties').property('ADBE Text Document') as any; // fuck this
        textProp.setValuesAtTimes(textKfTimestamps, textKfValues);
    }
    app.endUndoGroup();
}