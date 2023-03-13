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

    return new Bundle(manifest['tempo'], tracks, trackNames);
}

const bundleFolder = Folder.selectDialog('select klm songfolder');
const bundle = loadBundle(bundleFolder);

const comp = app.project.activeItem;
if (comp instanceof CompItem) {
    const fps = comp.frameRate;
    const tempo = bundle.tempo;

    app.beginUndoGroup('kalam_import');
    for (let i = 0; i < bundle.tracks.length; i++) {
        const track = bundle.tracks[i];
        const textLayer = comp.layers.addText('');
        textLayer.name = `KAL:${bundle.trackNames[i]}`;
    }
    app.endUndoGroup();
}