/// <reference types="types-for-adobe/AfterEffects/22.0"/>

import {BeatTs, Bundle, Track, Tempo} from './klm';

// -- polyfills
if (String.prototype.trim == null) {
    String.prototype.trim = function () {
        return this.replace(/(^[\s\n\r\t\x0B]+)|([\s\n\r\t\x0B]+$)/g, '')
    };
}
// -- end polyfills

declare function alert(msg: string);

function readTextSync(path: string): string {
    const f = new File(path);
    f.open('r');
    f.encoding = 'UTF-8';
    const data = f.read();
    f.close(); // TODO: check retn

    return data;
}

const bundleFolder = Folder.selectDialog('select klm songfolder');
const manifest = JSON.parse(readTextSync(bundleFolder.absoluteURI + '/song.json'));
const trackfiles = bundleFolder.getFiles('*.kal');
let tracks = [];
for (const trackfile of trackfiles) {
    if (trackfile instanceof Folder) continue;

    trackfile.open('r');
    tracks.push(Track.parse(trackfile.read()));
    trackfile.close();
}

const bundle = new Bundle(manifest['tempo'], tracks);

// alert(JSON.stringify(bundle));
alert(JSON.stringify(BeatTs.fromTime(60*2 + 3.632, new Tempo(190))));