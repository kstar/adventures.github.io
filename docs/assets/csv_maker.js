// This code was written by ChatGPT and Akarsh Simha
async function fetchDSOData(dsoName) {
    // URL encode the deep-sky object name
    const encodedName = encodeURIComponent(dsoName);
    const url = `https://cdsweb.u-strasbg.fr/cgi-bin/nph-sesame/-oxFI2/SVN?${encodedName}`;

    try {
        const response = await fetch(url);
        const text = await response.text(); // Get the response as text
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(text, "application/xml");

        const jposElement = xmlDoc.querySelector('jpos');
        const jpos = jposElement ? jposElement.textContent.trim() : null;

        // Split jpos into RA and DEC
        let ra = null;
        let dec = null;
        if (jpos) {
            const [raPart, decPart] = jpos.split(' ');
            ra = raPart || null;
            dec = decPart || null;
        }

        const magVElement = xmlDoc.querySelector('mag[band="V"] > v');
        const magV = magVElement ? magVElement.textContent.trim() : null;
        const aliases = new Set([...xmlDoc.querySelectorAll('alias')].map(alias => alias.textContent));
        return { ra: ra, dec: dec, mag: magV, aliases: aliases};
    } catch (error) {
        console.error(`Error fetching data for ${dsoName}:`, error);
        return { ra: null, dec: null, mag: null, aliases: null };
    }
}

async function generateCSV() {
    const xDSOs = document.querySelectorAll("x-dso");
    const csvRows = [["Designation", "RA", "DEC", "V Mag"]];

    let finishedIDs = new Set();
    for (const xDSO of xDSOs) {
        const simbadIdentifier = xDSO.getAttribute('simbad')
        const mainDesignation = xDSO.textContent;
        const identifier = simbadIdentifier ? simbadIdentifier : mainDesignation;
        if (finishedIDs.has(identifier)) {
            continue;
        }
        const dsoData = await fetchDSOData(identifier);
        csvRows.push([mainDesignation, dsoData.ra, dsoData.dec, dsoData.mag].map(el => el || ""));
        finishedIDs = finishedIDs.union(dsoData.aliases);
    }

    const csvContent = csvRows.map(row => row.join(",")).join("\n");
    downloadFile(csvContent, "dso_data.csv", "text/csv");
}


function downloadFile(content, fileName, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    link.click();
    URL.revokeObjectURL(link.href);
}

// Save the existing window.onload function if it exists
const existingOnload = window.onload;

// Define a new onload function that includes the existing one and additional code
window.onload = function() {
    // Call the existing onload function if it exists
    if (typeof existingOnload === 'function') {
        existingOnload();
    }

    const N = document.querySelectorAll("x-dso").length;
    if (N == 0) {
        return;
    }

    // Create a button element
    const button = document.createElement('button');
    const icon = document.createElement('img');
    icon.src = 'assets/download_csv.png';
    icon.width = 32;
    icon.alt = 'Download CSV table';
    button.appendChild(icon);
    button.className = 'floating';
    button.title = `Download table containing SIMBAD data on the ${N} underlined objects on this page`;

    // Style the button
    // Add an event listener to the button (optional)
    button.addEventListener('click', async () => {
        const prev_src = icon.src;
        icon.src = 'assets/loading.gif';
        await generateCSV();
        icon.src = prev_src;
    });

    // Append the button to the body
    document.body.appendChild(button);
};
