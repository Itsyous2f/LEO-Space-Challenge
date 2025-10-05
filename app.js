// Global variables
let emitData = null;
let currentDataset = 0;
let currentVisualization = 'heatmap';
let currentGroup = 'both';

// Color scales
const bandDepthColorScale = d3.scaleSequential(d3.interpolateViridis).domain([0, 0.5]);
const mineralColorScale = d3.scaleOrdinal(d3.schemeCategory10);

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadData();
});

function setupEventListeners() {
    // Control panel event listeners
    document.getElementById('dataset-select').addEventListener('change', function() {
        currentDataset = parseInt(this.value);
        updateVisualization();
        updateDatasetInfo();
    });
    
    document.getElementById('group-select').addEventListener('change', function() {
        currentGroup = this.value;
        updateVisualization();
    });
    
    document.getElementById('visualization-type').addEventListener('change', function() {
        currentVisualization = this.value;
        updateVisualization();
    });
    
    document.getElementById('load-data-btn').addEventListener('click', loadData);
    document.getElementById('export-btn').addEventListener('click', exportVisualization);
}

async function loadData() {
    try {
        showLoading();
        console.log('Loading EMIT data...');
        
        // Try to load the sample data first (smaller file)
        const response = await fetch('web_data_sample.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        emitData = await response.json();
        console.log('Data loaded successfully:', emitData);
        
        hideLoading();
        updateDatasetInfo();
        updateMineralLegend();
        updateVisualization();
        
    } catch (error) {
        console.error('Error loading data:', error);
        showError('Failed to load EMIT data. Please check that web_data_sample.json exists and is accessible.');
    }
}

function showLoading() {
    document.getElementById('loading-indicator').classList.remove('hidden');
    document.getElementById('main-visualization').classList.add('hidden');
    document.getElementById('error-display').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loading-indicator').classList.add('hidden');
    document.getElementById('main-visualization').classList.remove('hidden');
}

function showError(message) {
    document.getElementById('loading-indicator').classList.add('hidden');
    document.getElementById('main-visualization').classList.add('hidden');
    document.getElementById('error-display').classList.remove('hidden');
    document.getElementById('error-message').textContent = message;
}

function updateDatasetInfo() {
    if (!emitData || !emitData.datasets[currentDataset]) return;
    
    const dataset = emitData.datasets[currentDataset];
    const summary = dataset.summary;
    
    const metadataHtml = `
        <div class="metadata-item">
            <span class="metadata-label">File:</span>
            <span class="metadata-value">${summary.filename}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Start Time:</span>
            <span class="metadata-value">${summary.time_start}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">End Time:</span>
            <span class="metadata-value">${summary.time_end}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Latitude:</span>
            <span class="metadata-value">${summary.spatial_extent.south.toFixed(3)}° to ${summary.spatial_extent.north.toFixed(3)}°</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Longitude:</span>
            <span class="metadata-value">${summary.spatial_extent.west.toFixed(3)}° to ${summary.spatial_extent.east.toFixed(3)}°</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Group 1 Minerals:</span>
            <span class="metadata-value">${summary.group1_minerals.length}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Group 2 Minerals:</span>
            <span class="metadata-value">${summary.group2_minerals.length}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">G1 Pixels with Minerals:</span>
            <span class="metadata-value">${summary.band_depth_stats.group1.pixels_with_minerals.toLocaleString()}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">G2 Pixels with Minerals:</span>
            <span class="metadata-value">${summary.band_depth_stats.group2.pixels_with_minerals.toLocaleString()}</span>
        </div>
    `;
    
    document.getElementById('dataset-metadata').innerHTML = metadataHtml;
}

function updateMineralLegend() {
    if (!emitData) return;
    
    const dataset = emitData.datasets[currentDataset];
    const allMinerals = [...new Set([...dataset.summary.group1_minerals, ...dataset.summary.group2_minerals])];
    
    let legendHtml = '';
    allMinerals.forEach(mineralId => {
        const mineralName = emitData.mineral_mapping[mineralId] || `Mineral ${mineralId}`;
        const color = mineralColorScale(mineralId);
        const group = dataset.summary.group1_minerals.includes(mineralId) ? 'G1' : 'G2';
        
        legendHtml += `
            <div class="mineral-item">
                <div class="mineral-color" style="background-color: ${color}"></div>
                <span class="mineral-name">${group}: ${mineralName}</span>
            </div>
        `;
    });
    
    document.getElementById('mineral-list').innerHTML = legendHtml;
}

function updateVisualization() {
    if (!emitData) return;
    
    // Hide all visualization containers
    document.getElementById('heatmap-container').classList.add('hidden');
    document.getElementById('mineral-map-container').classList.add('hidden');
    document.getElementById('statistics-container').classList.add('hidden');
    
    // Show the selected visualization
    switch (currentVisualization) {
        case 'heatmap':
            document.getElementById('viz-title').textContent = 'Band Depth Heatmap';
            document.getElementById('heatmap-container').classList.remove('hidden');
            createHeatmaps();
            break;
        case 'mineral-map':
            document.getElementById('viz-title').textContent = 'Mineral ID Distribution';
            document.getElementById('mineral-map-container').classList.remove('hidden');
            createMineralMap();
            break;
        case 'statistics':
            document.getElementById('viz-title').textContent = 'Statistical Analysis';
            document.getElementById('statistics-container').classList.remove('hidden');
            createStatisticsCharts();
            break;
    }
}

function createHeatmaps() {
    const dataset = emitData.datasets[currentDataset];
    const vizData = dataset.visualization_data;
    
    // Show/hide groups based on selection
    const group1Section = document.getElementById('group1-heatmap');
    const group2Section = document.getElementById('group2-heatmap');
    
    group1Section.style.display = (currentGroup === 'group2') ? 'none' : 'block';
    group2Section.style.display = (currentGroup === 'group1') ? 'none' : 'block';
    
    if (currentGroup !== 'group2') {
        createHeatmap('group1-svg', vizData.group1_band_depth, vizData.group1_mineral_id, 'Group 1');
    }
    
    if (currentGroup !== 'group1') {
        createHeatmap('group2-svg', vizData.group2_band_depth, vizData.group2_mineral_id, 'Group 2');
    }
}

function createHeatmap(svgId, bandDepthData, mineralIdData, groupName) {
    const svg = d3.select(`#${svgId}`);
    svg.selectAll('*').remove();
    
    const margin = { top: 10, right: 10, bottom: 10, left: 10 };
    const width = 400 - margin.left - margin.right;
    const height = 300 - margin.bottom - margin.top;
    
    svg.attr('width', width + margin.left + margin.right)
       .attr('height', height + margin.bottom + margin.top);
    
    const g = svg.append('g')
                 .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const rows = bandDepthData.length;
    const cols = bandDepthData[0].length;
    
    const xScale = d3.scaleLinear().domain([0, cols]).range([0, width]);
    const yScale = d3.scaleLinear().domain([0, rows]).range([0, height]);
    
    const cellWidth = width / cols;
    const cellHeight = height / rows;
    
    // Create heatmap cells
    for (let i = 0; i < rows; i++) {
        for (let j = 0; j < cols; j++) {
            const bandDepth = bandDepthData[i][j];
            const mineralId = mineralIdData[i][j];
            
            if (mineralId > 0 && !isNaN(bandDepth)) {
                g.append('rect')
                 .attr('x', j * cellWidth)
                 .attr('y', i * cellHeight)
                 .attr('width', cellWidth)
                 .attr('height', cellHeight)
                 .attr('fill', bandDepthColorScale(bandDepth))
                 .attr('stroke', 'none')
                 .on('mouseover', function(event) {
                     showTooltip(event, {
                         group: groupName,
                         row: i,
                         col: j,
                         bandDepth: bandDepth.toFixed(3),
                         mineralId: mineralId,
                         mineralName: emitData.mineral_mapping[mineralId] || `Mineral ${mineralId}`
                     });
                 })
                 .on('mouseout', hideTooltip);
            }
        }
    }
    
    // Create colorbar
    createColorbar(`${svgId.replace('-svg', '-colorbar')}`, bandDepthColorScale, [0, 0.5], 'Band Depth');
}

function createColorbar(containerId, colorScale, domain, label) {
    const container = d3.select(`#${containerId}`);
    container.selectAll('*').remove();
    
    const width = 200;
    const height = 20;
    
    const svg = container.append('svg')
                        .attr('width', width + 60)
                        .attr('height', height + 30);
    
    const gradient = svg.append('defs')
                       .append('linearGradient')
                       .attr('id', `gradient-${containerId}`)
                       .attr('x1', '0%')
                       .attr('x2', '100%');
    
    const numStops = 10;
    for (let i = 0; i <= numStops; i++) {
        const t = i / numStops;
        const value = domain[0] + t * (domain[1] - domain[0]);
        gradient.append('stop')
                .attr('offset', `${t * 100}%`)
                .attr('stop-color', colorScale(value));
    }
    
    svg.append('rect')
       .attr('x', 0)
       .attr('y', 0)
       .attr('width', width)
       .attr('height', height)
       .attr('fill', `url(#gradient-${containerId})`)
       .attr('stroke', '#ccc');
    
    svg.append('text')
       .attr('x', 0)
       .attr('y', height + 15)
       .text(domain[0].toFixed(1))
       .style('font-size', '12px')
       .style('fill', '#666');
    
    svg.append('text')
       .attr('x', width)
       .attr('y', height + 15)
       .attr('text-anchor', 'end')
       .text(domain[1].toFixed(1))
       .style('font-size', '12px')
       .style('fill', '#666');
    
    svg.append('text')
       .attr('x', width / 2)
       .attr('y', height + 15)
       .attr('text-anchor', 'middle')
       .text(label)
       .style('font-size', '12px')
       .style('fill', '#333')
       .style('font-weight', 'bold');
}

function createMineralMap() {
    const dataset = emitData.datasets[currentDataset];
    const vizData = dataset.visualization_data;
    
    const container = d3.select('#mineral-map-container');
    container.selectAll('*').remove();
    
    // Create a container div for the mineral maps
    const mapContainer = container.append('div')
                                  .style('display', 'grid')
                                  .style('grid-template-columns', currentGroup === 'both' ? '1fr 1fr' : '1fr')
                                  .style('gap', '2rem')
                                  .style('justify-items', 'center');
    
    // Show/hide groups based on selection
    if (currentGroup !== 'group2') {
        const group1Container = mapContainer.append('div')
                                           .style('text-align', 'center');
        group1Container.append('h4')
                      .style('margin-bottom', '1rem')
                      .style('color', '#555')
                      .text('Group 1 Mineral Distribution');
        
        createMineralIdMap(group1Container, vizData.group1_mineral_id, 'group1', 'Group 1');
    }
    
    if (currentGroup !== 'group1') {
        const group2Container = mapContainer.append('div')
                                           .style('text-align', 'center');
        group2Container.append('h4')
                      .style('margin-bottom', '1rem')
                      .style('color', '#555')
                      .text('Group 2 Mineral Distribution');
        
        createMineralIdMap(group2Container, vizData.group2_mineral_id, 'group2', 'Group 2');
    }
}

function createMineralIdMap(container, mineralIdData, groupName, groupDisplayName) {
    const margin = { top: 10, right: 10, bottom: 10, left: 10 };
    const width = 400 - margin.left - margin.right;
    const height = 300 - margin.bottom - margin.top;
    
    const svg = container.append('svg')
                        .attr('width', width + margin.left + margin.right)
                        .attr('height', height + margin.bottom + margin.top);
    
    const g = svg.append('g')
                 .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const rows = mineralIdData.length;
    const cols = mineralIdData[0].length;
    
    const cellWidth = width / cols;
    const cellHeight = height / rows;
    
    // Get unique mineral IDs in this group for color scaling
    const uniqueMinerals = [...new Set(mineralIdData.flat().filter(id => id > 0))];
    
    // Create a color scale with enough distinct colors
    const mineralColors = d3.scaleOrdinal()
                            .domain(uniqueMinerals)
                            .range(d3.schemeSet3.concat(d3.schemeSet2).concat(d3.schemeSet1));
    
    // Create mineral map cells
    for (let i = 0; i < rows; i++) {
        for (let j = 0; j < cols; j++) {
            const mineralId = mineralIdData[i][j];
            
            if (mineralId > 0 && !isNaN(mineralId)) {
                const mineralName = emitData.mineral_mapping[mineralId] || `Mineral ${mineralId}`;
                const color = mineralColors(mineralId);
                
                g.append('rect')
                 .attr('x', j * cellWidth)
                 .attr('y', i * cellHeight)
                 .attr('width', cellWidth)
                 .attr('height', cellHeight)
                 .attr('fill', color)
                 .attr('stroke', '#ffffff')
                 .attr('stroke-width', 0.1)
                 .on('mouseover', function(event) {
                     showTooltip(event, {
                         group: groupDisplayName,
                         row: i,
                         col: j,
                         mineralId: mineralId,
                         mineralName: mineralName,
                         color: color
                     });
                 })
                 .on('mouseout', hideTooltip);
            }
        }
    }
    
    // Create a mineral legend for this group
    createMineralLegend(container, uniqueMinerals, mineralColors, groupDisplayName);
}

function createMineralLegend(container, uniqueMinerals, colorScale, groupName) {
    const legendContainer = container.append('div')
                                   .style('margin-top', '1rem')
                                   .style('max-height', '200px')
                                   .style('overflow-y', 'auto')
                                   .style('border', '1px solid #ddd')
                                   .style('border-radius', '6px')
                                   .style('padding', '0.75rem')
                                   .style('background', '#f8f9fa');
    
    legendContainer.append('h5')
                  .style('margin', '0 0 0.5rem 0')
                  .style('font-size', '0.9rem')
                  .style('color', '#333')
                  .text(`${groupName} Minerals (${uniqueMinerals.length} types)`);
    
    const legendItems = legendContainer.append('div')
                                     .style('display', 'grid')
                                     .style('grid-template-columns', 'repeat(auto-fit, minmax(200px, 1fr))')
                                     .style('gap', '0.25rem');
    
    uniqueMinerals.forEach(mineralId => {
        const mineralName = emitData.mineral_mapping[mineralId] || `Mineral ${mineralId}`;
        const color = colorScale(mineralId);
        
        const item = legendItems.append('div')
                               .style('display', 'flex')
                               .style('align-items', 'center')
                               .style('gap', '0.5rem')
                               .style('padding', '0.2rem')
                               .style('border-radius', '3px')
                               .style('font-size', '0.8rem')
                               .on('mouseover', function() {
                                   d3.select(this).style('background-color', '#e9ecef');
                               })
                               .on('mouseout', function() {
                                   d3.select(this).style('background-color', 'transparent');
                               });
        
        item.append('div')
            .style('width', '12px')
            .style('height', '12px')
            .style('background-color', color)
            .style('border', '1px solid #ccc')
            .style('border-radius', '2px')
            .style('flex-shrink', '0');
        
        item.append('span')
            .style('color', '#555')
            .style('overflow', 'hidden')
            .style('text-overflow', 'ellipsis')
            .style('white-space', 'nowrap')
            .text(`${mineralId}: ${mineralName}`);
    });
}

function createStatisticsCharts() {
    const dataset = emitData.datasets[currentDataset];
    const summary = dataset.summary;
    
    // Mineral count chart
    createMineralCountChart(summary);
    
    // Band depth statistics chart
    createBandDepthChart(summary);
    
    // Spatial distribution placeholder
    createSpatialChart();
    
    // Comparison chart placeholder
    createComparisonChart();
}

function createMineralCountChart(summary) {
    const ctx = document.getElementById('mineral-count-chart');
    if (ctx.chart) {
        ctx.chart.destroy();
    }
    
    ctx.chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Group 1', 'Group 2'],
            datasets: [{
                label: 'Number of Unique Minerals',
                data: [summary.group1_minerals.length, summary.group2_minerals.length],
                backgroundColor: ['#667eea', '#764ba2'],
                borderColor: ['#5a6fd8', '#6a4190'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Mineral Count by Group'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function createBandDepthChart(summary) {
    const ctx = document.getElementById('band-depth-chart');
    if (ctx.chart) {
        ctx.chart.destroy();
    }
    
    ctx.chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Min', 'Mean', 'Max'],
            datasets: [{
                label: 'Group 1',
                data: [
                    summary.band_depth_stats.group1.min,
                    summary.band_depth_stats.group1.mean,
                    summary.band_depth_stats.group1.max
                ],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                fill: true
            }, {
                label: 'Group 2',
                data: [
                    summary.band_depth_stats.group2.min,
                    summary.band_depth_stats.group2.mean,
                    summary.band_depth_stats.group2.max
                ],
                borderColor: '#764ba2',
                backgroundColor: 'rgba(118, 75, 162, 0.1)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Band Depth Statistics'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 0.5
                }
            }
        }
    });
}

function createSpatialChart() {
    const ctx = document.getElementById('spatial-distribution-chart');
    if (ctx.chart) {
        ctx.chart.destroy();
    }
    
    ctx.chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Pixels with Minerals', 'Pixels without Minerals'],
            datasets: [{
                data: [25, 75], // Placeholder data
                backgroundColor: ['#667eea', '#e9ecef'],
                borderColor: ['#5a6fd8', '#dee2e6'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Mineral Coverage'
                }
            }
        }
    });
}

function createComparisonChart() {
    const ctx = document.getElementById('comparison-chart');
    if (ctx.chart) {
        ctx.chart.destroy();
    }
    
    ctx.chart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Coverage', 'Diversity', 'Intensity', 'Quality'],
            datasets: [{
                label: 'Group 1',
                data: [65, 59, 80, 81],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.2)',
                pointBackgroundColor: '#667eea'
            }, {
                label: 'Group 2',
                data: [28, 48, 40, 19],
                borderColor: '#764ba2',
                backgroundColor: 'rgba(118, 75, 162, 0.2)',
                pointBackgroundColor: '#764ba2'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Group Comparison'
                }
            }
        }
    });
}

function showTooltip(event, data) {
    const tooltip = document.getElementById('tooltip');
    const content = document.getElementById('tooltip-content');
    
    let tooltipHTML = `<strong>${data.group}</strong><br>Position: (${data.row}, ${data.col})<br>`;
    
    if (data.bandDepth !== undefined) {
        // Heatmap tooltip
        tooltipHTML += `Band Depth: ${data.bandDepth}<br>`;
    }
    
    if (data.color !== undefined) {
        // Mineral map tooltip with color indicator
        tooltipHTML += `<div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem;">
                           <div style="width: 16px; height: 16px; background-color: ${data.color}; border: 1px solid #ccc; border-radius: 3px;"></div>
                           <span>Color</span>
                       </div>`;
    }
    
    tooltipHTML += `Mineral ID: ${data.mineralId}<br>Mineral: ${data.mineralName}`;
    
    content.innerHTML = tooltipHTML;
    
    tooltip.style.left = (event.pageX + 10) + 'px';
    tooltip.style.top = (event.pageY - 10) + 'px';
    tooltip.classList.remove('hidden');
}

function hideTooltip() {
    document.getElementById('tooltip').classList.add('hidden');
}

function exportVisualization() {
    // Simple export functionality - could be enhanced
    html2canvas(document.getElementById('main-visualization')).then(canvas => {
        const link = document.createElement('a');
        link.download = `emit-visualization-${new Date().toISOString().slice(0, 10)}.png`;
        link.href = canvas.toDataURL();
        link.click();
    }).catch(err => {
        console.error('Export failed:', err);
        alert('Export failed. Please check console for details.');
    });
}

// Error handling for missing dependencies
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    if (e.error.message.includes('html2canvas')) {
        console.log('html2canvas library not loaded - export functionality disabled');
    }
});