/**
 * Politician Graph Visualization
 * Adapted from OpenBallot demo.html for Flask integration
 */

class PoliticianGraph {
    constructor(containerId, politicianId) {
        this.containerId = containerId;
        this.politicianId = politicianId;
        this.svg = null;
        this.simulation = null;
        this.width = 0;
        this.height = 0;
        this.data = null;
        
        // D3 selections
        this.gAll = null;
        this.gBack = null;
        this.gLinks = null;
        this.gNodes = null;
        this.gLabels = null;
        
        this.init();
    }

    init() {
        this.setupSVG();
        this.setupDefs();
        this.resize();
        this.loadData();
        
        // Handle window resize
        window.addEventListener('resize', () => this.resize());
    }

    setupSVG() {
        const container = document.getElementById(this.containerId);
        this.svg = d3.select(container)
            .append('svg')
            .attr('class', 'w-100 h-100');
        
        this.gAll = this.svg.append('g');
        this.gBack = this.gAll.append('g');
        this.gLinks = this.gAll.append('g');
        this.gNodes = this.gAll.append('g');
        this.gLabels = this.gAll.append('g');
    }

    setupDefs() {
        const defs = this.svg.append('defs');
        
        // Soft glow filter
        defs.append('filter').attr('id', 'softGlow')
            .append('feDropShadow')
            .attr('dx', 0).attr('dy', 0)
            .attr('stdDeviation', 4)
            .attr('flood-color', '#2aa36b')
            .attr('flood-opacity', 0.35);
        
        // Arrow marker
        const marker = defs.append('marker')
            .attr('id', 'arrow')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 10)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto');
        
        marker.append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#6c757d');
    }

    resize() {
        const container = document.getElementById(this.containerId);
        const rect = container.getBoundingClientRect();
        this.width = rect.width;
        this.height = Math.max(400, rect.height);
        
        this.svg
            .attr('width', this.width)
            .attr('height', this.height);
        
        if (this.data) {
            this.draw();
        }
    }

    async loadData() {
        try {
            const response = await fetch(`/api/politician/${this.politicianId}/graph`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            this.data = await response.json();
            
            // Hide loading indicator and show graph
            const loadingEl = document.getElementById('graph-loading');
            const containerEl = document.getElementById(this.containerId);
            if (loadingEl) loadingEl.style.display = 'none';
            if (containerEl) containerEl.style.display = 'block';
            
            this.draw();
        } catch (error) {
            console.error('Failed to load graph data:', error);
            this.showError('Failed to load graph data');
        }
    }

    showError(message) {
        // Hide loading indicator
        const loadingEl = document.getElementById('graph-loading');
        if (loadingEl) loadingEl.style.display = 'none';
        
        // Show error in the graph container
        const container = document.getElementById(this.containerId);
        if (container) {
            container.style.display = 'block';
            container.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <i class="bi bi-exclamation-triangle"></i>
                    ${message}
                </div>
            `;
        }
    }

    draw() {
        if (!this.data || !this.data.nodes || !this.data.links) {
            return;
        }

        this.gAll.selectAll('*').remove();
        
        // Recreate groups
        this.gBack = this.gAll.append('g');
        this.gLinks = this.gAll.append('g');
        this.gNodes = this.gAll.append('g');
        this.gLabels = this.gAll.append('g');

        // Preprocess data with anchor positioning
        const processedData = this.preprocessData(this.data);
        const nodes = processedData.nodes;
        const links = processedData.links;

        // Create force simulation with fixed anchors
        this.simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(60))
            .force('charge', d3.forceManyBody().strength(-150))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(15))
            .force('x', d3.forceX(this.width / 2).strength(0.1))
            .force('y', d3.forceY(this.height / 2).strength(0.1));

        // Create links with thinner lines
        const link = this.gLinks.selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('stroke', '#7c8a92')
            .attr('stroke-opacity', 0.7)
            .attr('stroke-width', d => Math.max(1, Math.log10((d.amount || 1000) + 10)))
            .attr('marker-end', 'url(#arrow)');

        // Create nodes with initial positioning
        const node = this.gNodes.selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('r', d => this.getNodeRadius(d))
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.5)
            .attr('cx', d => d._tx || this.width / 2)
            .attr('cy', d => d._ty || this.height / 2)
            .style('cursor', 'pointer')
            .call(this.drag(this.simulation));

        // Add node labels with initial positioning
        const label = this.gLabels.selectAll('text')
            .data(nodes)
            .enter().append('text')
            .text(d => this.getNodeLabel(d))
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .attr('x', d => d._tx || this.width / 2)
            .attr('y', d => d._ty || this.height / 2)
            .style('font-size', '11px')
            .style('fill', '#ffffff')
            .style('font-weight', 'bold')
            .style('paint-order', 'stroke')
            .style('stroke', '#0a0c12')
            .style('stroke-width', '3px')
            .style('pointer-events', 'none');

        // Add corner labels for funding groups
        this.addCornerLabels(processedData._anchors);

        // Add tooltips
        node.append('title')
            .text(d => this.getTooltipText(d));

        // Update positions on simulation tick
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });

        // Add click handlers
        node.on('click', (event, d) => {
            this.onNodeClick(event, d);
        });

        // Add hover effects
        node.on('mouseover', (event, d) => {
            this.onNodeHover(event, d, true);
        }).on('mouseout', (event, d) => {
            this.onNodeHover(event, d, false);
        });
    }

    preprocessData(data) {
        const anchors = this.getAnchors();
        const byId = new Map(data.nodes.map(n => [n.id, n]));
        
        // Set fixed positions for funding groups
        ["grp_indiv", "grp_pac", "grp_party"].forEach(id => {
            const n = byId.get(id);
            if (n) {
                n.fx = anchors[id].x;
                n.fy = anchors[id].y;
            }
        });

        // Calculate funding amounts and positioning for politicians
        const amtByPol = new Map();
        for (const l of data.links) {
            if (l.type !== "donation") continue;
            const rec = amtByPol.get(l.target) || { indiv: 0, pac: 0, party: 0 };
            if (l.source === "grp_indiv") rec.indiv += +l.amount || 0;
            if (l.source === "grp_pac") rec.pac += +l.amount || 0;
            if (l.source === "grp_party") rec.party += +l.amount || 0;
            amtByPol.set(l.target, rec);
        }

        for (const n of data.nodes) {
            if (n.type !== "Politician") continue;
            const a = amtByPol.get(n.id) || { indiv: 0, pac: 0, party: 0 };
            const tot = a.indiv + a.pac + a.party;
            const sI = tot ? a.indiv / tot : 0;
            const sP = tot ? a.pac / tot : 0;
            const sY = tot ? a.party / tot : 0;
            const I = anchors.grp_indiv;
            const P = anchors.grp_pac;
            const Y = anchors.grp_party;
            
            // Position politician in the center area, weighted by funding sources
            const centerX = this.width / 2;
            const centerY = this.height / 2;
            
            // Calculate weighted position but keep it more centered
            const weightedX = sI * I.x + sP * P.x + sY * Y.x;
            const weightedY = sI * I.y + sP * P.y + sY * Y.y;
            
            // Start politician closer to center, blend with weighted position
            n._tx = centerX + (weightedX - centerX) * 0.3;
            n._ty = centerY + (weightedY - centerY) * 0.3;
            
            n._total = tot;
            n._sI = sI;
            n._sP = sP;
            n._sY = sY;
            n._dom = (sI >= sP && sI >= sY) ? "indiv" : (sP >= sI && sP >= sY) ? "pac" : "party";
        }

        data._amtByPol = amtByPol;
        data._anchors = anchors;
        return data;
    }

    getAnchors() {
        // Use more centered positioning for the politician-focused view
        const margin = 80; // Leave more margin from edges
        const centerY = this.height / 2;
        
        // Position funding groups more centrally within the visible area
        const leftX = margin;
        const rightX = this.width - margin;
        
        return {
            grp_indiv: { x: leftX, y: centerY },
            grp_pac: { x: rightX, y: centerY - 60 },
            grp_party: { x: rightX, y: centerY + 60 }
        };
    }

    addCornerLabels(anchors) {
        const cornerGroup = this.gLabels.append('g').attr('class', 'corner-labels');
        
        cornerGroup.append('text')
            .attr('class', 'cornerLabel')
            .attr('x', anchors.grp_indiv.x - 8)
            .attr('y', anchors.grp_indiv.y - 14)
            .attr('text-anchor', 'end')
            .style('fill', '#93a9ff')
            .style('font-size', '12px')
            .style('opacity', 0.9)
            .style('pointer-events', 'none')
            .text('Individuals');

        cornerGroup.append('text')
            .attr('class', 'cornerLabel')
            .attr('x', anchors.grp_pac.x + 8)
            .attr('y', anchors.grp_pac.y - 12)
            .attr('text-anchor', 'start')
            .style('fill', '#93a9ff')
            .style('font-size', '12px')
            .style('opacity', 0.9)
            .style('pointer-events', 'none')
            .text('PACs / Committees');

        cornerGroup.append('text')
            .attr('class', 'cornerLabel')
            .attr('x', anchors.grp_party.x + 8)
            .attr('y', anchors.grp_party.y + 16)
            .attr('text-anchor', 'start')
            .style('fill', '#93a9ff')
            .style('font-size', '12px')
            .style('opacity', 0.9)
            .style('pointer-events', 'none')
            .text('Party Committees');
    }

    getNodeRadius(d) {
        if (d.type === 'FundingGroup') {
            return 18;
        } else if (d.type === 'Politician') {
            const t = d._total || 0;
            return Math.max(4, Math.min(11, 4 + Math.log10(t + 10)));
        }
        return 8;
    }

    getNodeColor(d) {
        if (d.type === 'FundingGroup') {
            return '#2aa36b'; // Same green for all funding groups
        } else if (d.type === 'Politician') {
            const colors = {
                indiv: '#6ee7b7',
                pac: '#60a5fa',
                party: '#a78bfa'
            };
            return colors[d._dom] || '#e74c3c';
        }
        return '#6c757d';
    }

    getNodeLabel(d) {
        if (d.type === 'FundingGroup') {
            return d.name.split(' ')[0]; // First word only for funding groups
        } else if (d.type === 'Politician') {
            const name = d.name || 'Unknown';
            const parts = name.split(', ');
            if (parts.length >= 2) {
                return parts[1].split(' ')[0]; // First name only
            }
            return name.split(' ')[0];
        }
        return d.name || d.id;
    }

    getTooltipText(d) {
        if (d.type === 'FundingGroup') {
            return `${d.name}\nType: ${d.type}`;
        } else if (d.type === 'Politician') {
            const lines = [d.name || 'Unknown Politician'];
            if (d.state) lines.push(`State: ${d.state}`);
            if (d.party) lines.push(`Party: ${d.party}`);
            if (d._total) lines.push(`Total: $${d._total.toLocaleString()}`);
            if (d._sI !== undefined) {
                lines.push(`Individual: ${(d._sI * 100).toFixed(1)}%`);
                lines.push(`PAC: ${(d._sP * 100).toFixed(1)}%`);
                lines.push(`Party: ${(d._sY * 100).toFixed(1)}%`);
            }
            return lines.join('\n');
        }
        return `${d.name || d.id}\nType: ${d.type}`;
    }

    onNodeClick(event, d) {
        // Highlight the clicked node
        this.gNodes.selectAll('circle')
            .attr('stroke-width', 2);
        
        d3.select(event.currentTarget)
            .attr('stroke-width', 4)
            .attr('stroke', '#ffc107');
    }

    onNodeHover(event, d, isHover) {
        if (isHover) {
            d3.select(event.currentTarget)
                .attr('stroke-width', 3)
                .attr('stroke', '#17a2b8');
        } else {
            d3.select(event.currentTarget)
                .attr('stroke-width', 2)
                .attr('stroke', '#fff');
        }
    }

    drag(simulation) {
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended);
    }
}

// Initialize graph when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a politician page and if D3 is loaded
    if (window.d3 && document.getElementById('politician-graph-container')) {
        const politicianId = document.getElementById('politician-graph-container').dataset.politicianId;
        if (politicianId) {
            new PoliticianGraph('politician-graph-container', politicianId);
        }
    }
});
