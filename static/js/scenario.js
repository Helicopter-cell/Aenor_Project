(() => {
    const EXPAND_BY_DEFAULT = false;
    const outlineMarkdown = {{ outline_markdown|tojson }};
    const mindmapElement = document.getElementById('obsidian-mindmap');

    if (mindmapElement) {
        const rootNode = { id: 'mindmap-root', label: 'Coffre Obsidian', depth: 0, children: [], leafCount: 1 };
        const treeNodes = new Map([[rootNode.id, rootNode]]);
        const stack = [rootNode];
        let treeNodeNumber = 0;

        outlineMarkdown.split('\n').forEach((line, lineIndex) => {
            if (lineIndex === 0 && line.startsWith('# ')) {
                rootNode.label = line.slice(2).trim();
                return;
            }
            const item = line.match(/^(\s*)-\s+(.+)$/);
            if (!item) return;
            const depth = Math.floor(item[1].length / 2) + 1;
            const parent = stack[depth - 1] || rootNode;
            const node = {
                id: `mindmap-${++treeNodeNumber}`,
                label: item[2].trim(),
                depth,
                parentId: parent.id,
                children: [],
                leafCount: 1,
            };
            parent.children.push(node);
            treeNodes.set(node.id, node);
            stack.length = depth;
            stack[depth] = node;
        });

        const expandedNodes = new Set([rootNode.id]);
        if (EXPAND_BY_DEFAULT) {
            treeNodes.forEach((node) => {
                if (node.children.length) expandedNodes.add(node.id);
            });
        }

        function estimateNodeHeight(node) {
            const fontSize = node.depth < 2 ? 17 : 14;
            const width = node.depth === 0 ? 220 : 280;
            const charactersPerLine = Math.max(12, Math.floor(width / (fontSize * 0.58)));
            return Math.max(48, Math.ceil(node.label.length / charactersPerLine) * fontSize * 1.5 + 24);
        }

        function visibleSpan(node) {
            if (!node.children.length || !expandedNodes.has(node.id)) return estimateNodeHeight(node);
            const siblingGap = 20 + Math.min(node.depth * 3, 16);
            return node.children.reduce((total, child) => total + visibleSpan(child), 0)
                + siblingGap * (node.children.length - 1);
        }

        function positionTree() {
            const horizontalSpacing = 250;
            const rootSpacing = 500;
            const positions = new Map([[rootNode.id, { x: 0, y: 0 }]]);
            rootNode.x = 0;
            rootNode.y = 0;
            let cursorY = -visibleSpan(rootNode) / 2;

            function placeVisibleChildren(parent, top, side) {
                if (!expandedNodes.has(parent.id)) return;
                let childTop = top;
                const siblingGap = 20 + Math.min(parent.depth * 3, 16);
                parent.children.forEach((child, index) => {
                    const childSide = parent.depth <= 1
                        ? (index % 2 === 0 ? 1 : -1)
                        : side;
                    const height = visibleSpan(child);
                    const position = {
                        x: parent.x + childSide * (horizontalSpacing + Math.min(child.depth * 18, 90)),
                        y: childTop + height / 2,
                    };
                    child.x = position.x;
                    child.y = position.y;
                    positions.set(child.id, position);
                    placeVisibleChildren(child, childTop, childSide);
                    childTop += height + siblingGap;
                });
            }

            rootNode.children.forEach((child, index) => {
                const side = index % 2 === 0 ? 1 : -1;
                const height = visibleSpan(child);
                const position = { x: side * rootSpacing, y: cursorY + height / 2 };
                child.x = position.x;
                child.y = position.y;
                positions.set(child.id, position);
                placeVisibleChildren(child, cursorY, side);
                cursorY += height + 28;
            });
            return positions;
        }

        const initialPositions = positionTree();

        function isInitiallyVisible(node) {
            if (node === rootNode) return true;
            const parent = treeNodes.get(node.parentId);
            return Boolean(parent && expandedNodes.has(parent.id) && isInitiallyVisible(parent));
        }

        function collectVisibleNodeIds() {
            const visible = new Set();
            function visit(node) {
                visible.add(node.id);
                if (expandedNodes.has(node.id)) node.children.forEach(visit);
            }
            visit(rootNode);
            return visible;
        }

        let visibleNodeIds = collectVisibleNodeIds();
        let visibleEdgeIds = new Set();
        treeNodes.forEach((node) => {
            node.children.forEach((child) => {
                if (visibleNodeIds.has(node.id) && visibleNodeIds.has(child.id)) {
                    visibleEdgeIds.add(`mindmap-edge-${child.id}`);
                }
            });
        });

        const mindmapNodeItems = Array.from(treeNodes.values(), (node) => ({
            id: node.id,
            label: node.children.length
                ? `${node.label}  ${expandedNodes.has(node.id) ? '-' : '+'}`
                : node.label,
            x: initialPositions.get(node.id)?.x ?? 0,
            y: initialPositions.get(node.id)?.y ?? 0,
            fixed: { x: true, y: true },
            hidden: !isInitiallyVisible(node),
            shape: 'box',
            margin: 12,
            widthConstraint: { maximum: node.depth === 0 ? 220 : 280 },
            borderWidth: 1.5,
            color: {
                background: node.depth === 0 ? '#35584e' : node.depth === 1 ? '#557868' : '#314840',
                border: node.depth === 0 ? '#e3c478' : '#a9c5a2',
                highlight: { background: '#456d5e', border: '#f0d58c' },
                hover: { background: '#456d5e', border: '#e3c478' },
            },
            font: { color: '#fff8e8', face: 'Georgia', size: node.depth < 2 ? 17 : 14 },
            chosen: { node: false, label: false },
        }));
        const mindmapEdgeItems = [];
        treeNodes.forEach((node) => {
            node.children.forEach((child) => mindmapEdgeItems.push({
                id: `mindmap-edge-${child.id}`,
                from: node.id,
                to: child.id,
                hidden: !visibleNodeIds.has(child.id),
                color: { color: 'rgba(207, 195, 152, 0.55)' },
                smooth: { type: 'cubicBezier', forceDirection: 'horizontal', roundness: 0.4 },
            }));
        });

        const mindmapNodes = new vis.DataSet(mindmapNodeItems);
        const mindmapEdges = new vis.DataSet(mindmapEdgeItems);
        const mindmapNetwork = new vis.Network(mindmapElement, {
            nodes: mindmapNodes,
            edges: mindmapEdges,
        }, {
            autoResize: true,
            nodes: { shape: 'box', margin: 12, shapeProperties: { borderRadius: 6 } },
            edges: {
                arrows: { to: { enabled: false } },
                smooth: { type: 'cubicBezier', forceDirection: 'horizontal', roundness: 0.4 },
                color: { color: 'rgba(207, 195, 152, 0.55)' },
            },
            interaction: { hover: true, zoomView: true, dragView: true, dragNodes: false },
            physics: { enabled: false },
        });

        requestAnimationFrame(() => mindmapNetwork.fit({ animation: false }));

        function updateVisibleTree(changedNodeId) {
            const positions = positionTree();
            const nextVisibleNodeIds = collectVisibleNodeIds();
            const nodeUpdates = [];
            const nextVisibleEdgeIds = new Set();
            const edgeUpdates = [];

            treeNodes.forEach((node) => {
                const wasVisible = visibleNodeIds.has(node.id);
                const isVisible = nextVisibleNodeIds.has(node.id);
                const position = positions.get(node.id);
                const oldPosition = initialPositions.get(node.id);
                const moved = isVisible && position && (!oldPosition
                    || Math.abs(position.x - oldPosition.x) > 0.5
                    || Math.abs(position.y - oldPosition.y) > 0.5);
                if (wasVisible === isVisible && !moved && node.id !== changedNodeId) return;

                const update = { id: node.id, hidden: !isVisible };
                if (isVisible && position) Object.assign(update, position);
                if (node.children.length) {
                    update.label = `${node.label}  ${expandedNodes.has(node.id) ? '-' : '+'}`;
                }
                nodeUpdates.push(update);

                node.children.forEach((child) => {
                    const edgeId = `mindmap-edge-${child.id}`;
                    const edgeVisible = isVisible && nextVisibleNodeIds.has(child.id);
                    if (edgeVisible) nextVisibleEdgeIds.add(edgeId);
                    if (visibleEdgeIds.has(edgeId) !== edgeVisible) {
                        edgeUpdates.push({ id: edgeId, hidden: !edgeVisible });
                    }
                });
            });

            mindmapNodes.update(nodeUpdates);
            mindmapEdges.update(edgeUpdates);
            initialPositions.clear();
            positions.forEach((position, id) => initialPositions.set(id, position));
            visibleNodeIds = nextVisibleNodeIds;
            visibleEdgeIds = nextVisibleEdgeIds;
            mindmapNetwork.fit({ animation: { duration: 350, easingFunction: 'easeInOutQuad' } });
        }

        mindmapNetwork.on('click', ({ nodes: selectedNodes }) => {
            if (!selectedNodes.length) return;
            const selectedNode = treeNodes.get(selectedNodes[0]);
            if (!selectedNode || !selectedNode.children.length) return;
            if (expandedNodes.has(selectedNode.id)) expandedNodes.delete(selectedNode.id);
            else expandedNodes.add(selectedNode.id);
            updateVisibleTree(selectedNode.id);
        });

        mindmapNetwork.on('zoom', ({ scale }) => {
            const boundedScale = Math.min(2.0, Math.max(0.3, scale));
            if (boundedScale !== scale) mindmapNetwork.moveTo({ scale: boundedScale });
        });

        mindmapNetwork.on('dragEnd', () => {
            const view = mindmapNetwork.getViewPosition();
            const positions = mindmapNetwork.getPositions(Array.from(visibleNodeIds));
            const visiblePositions = Object.values(positions);
            if (!visiblePositions.length) return;
            const center = visiblePositions.reduce((total, position) => ({
                x: total.x + position.x / visiblePositions.length,
                y: total.y + position.y / visiblePositions.length,
            }), { x: 0, y: 0 });
            const graphRadius = visiblePositions.reduce((radius, position) => Math.max(
                radius,
                Math.hypot(position.x - center.x, position.y - center.y),
            ), 0);
            const maxRadius = graphRadius + 300;
            if (Math.hypot(view.x - center.x, view.y - center.y) > maxRadius) {
                mindmapNetwork.moveTo({
                    position: center,
                    animation: { duration: 400, easingFunction: 'easeInOutQuad' },
                });
            }
        });

        document.getElementById('mindmap-fit').addEventListener('click', () => {
            mindmapNetwork.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
        });
    }

    const graphData = {{ graph_data|tojson }};
    const graphElement = document.getElementById('scenario-network');
    const previewPlaceholder = document.getElementById('preview-placeholder');
    const notePreview = document.getElementById('note-preview');
    const previewTitle = document.getElementById('preview-title');
    const previewSummary = document.getElementById('preview-summary');
    const previewContent = document.getElementById('preview-content');
    const minZoom = 0.2;
    const maxZoom = 2.5;
    const degreeByNode = new Map(graphData.nodes.map((node) => [node.id, 0]));
    graphData.edges.forEach((edge) => {
        degreeByNode.set(edge.from, (degreeByNode.get(edge.from) || 0) + 1);
        degreeByNode.set(edge.to, (degreeByNode.get(edge.to) || 0) + 1);
    });
    const maxDegree = Math.max(1, ...degreeByNode.values());
    const nodePalette = [
        { background: '#92b9c6', border: '#c9e0e5' },
        { background: '#80b89e', border: '#c1dfbd' },
        { background: '#d0bb70', border: '#f1dfa0' },
        { background: '#dc9166', border: '#f4c59b' },
        { background: '#d86e76', border: '#f0a7a0' },
    ];
    const originalNodes = graphData.nodes.map((node) => ({
        id: node.id,
        label: node.title,
        title: node.summary,
        shape: 'dot',
        size: 18,
        borderWidth: 2,
        color: nodePalette[Math.min(nodePalette.length - 1, Math.floor((degreeByNode.get(node.id) / maxDegree) * nodePalette.length))],
        font: { color: '#fff8e8', size: 15, face: 'Georgia' },
    }));
    const nodes = new vis.DataSet(originalNodes);
    const edges = new vis.DataSet(graphData.edges.map((edge) => ({
        ...edge,
    })));
    const network = new vis.Network(graphElement, { nodes, edges }, {
        autoResize: true,
        nodes: { chosen: true },
        edges: {
            arrows: { to: { enabled: false } },
            color: { inherit: 'both' },
            scaling: { min: 1, max: 6 },
            smooth: { type: 'continuous' },
            selectionWidth: 2,
            hoverWidth: 1.5,
        },
        interaction: {
            hover: true,
            hoverConnectedEdges: true,
            zoomView: true,
            dragView: true,
            dragNodes: true,
            navigationButtons: false,
        },
        physics: {
            stabilization: { iterations: 180, fit: true },
            barnesHut: { gravitationalConstant: -3800, springLength: 125, springConstant: 0.035 },
        },
    });

    network.on('zoom', ({ scale }) => {
        const boundedScale = Math.min(maxZoom, Math.max(minZoom, scale));
        if (boundedScale !== scale) network.moveTo({ scale: boundedScale });
    });

    function constrainView() {
        if (!graphData.nodes.length) return;
        const positions = Object.values(network.getPositions());
        if (!positions.length) return;

        const bounds = positions.reduce((result, position) => ({
            minX: Math.min(result.minX, position.x),
            maxX: Math.max(result.maxX, position.x),
            minY: Math.min(result.minY, position.y),
            maxY: Math.max(result.maxY, position.y),
        }), {
            minX: Infinity,
            maxX: -Infinity,
            minY: Infinity,
            maxY: -Infinity,
        });
        const scale = network.getScale();
        const padding = 120 + Math.sqrt(graphData.nodes.length) * 18;
        const halfWidth = graphElement.clientWidth / (2 * scale);
        const halfHeight = graphElement.clientHeight / (2 * scale);
        const view = network.getViewPosition();
        const boundedPosition = {
            x: Math.min(bounds.maxX + padding + halfWidth, Math.max(bounds.minX - padding - halfWidth, view.x)),
            y: Math.min(bounds.maxY + padding + halfHeight, Math.max(bounds.minY - padding - halfHeight, view.y)),
        };

        if (boundedPosition.x !== view.x || boundedPosition.y !== view.y) {
            network.moveTo({ position: boundedPosition, scale, animation: { duration: 280 } });
        }
    }

    network.on('dragEnd', constrainView);

    function setHighlight(nodeId) {
        const linkedEdges = new Set(nodeId === null ? [] : network.getConnectedEdges(nodeId));
        const linkedNodes = new Set(nodeId === null ? [] : network.getConnectedNodes(nodeId));
        if (nodeId !== null) linkedNodes.add(nodeId);
        nodes.update(originalNodes.map((node) => {
            if (nodeId === null || linkedNodes.has(node.id)) return node;
            return { id: node.id, color: { background: 'rgba(91, 105, 82, 0.42)', border: 'rgba(180, 179, 151, 0.35)' }, font: { color: 'rgba(255, 248, 232, 0.38)' } };
        }));
        edges.update(graphData.edges.map((edge) => ({
            id: edge.id,
            color: nodeId === null || linkedEdges.has(edge.id)
                ? { inherit: 'both' }
                : { color: 'rgba(150, 150, 130, 0.12)', inherit: false },
        })));
    }

    function showPreview(nodeId) {
        const node = graphData.nodes.find((candidate) => candidate.id === nodeId);
        if (!node) return;
        previewTitle.textContent = node.title;
        previewSummary.textContent = node.summary;
        previewContent.innerHTML = node.content_html;
        previewPlaceholder.hidden = true;
        notePreview.hidden = false;
        setHighlight(nodeId);
    }

    function clearPreview() {
        previewPlaceholder.hidden = false;
        notePreview.hidden = true;
        setHighlight(null);
    }

    network.on('hoverNode', ({ node }) => showPreview(node));
    network.on('blurNode', () => {
        const selected = network.getSelectedNodes();
        if (selected.length) showPreview(selected[0]);
        else clearPreview();
    });
    network.on('click', ({ nodes: selected }) => {
        if (selected.length) showPreview(selected[0]);
        else clearPreview();
    });
    previewContent.addEventListener('click', (event) => {
        const link = event.target.closest('a[href^="#vault-"]');
        if (!link) return;
        event.preventDefault();
        const nodeId = decodeURIComponent(link.getAttribute('href').slice('#vault-'.length));
        network.selectNodes([nodeId]);
        network.focus(nodeId, { scale: 1.15, animation: { duration: 350 } });
        showPreview(nodeId);
    });

    document.getElementById('zoom-in').addEventListener('click', () => network.moveTo({ scale: Math.min(maxZoom, network.getScale() * 1.2) }));
    document.getElementById('zoom-out').addEventListener('click', () => network.moveTo({ scale: Math.max(minZoom, network.getScale() / 1.2) }));
    document.getElementById('fit-graph').addEventListener('click', () => network.fit({ animation: { duration: 400 } }));
})();