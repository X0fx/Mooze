// docs/ascii-plasma.js
const canvas = document.getElementById('plasma-canvas');
const ctx = canvas.getContext('2d');

let width, height, cols, rows;
const fontSize = 14; 

// Expanded 70-character density set for smooth, high-resolution depth
const chars = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$";

// Reduced brightness layers (capped at 0.32 alpha max to stay subtle)
const depthColors = [
    "rgba(34, 197, 94, 0.03)",
    "rgba(34, 197, 94, 0.08)",
    "rgba(34, 197, 94, 0.15)",
    "rgba(34, 197, 94, 0.22)",
    "rgba(34, 197, 94, 0.32)" 
];

function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    cols = Math.floor(width / fontSize);
    rows = Math.floor(height / fontSize);
    ctx.font = `bold ${fontSize}px monospace`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
}

window.addEventListener('resize', resize);
resize();

let time = 0;

function draw() {
    ctx.fillStyle = '#09090b'; 
    ctx.fillRect(0, 0, width, height);

    for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
            // Tight perlin spatial frequency
            let nx = x * 0.11; 
            let ny = y * 0.11;

            // Multi-frequency aperiodic noise synthesis (using irrational step ratios)
            let v1 = Math.sin(nx * 1.000 + time * 0.70);
            let v2 = Math.sin(ny * 1.314 + time * 0.43);
            let v3 = Math.sin((nx + ny) * 0.707 + time * 0.29);
            let v4 = Math.sin(Math.sqrt(nx * nx + ny * ny) * 0.500 + time * 0.17);
            let v5 = Math.sin(nx * 0.382 - ny * 0.618 + time * 0.11); // Golden ratio offsets

            let sum = v1 + v2 + v3 + v4 + v5;
            let normalized = (sum + 5) / 10; // Normalize [-5, 5] -> [0, 1]

            // 1. Map to expanded character ramp
            let charIndex = Math.floor(normalized * chars.length);
            charIndex = Math.max(0, Math.min(chars.length - 1, charIndex));

            // 2. Map to dim depth colors
            let colorIndex = Math.floor(normalized * depthColors.length);
            colorIndex = Math.max(0, Math.min(depthColors.length - 1, colorIndex));

            ctx.fillStyle = depthColors[colorIndex];
            ctx.fillText(chars[charIndex], x * fontSize + fontSize/2, y * fontSize + fontSize/2);
        }
    }
    time += 0.035; // Smooth time progression
}

setInterval(draw, 40);