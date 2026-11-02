const path = require('node:path');
const root = path.resolve(__dirname, '../../..');
module.exports = { testDir: __dirname, workers: 1, retries: 0, timeout: 30000,
    reporter: [['list'], ['json', { outputFile: path.join(root, 'docs/implementation/evidence/P04_2026-10-09/browser-tests.json') }]],
    outputDir: path.join(process.env.COSMOS_P04_OUTPUT, 'browser-output'),
    use: { browserName: 'chromium', viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1, reducedMotion: 'reduce',
        launchOptions: { executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' } } };
