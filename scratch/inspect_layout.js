const fs = require('fs');
const path = require('path');

function checkDir(dir) {
    const files = fs.readdirSync(dir);
    for (const f of files) {
        const full = path.join(dir, f);
        if (fs.statSync(full).isDirectory()) {
            checkDir(full);
        } else if (f.endsWith('.html') && (full.includes('bank') || full.includes('internal'))) {
            const content = fs.readFileSync(full, 'utf8');
            const lines = content.split('\n');
            console.log('\n---', full.replace(/\\/g, '/'), '---');
            
            // Check aside tag
            for (let i = 0; i < lines.length; i++) {
                if (lines[i].includes('id="sidebar-container"') || lines[i].includes("id='sidebar-container'")) {
                    console.log('  aside line:', lines[i].trim());
                }
            }

            // Find elements immediately after aside or elements with md:pl or id=main
            const asideEnd = content.indexOf('</aside>');
            if (asideEnd !== -1) {
                const afterAside = content.substring(asideEnd, asideEnd + 1000);
                const firstDivs = afterAside.match(/<(?:div|main)[^>]*>/g) || [];
                console.log('  next 2 containers after aside:');
                firstDivs.slice(0, 2).forEach(d => console.log('   ', d));
            }
        }
    }
}
checkDir('frontend');
