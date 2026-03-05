<!DOCTYPE html>
<html lang="ms">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visualisasi Poligon Pro - PUO</title>
    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <style>
        :root {
            --primary: #003366;
            --bg: #f4f4f9;
        }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; display: flex; height: 100vh; background: var(--bg); }
        
        /* Sidebar */
        #sidebar { width: 300px; background: white; padding: 20px; border-right: 1px solid #ddd; overflow-y: auto; }
        .logo-section { text-align: center; margin-bottom: 20px; }
        .logo-placeholder { font-weight: bold; color: var(--primary); font-size: 1.2rem; }
        
        /* Main Content */
        #main { flex: 1; padding: 20px; display: flex; flex-direction: column; }
        .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .metric-card h3 { margin: 0; font-size: 0.8rem; color: #666; }
        .metric-card p { margin: 5px 0 0; font-size: 1.2rem; font-weight: bold; color: var(--primary); }

        #canvas-container { flex: 1; background: white; border-radius: 8px; position: relative; overflow: hidden; border: 1px solid #ccc; }
        canvas { width: 100%; height: 100%; cursor: crosshair; }
        
        input, select, slider { width: 100%; margin-bottom: 15px; }
        label { font-size: 0.9rem; font-weight: bold; display: block; margin-bottom: 5px; }
    </style>
</head>
<body>

<div id="sidebar">
    <div class="logo-section">
        <div class="logo-placeholder">POLITEKNIK UNGKU OMAR</div>
        <p style="font-size: 0.8rem;">Visualisasi Poligon Tanah</p>
    </div>

    <label>Muat Naik CSV (E, N, STN)</label>
    <input type="file" id="csvFile" accept=".csv">

    <hr>
    <label>Tema Warna</label>
    <select id="theme">
        <option value="light">Light Mode</option>
        <option value="dark">Dark Mode</option>
        <option value="blueprint">Blueprint</option>
    </select>

    <label>Saiz Tulisan LUAS</label>
    <input type="range" id="sizeLuas" min="10" max="40" value="20">

    <label>Saiz Label Stesen</label>
    <input type="range" id="sizeStn" min="8" max="20" value="12">
    
    <button id="downloadJson" style="width:100%; padding: 10px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
        📥 Simpan GeoJSON
    </button>
</div>

<div id="main">
    <div class="metrics">
        <div class="metric-card"><h3>Luas (m²)</h3><p id="m-area">0.00</p></div>
        <div class="metric-card"><h3>Luas (Ekar)</h3><p id="m-acre">0.0000</p></div>
        <div class="metric-card"><h3>Stesen</h3><p id="m-stn">0</p></div>
        <div class="metric-card"><h3>Status</h3><p id="m-status">-</p></div>
    </div>

    <div id="canvas-container">
        <canvas id="polyCanvas"></canvas>
    </div>
</div>

<script>
    const fileInput = document.getElementById('csvFile');
    const canvas = document.getElementById('polyCanvas');
    const ctx = canvas.getContext('2d');
    let rawData = [];

    // Listener Input
    fileInput.addEventListener('change', handleFile);
    window.addEventListener('resize', draw);
    document.querySelectorAll('input, select').forEach(el => el.addEventListener('input', draw));

    function handleFile(e) {
        const file = e.target.files[0];
        const reader = new FileReader();
        reader.onload = function(event) {
            const text = event.target.result;
            processData(text);
        };
        reader.readAsText(file);
    }

    function processData(csvText) {
        const lines = csvText.split('\n');
        rawData = [];
        const headers = lines[0].split(',').map(h => h.trim().toUpperCase());
        
        for(let i = 1; i < lines.length; i++) {
            const cols = lines[i].split(',');
            if(cols.length >= 3) {
                rawData.push({
                    E: parseFloat(cols[headers.indexOf('E')]),
                    N: parseFloat(cols[headers.indexOf('N')]),
                    STN: cols[headers.indexOf('STN')]
                });
            }
        }
        calculateArea();
        draw();
    }

    function calculateArea() {
        if (rawData.length < 3) return;
        let area = 0;
        for (let i = 0; i < rawData.length; i++) {
            let j = (i + 1) % rawData.length;
            area += rawData[i].E * rawData[j].N;
            area -= rawData[j].E * rawData[i].N;
        }
        area = Math.abs(area) / 2;
        document.getElementById('m-area').innerText = area.toFixed(2);
        document.getElementById('m-acre').innerText = (area / 4046.856).toFixed(4);
        document.getElementById('m-stn').innerText = rawData.length;
        document.getElementById('m-status').innerText = "Tutup";
        return area;
    }

    function draw() {
        if (rawData.length === 0) return;

        // Set saiz canvas
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;

        const theme = document.getElementById('theme').value;
        const sizeLuas = document.getElementById('sizeLuas').value;
        const sizeStn = document.getElementById('sizeStn').value;

        // Warna Tema
        let bg = "#ffffff", line = "#000000", grid = "#dddddd", text = "#000000";
        if(theme === 'dark') { bg = "#121212"; line = "cyan"; grid = "#333333"; text = "white"; }
        if(theme === 'blueprint') { bg = "#003366"; line = "yellow"; grid = "#004080"; text = "white"; }

        ctx.fillStyle = bg;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Scaling (Fit poligon ke dalam canvas)
        const margin = 50;
        const minE = Math.min(...rawData.map(d => d.E));
        const maxE = Math.max(...rawData.map(d => d.E));
        const minN = Math.min(...rawData.map(d => d.N));
        const maxN = Math.max(...rawData.map(d => d.N));

        const scale = Math.min(
            (canvas.width - margin * 2) / (maxE - minE),
            (canvas.height - margin * 2) / (maxN - minN)
        );

        const tx = (d) => margin + (d - minE) * scale;
        const ty = (d) => canvas.height - (margin + (d - minN) * scale); // Invert Y untuk koordinat utara

        // Draw Grid
        ctx.strokeStyle = grid;
        ctx.setLineDash([5, 5]);
        for(let x = 0; x < canvas.width; x += 50) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
        }
        for(let y = 0; y < canvas.height; y += 50) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
        }
        ctx.setLineDash([]);

        // Draw Polygon
        ctx.beginPath();
        ctx.strokeStyle = line;
        ctx.lineWidth = 2;
        rawData.forEach((p, i) => {
            if (i === 0) ctx.moveTo(tx(p.E), ty(p.N));
            else ctx.lineTo(tx(p.E), ty(p.N));
        });
        ctx.closePath();
        ctx.stroke();
        ctx.fillStyle = "rgba(0, 255, 0, 0.1)";
        ctx.fill();

        // Draw Stations & Labels
        rawData.forEach(p => {
            ctx.fillStyle = "red";
            ctx.beginPath();
            ctx.arc(tx(p.E), ty(p.N), 4, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = "blue";
            ctx.font = `bold ${sizeStn}px Arial`;
            ctx.fillText(p.STN, tx(p.E) + 8, ty(p.N) - 8);
        });

        // Draw Area Label (Centroid)
        const avgE = rawData.reduce((a, b) => a + b.E, 0) / rawData.length;
        const avgN = rawData.reduce((a, b) => a + b.N, 0) / rawData.length;
        
        ctx.fillStyle = "darkgreen";
        ctx.font = `bold ${sizeLuas}px Arial`;
        ctx.textAlign = "center";
        ctx.fillText(`LUAS: ${document.getElementById('m-area').innerText} m²`, tx(avgE), ty(avgN));
    }
</script>

</body>
</html>
