const fs = require('fs');
const path = require('path');

function checkDir(dir) {
    const files = fs.readdirSync(dir);
    for (const f of files) {
        const full = path.join(dir, f);
        if (fs.statSync(full).isDirectory()) {
            checkDir(full);
        } else if (f.endsWith('.html')) {
            const content = fs.readFileSync(full, 'utf8');
            const match = content.match(/<aside id=["']sidebar-container["'][^>]*>([\s\S]*?)<\/aside>/i);
            const rel = path.relative(path.join(__dirname, '..'), full).replace(/\\/g, '/');
            if (match) {
                const inner = match[1].trim();
                const hasNav = inner.includes('<nav');
                console.log(rel, hasNav ? 'HAS_NAV (' + inner.length + ' chars)' : 'EMPTY_SIDEBAR (' + inner.length + ' chars)');
            } else {
                console.log(rel, 'NO_SIDEBAR_CONTAINER');
            }
        }
    }
}
checkDir(path.join(__dirname, '../frontend'));
