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
            if (content.includes('sidebar-container')) {
                const match = content.match(/<aside[^>]*id=["']sidebar-container["'][^>]*>([\s\S]*?)<\/aside>/);
                if (match) {
                    const inner = match[1].trim();
                    const hasNav = inner.includes('<nav');
                    const hasToggle = inner.includes('sidebar-toggle-btn') || inner.includes('toggleMuleGuardSidebar');
                    const hasTextClass = inner.includes('sidebar-text');
                    const asideTag = content.match(/<aside[^>]*id=["']sidebar-container["'][^>]*>/)[0];
                    console.log(full.replace(/\\/g, '/'), {
                        innerLen: inner.length,
                        hasNav,
                        hasToggle,
                        hasTextClass,
                        asideTag
                    });
                } else {
                    console.log(full.replace(/\\/g, '/'), 'matched id but not aside tag?');
                }
            }
        }
    }
}
checkDir('frontend');
