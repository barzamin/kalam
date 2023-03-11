import { FOO } from './common';

declare var File: {
    openDialog(title: string, filetypes: string): string;
};
declare function alert(msg: string);

const fname: string = File.openDialog('select klm file', 'Kalam files:*.klm,All files:*.*');

alert(`foo=${FOO}`);