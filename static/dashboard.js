let countdown = 15;

async function fetchPrices() {
    const res = await fetch("/api/prices");
    const data = await res.json();
    
    document.getElementById("last-update").textContent = new Date().toLocaleTimeString();
    document.getElementById("cache-status").textContent = data.cached ? "HIT" : "MISS";
    
    const grid = document.getElementById("pairs-grid");
    grid.innerHTML = "";
    
    for (const [pair, dexes] of Object.entries(data.prices)) {
        const spread = data.spreads[pair];
        const spreadPct = spread ? spread.spread_pct.toFixed(4) : "0.0000";
        const spreadClass = spreadPct > 0.5 ? "hot" : spreadPct > 0.1 ? "warm" : "cold";
        
        let dexRows = "";
        for (const [dex, info] of Object.entries(dexes)) {
            if (info.error) {
                dexRows += `<div class="dex-row"><span>${dex}</span><span style="color:#f85149">Error</span></div>`;
            } else {
                const isBest = spread && spread.best_buy === dex;
                dexRows += `
                    <div class="dex-row">
                        <span>${dex} ${isBest ? "✅" : ""}</span>
                        <span>${info.price.toFixed(4)}</span>
                    </div>
                    <div style="font-size:0.75em;color:#8b949e;padding-left:8px">
                        Reserves: ${formatNumber(info.reserve0)} ${info.token0} / ${formatNumber(info.reserve1)} ${info.token1}
                    </div>`;
            }
        }
        
        grid.innerHTML += `
            <div class="card">
                <h3>${pair} 
                    <span class="spread ${spreadClass}">△${spreadPct}%</span>
                </h3>
                ${dexRows}
            </div>`;
    }
}

function formatNumber(n) {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
    if (n >= 1_000) return (n / 1_000).toFixed(2) + "K";
    return n.toFixed(4);
}

async function calcSlippage() {
    const pair   = document.getElementById("calc-pair").value;
    const dex    = document.getElementById("calc-dex").value;
    const amount = document.getElementById("calc-amount").value;
    const result = document.getElementById("calc-result");

    // For WETH/* pairs the contract stores token0=stable, token1=WETH
    // so we must tell the API we are selling token1 (WETH)
    const token_in = pair.startsWith("WETH/") ? "token1" : "token0";

    result.innerHTML = `<span style="color:#8b949e">Calculating...</span>`;

    try {
        const res  = await fetch(`/api/slippage?pair=${encodeURIComponent(pair)}&dex=${dex}&amount=${amount}&token_in=${token_in}`);
        const data = await res.json();

        if (data.error) {
            result.innerHTML = `<span style="color:#f85149">Error: ${data.error}</span>`;
            return;
        }

        const impactColor  = data.price_impact_pct > 1  ? "#f85149" : data.price_impact_pct > 0.3 ? "#d29922" : "#3fb950";
        const slippageColor = data.slippage_pct    > 1  ? "#f85149" : "#3fb950";

        result.innerHTML = `
            <table>
                <tr><td>Selling</td><td>${amount} ${data.selling}</td></tr>
                <tr><td>Buying</td><td>${data.amount_out.toFixed(4)} ${data.buying}</td></tr>
                <tr><td>Spot Price</td><td>${data.mid_price.toFixed(4)}</td></tr>
                <tr><td>Effective Price</td><td>${data.effective_price.toFixed(4)}</td></tr>
                <tr><td>Slippage</td><td style="color:${slippageColor}">${data.slippage_pct.toFixed(4)}%</td></tr>
                <tr><td>Price Impact</td><td style="color:${impactColor}">${data.price_impact_pct.toFixed(4)}% 🥪</td></tr>
            </table>`;
    } catch (e) {
        result.innerHTML = `<span style="color:#f85149">Request failed: ${e.message}</span>`;
    }
}

// Auto-refresh
function tick() {
    countdown--;
    document.getElementById("countdown").textContent = countdown + "s";
    if (countdown <= 0) {
        countdown = 15;
        fetchPrices();
    }
}

fetchPrices();
setInterval(tick, 1000);
