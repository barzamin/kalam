import typescript from '@rollup/plugin-typescript';

export default {
    input: 'src/main.ts',
    output: {
        file: 'dist/kalam.jsx',
        format: 'iife',
    },
    'plugins': [typescript()]
};
