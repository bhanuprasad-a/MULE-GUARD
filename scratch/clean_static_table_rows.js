const fs = require('fs');

['frontend/bank/investigator/transactions.html', 'frontend/bank/compliance/transactions.html'].forEach(f => {
    let content = fs.readFileSync(f, 'utf8');
    // Replace the static tbody contents with clean empty tbody
    content = content.replace(/<tbody class="divide-y divide-\[#f1f5f9\]" id="transactions-tbody" aria-live="polite">[\s\S]*?<\/tbody>/, '<tbody class="divide-y divide-[#f1f5f9]" id="transactions-tbody" aria-live="polite">\n\t\t\t\t\t\t\t\t\t\t\t\t\t<!-- Populated dynamically from PostgreSQL via MuleGuardStore -->\n\t\t\t\t\t\t\t\t\t\t\t\t</tbody>');
    
    // Also check for any remaining legacy names in drawers or comments
    content = content.replace(/Apex Trading Ltd/g, 'Prakash Chatterjee');
    content = content.replace(/Apex Trading/g, 'Prakash Chatterjee');
    content = content.replace(/Orion Financial/g, 'Kalyan Chowdary');
    content = content.replace(/Vertex Imports/g, 'Suresh Babu');
    content = content.replace(/Northstar Holdings/g, 'Venkatesh Naidu');
    content = content.replace(/Blackwood Assets/g, 'Sri Venkateswara');
    content = content.replace(/Shell Partner/g, 'Retail Ingress');

    fs.writeFileSync(f, content, 'utf8');
    console.log('Cleaned static rows in', f);
});

['frontend/bank/investigator/entities.html', 'frontend/bank/compliance/entities.html'].forEach(f => {
    let content = fs.readFileSync(f, 'utf8');
    // Replace the static tbody contents with clean empty tbody
    content = content.replace(/<tbody class="divide-y divide-\[#f1f5f9\]" id="entities-tbody">[\s\S]*?<\/tbody>/, '<tbody class="divide-y divide-[#f1f5f9]" id="entities-tbody">\n\t\t\t\t\t\t\t\t\t\t\t\t\t<!-- Populated dynamically from PostgreSQL via MuleGuardStore -->\n\t\t\t\t\t\t\t\t\t\t\t\t</tbody>');
    
    // Replace remaining legacy names
    content = content.replace(/Apex Trading Ltd/g, 'Prakash Chatterjee');
    content = content.replace(/Apex Trading/g, 'Prakash Chatterjee');
    content = content.replace(/Orion Financial/g, 'Kalyan Chowdary');
    content = content.replace(/Vertex Imports/g, 'Suresh Babu');
    content = content.replace(/Northstar Holdings/g, 'Venkatesh Naidu');
    content = content.replace(/Blackwood Assets/g, 'Sri Venkateswara');
    content = content.replace(/Shell Partner/g, 'Retail Ingress');

    fs.writeFileSync(f, content, 'utf8');
    console.log('Cleaned static rows in', f);
});
