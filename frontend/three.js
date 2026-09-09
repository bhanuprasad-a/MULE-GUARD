(function() {
  let initialized = false;
  let retries = 0;
  const MAX_RETRIES = 120; // Retry for up to 2 seconds at 60fps

  function initVisualizer(container, width, height) {
    if (initialized) return;
    initialized = true;

    // Scene Setup
    const scene = new THREE.Scene();

    // Perspective Camera
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(0, 0, 11);

    // WebGL Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    
    // Clear container to prevent duplicate canvas rendering
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Color System Constants
    const COLOR_NAVY = 0x0B1F3A;
    const COLOR_COBALT = 0x2563EB;
    const COLOR_CYAN = 0x38BDF8;
    const COLOR_RISK = 0xEF4444; // Red/orange suspicious accent
    const COLOR_WHITE = 0xFFFFFF;

    // Reduced Motion Detection
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    let reducedMotion = motionQuery.matches;
    motionQuery.addEventListener('change', (e) => {
      reducedMotion = e.matches;
    });

    // Lights Setup
    const ambientLight = new THREE.AmbientLight(0x0e2544, 1.8);
    scene.add(ambientLight);

    const mainLight = new THREE.DirectionalLight(0x38BDF8, 1.5);
    mainLight.position.set(5, 8, 5);
    scene.add(mainLight);

    const glowLight = new THREE.PointLight(0x2563EB, 3, 12);
    glowLight.position.set(-1.0, 0, 0);
    scene.add(glowLight);

    // Group containing the entire network
    const networkGroup = new THREE.Group();
    scene.add(networkGroup);

    // Reusable Geometries
    const geoSphere = new THREE.SphereGeometry(1, 24, 24);
    const geoParticle = new THREE.SphereGeometry(0.045, 8, 8);
    const geoCentralOuter = new THREE.IcosahedronGeometry(0.85, 2);

    // Graph Arrays
    const nodes = [];
    const connections = [];
    const particles = [];

    // 1. Central Account Node (Level 0)
    const centralNode = {
      id: 0,
      level: 0,
      size: 0.65,
      pos: new THREE.Vector3(-1.0, 0, 0),
      basePos: new THREE.Vector3(-1.0, 0, 0),
      mesh: new THREE.Group(),
      isSuspicious: false
    };
    centralNode.mesh.position.copy(centralNode.pos);

    // Central Core Mesh
    const coreMat = new THREE.MeshStandardMaterial({
      color: COLOR_COBALT,
      emissive: 0x081a33,
      roughness: 0.1,
      metalness: 0.8,
      transparent: true,
      opacity: 0.95
    });
    const coreMesh = new THREE.Mesh(geoSphere, coreMat);
    coreMesh.scale.setScalar(centralNode.size);
    centralNode.mesh.add(coreMesh);

    // Central Wireframe Shell
    const outerMat = new THREE.MeshBasicMaterial({
      color: COLOR_CYAN,
      wireframe: true,
      transparent: true,
      opacity: 0.22
    });
    const outerShell = new THREE.Mesh(geoCentralOuter, outerMat);
    centralNode.mesh.add(outerShell);
    centralNode.outerShell = outerShell;

    networkGroup.add(centralNode.mesh);
    nodes.push(centralNode);

    // 2. Intermediate Nodes (Level 1)
    const numIntermediates = 6;
    const intermediateDist = 3.2;

    // Designate Branch 2 as Suspicious (red/orange)
    for (let i = 0; i < numIntermediates; i++) {
      const isSusp = (i === 2);
      
      // Spread in 3D sphere around central node
      const theta = (i / numIntermediates) * Math.PI * 2 + 0.3;
      const phi = (Math.random() - 0.5) * 0.8;
      const pos = new THREE.Vector3(
        centralNode.basePos.x + Math.cos(theta) * Math.cos(phi) * intermediateDist,
        centralNode.basePos.y + Math.sin(theta) * Math.cos(phi) * intermediateDist,
        centralNode.basePos.z + Math.sin(phi) * intermediateDist
      );

      const size = 0.26 + Math.random() * 0.08;
      const mat = new THREE.MeshStandardMaterial({
        color: isSusp ? COLOR_RISK : COLOR_CYAN,
        emissive: isSusp ? 0x220505 : 0x071e35,
        roughness: 0.2,
        metalness: 0.6,
        transparent: true,
        opacity: 0.85
      });

      const mesh = new THREE.Mesh(geoSphere, mat);
      mesh.scale.setScalar(size);
      mesh.position.copy(pos);
      networkGroup.add(mesh);

      nodes.push({
        id: nodes.length,
        level: 1,
        size,
        pos: pos.clone(),
        basePos: pos.clone(),
        mesh,
        material: mat,
        isSuspicious: isSusp,
        driftSpeed: 0.35 + Math.random() * 0.45,
        driftPhase: Math.random() * Math.PI * 2,
        pulseSpeed: 1.0 + Math.random() * 1.5,
        pulsePhase: Math.random() * Math.PI * 2
      });
    }

    // 3. Counterparty Leaf Nodes (Level 2)
    const childrenPerIntermediate = 3;
    const leafDist = 1.6;

    nodes.filter(n => n.level === 1).forEach((parent) => {
      for (let j = 0; j < childrenPerIntermediate; j++) {
        const isSusp = parent.isSuspicious && (j < 2);

        const angle = (j / childrenPerIntermediate) * Math.PI * 2 + (Math.random() - 0.5) * 0.5;
        const xOffset = Math.cos(angle) * leafDist;
        const yOffset = Math.sin(angle) * leafDist;
        const zOffset = (Math.random() - 0.5) * 1.2;

        const pos = new THREE.Vector3(
          parent.basePos.x + xOffset,
          parent.basePos.y + yOffset,
          parent.basePos.z + zOffset
        );

        const size = 0.12 + Math.random() * 0.05;
        const mat = new THREE.MeshStandardMaterial({
          color: isSusp ? COLOR_RISK : (Math.random() > 0.4 ? COLOR_CYAN : COLOR_COBALT),
          emissive: isSusp ? 0x220505 : 0x041324,
          roughness: 0.3,
          metalness: 0.5,
          transparent: true,
          opacity: 0.8
        });

        const mesh = new THREE.Mesh(geoSphere, mat);
        mesh.scale.setScalar(size);
        mesh.position.copy(pos);
        networkGroup.add(mesh);

        nodes.push({
          id: nodes.length,
          level: 2,
          parentId: parent.id,
          size,
          pos: pos.clone(),
          basePos: pos.clone(),
          mesh,
          material: mat,
          isSuspicious: isSusp,
          driftSpeed: 0.4 + Math.random() * 0.6,
          driftPhase: Math.random() * Math.PI * 2,
          pulseSpeed: 1.2 + Math.random() * 1.8,
          pulsePhase: Math.random() * Math.PI * 2
        });
      }
    });

    // Curve Generation Helper
    function createBezierCurve(pA, pB, connId) {
      const dir = new THREE.Vector3().subVectors(pB, pA);
      const length = dir.length();
      const up = new THREE.Vector3(0, 1, 0);
      if (Math.abs(dir.dot(up)) > 0.95 * length) {
        up.set(1, 0, 0);
      }
      const perp = new THREE.Vector3().crossVectors(dir, up).normalize();
      const seedOffset = (connId * 1.9) % 0.3 - 0.15;
      const pControl = new THREE.Vector3()
        .addVectors(pA, pB)
        .multiplyScalar(0.5)
        .addScaledVector(perp, length * 0.16 + seedOffset);

      return new THREE.QuadraticBezierCurve3(pA, pControl, pB);
    }

    // 4. Set up connections between nodes
    let connectionCounter = 0;

    // Level 0 -> Level 1
    nodes.filter(n => n.level === 1).forEach(node => {
      const isSusp = node.isSuspicious;
      const curve = createBezierCurve(centralNode.pos, node.pos, connectionCounter);
      const points = curve.getPoints(16);
      const geometry = new THREE.BufferGeometry().setFromPoints(points);

      const lineMat = new THREE.LineBasicMaterial({
        color: isSusp ? COLOR_RISK : COLOR_CYAN,
        transparent: true,
        opacity: isSusp ? 0.65 : 0.22,
        blending: THREE.AdditiveBlending
      });

      const line = new THREE.Line(geometry, lineMat);
      networkGroup.add(line);

      connections.push({
        id: connectionCounter++,
        nodeA: centralNode,
        nodeB: node,
        curve,
        geometry,
        line,
        isSuspicious: isSusp
      });
    });

    // Level 1 -> Level 2
    nodes.filter(n => n.level === 2).forEach(node => {
      const parentNode = nodes.find(parent => parent.id === node.parentId);
      const isSusp = node.isSuspicious && parentNode.isSuspicious;
      const curve = createBezierCurve(parentNode.pos, node.pos, connectionCounter);
      const points = curve.getPoints(16);
      const geometry = new THREE.BufferGeometry().setFromPoints(points);

      const lineMat = new THREE.LineBasicMaterial({
        color: isSusp ? COLOR_RISK : COLOR_COBALT,
        transparent: true,
        opacity: isSusp ? 0.55 : 0.15,
        blending: THREE.AdditiveBlending
      });

      const line = new THREE.Line(geometry, lineMat);
      networkGroup.add(line);

      connections.push({
        id: connectionCounter++,
        nodeA: parentNode,
        nodeB: node,
        curve,
        geometry,
        line,
        isSuspicious: isSusp
      });
    });

    // Extra Cross-Connections for mesh/network realism
    const crossConnections = [
      { fromId: 2, toId: 4 },
      { fromId: 8, toId: 11 }
    ];

    crossConnections.forEach(connData => {
      const nodeA = nodes.find(n => n.id === connData.fromId);
      const nodeB = nodes.find(n => n.id === connData.toId);
      if (nodeA && nodeB) {
        const isSusp = nodeA.isSuspicious && nodeB.isSuspicious;
        const curve = createBezierCurve(nodeA.pos, nodeB.pos, connectionCounter);
        const points = curve.getPoints(16);
        const geometry = new THREE.BufferGeometry().setFromPoints(points);

        const lineMat = new THREE.LineBasicMaterial({
          color: isSusp ? COLOR_RISK : COLOR_COBALT,
          transparent: true,
          opacity: isSusp ? 0.45 : 0.12,
          blending: THREE.AdditiveBlending
        });

        const line = new THREE.Line(geometry, lineMat);
        networkGroup.add(line);

        connections.push({
          id: connectionCounter++,
          nodeA,
          nodeB,
          curve,
          geometry,
          line,
          isSuspicious: isSusp
        });
      }
    });

    // 5. Initialize Moving Transaction Particles
    const numParticles = 24;
    const routes = [
      [8, 1, 0, 2, 10],   // Suspicious chain route (8 -> parent 1 -> center -> parent 2 -> leaf 10)
      [10, 2, 0, 3, 14],  // Partially suspicious route (leaf 10 -> parent 2 -> center -> parent 3 -> leaf 14)
      [12, 2, 0, 5, 20],  // Safe transaction chain (leaf 12 -> parent 2 -> center -> parent 5 -> leaf 20)
      [17, 4, 0, 6, 23],  // Safe transaction chain (leaf 17 -> parent 4 -> center -> parent 6 -> leaf 23)
      [24, 6, 0, 1, 9]    // Safe to suspicious route (leaf 24 -> parent 6 -> center -> parent 1 -> leaf 9)
    ];

    for (let i = 0; i < numParticles; i++) {
      const routeIndex = i % (routes.length + 3);
      let route = null;
      let isSuspicious = false;

      if (routeIndex < routes.length) {
        route = routes[routeIndex];
        isSuspicious = route.includes(2);
      } else {
        const conn = connections[Math.floor(Math.random() * connections.length)];
        isSuspicious = conn.isSuspicious;
      }

      const pMat = new THREE.MeshBasicMaterial({
        color: isSuspicious ? COLOR_RISK : 0xFFFFFF,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending
      });

      const pMesh = new THREE.Mesh(geoParticle, pMat);
      networkGroup.add(pMesh);

      let currentConn = null;
      let routeIndexInChain = 0;
      let direction = 1;

      if (route) {
        const fromNodeId = route[0];
        const toNodeId = route[1];
        currentConn = connections.find(c => 
          (c.nodeA.id === fromNodeId && c.nodeB.id === toNodeId) || 
          (c.nodeA.id === toNodeId && c.nodeB.id === fromNodeId)
        );
        if (currentConn) {
          direction = currentConn.nodeA.id === fromNodeId ? 1 : -1;
        } else {
          // Fallback if route connection fails
          route = null;
          currentConn = connections[Math.floor(Math.random() * connections.length)];
          direction = Math.random() > 0.5 ? 1 : -1;
        }
      } else {
        currentConn = connections[Math.floor(Math.random() * connections.length)];
        direction = Math.random() > 0.5 ? 1 : -1;
      }

      particles.push({
        mesh: pMesh,
        route,
        routeIndexInChain,
        currentConnection: currentConn,
        direction,
        t: Math.random(),
        speed: 0.0025 + Math.random() * 0.004,
        isSuspicious
      });
    }

    // Pre-allocated variables to avoid GC thrashing/lag
    const tempDir = new THREE.Vector3();
    const tempUp = new THREE.Vector3(0, 1, 0);
    const tempPerp = new THREE.Vector3();
    const tempControl = new THREE.Vector3();
    const curvePoints = [];
    for (let i = 0; i <= 16; i++) {
      curvePoints.push(new THREE.Vector3());
    }

    // Clock & Control variables
    const clock = new THREE.Clock();
    let animationFrameId = null;
    let isLooping = true;

    // Animation Frame Loop
    function animate() {
      if (!isLooping) return;
      animationFrameId = requestAnimationFrame(animate);

      const elapsed = clock.getElapsedTime();

      // Camera Cinematic Orbit
      if (!reducedMotion) {
        const cameraAngle = Math.sin(elapsed * 0.02) * 0.08;
        camera.position.x = Math.sin(cameraAngle) * 11.5;
        camera.position.z = Math.cos(cameraAngle) * 11.5;
        camera.position.y = Math.cos(elapsed * 0.015) * 0.25;
        camera.lookAt(new THREE.Vector3(-1.0, 0, 0));
      } else {
        camera.position.set(0, 0, 11);
        camera.lookAt(new THREE.Vector3(-1.0, 0, 0));
      }

      // Node drift and scale pulse animation
      nodes.forEach(node => {
        if (node.level === 0) {
          if (!reducedMotion) {
            const centralScale = 1.0 + Math.sin(elapsed * 1.0) * 0.035;
            node.mesh.scale.setScalar(centralScale);
            node.outerShell.rotation.y = elapsed * 0.06;
            node.outerShell.rotation.x = elapsed * 0.03;
          } else {
            node.mesh.scale.setScalar(1.0);
          }
        } else {
          if (!reducedMotion) {
            const driftX = Math.sin(elapsed * node.driftSpeed + node.driftPhase) * 0.1;
            const driftY = Math.cos(elapsed * node.driftSpeed * 0.85 + node.driftPhase) * 0.1;
            const driftZ = Math.sin(elapsed * node.driftSpeed * 0.6 + node.driftPhase) * 0.1;
            tempDir.set(driftX, driftY, driftZ);
            node.pos.copy(node.basePos).add(tempDir);
          } else {
            node.pos.copy(node.basePos);
          }
          node.mesh.position.copy(node.pos);

          // Slow glow pulsing
          if (!reducedMotion && node.material.emissive) {
            node.material.emissiveIntensity = 0.2 + Math.sin(elapsed * node.pulseSpeed + node.pulsePhase) * 0.12;
          }
        }
      });

      // Update connection lines to follow drifting nodes
      connections.forEach(conn => {
        const pA = conn.nodeA.pos;
        const pB = conn.nodeB.pos;
        
        tempDir.subVectors(pB, pA);
        const length = tempDir.length();
        tempUp.set(0, 1, 0);
        if (Math.abs(tempDir.dot(tempUp)) > 0.95 * length) {
          tempUp.set(1, 0, 0);
        }
        tempPerp.crossVectors(tempDir, tempUp).normalize();
        
        const seedOffset = (conn.id * 1.9) % 0.3 - 0.15;
        tempControl
          .addVectors(pA, pB)
          .multiplyScalar(0.5)
          .addScaledVector(tempPerp, length * 0.16 + seedOffset);
        
        conn.curve.v0.copy(pA);
        conn.curve.v1.copy(tempControl);
        conn.curve.v2.copy(pB);
        
        // Update points in place to avoid creating new Vector3 objects
        for (let i = 0; i <= 16; i++) {
          conn.curve.getPoint(i / 16, curvePoints[i]);
        }
        conn.geometry.setFromPoints(curvePoints);
      });

      // Animate transaction particles
      const speedScale = reducedMotion ? 0.05 : 1.0;
      particles.forEach(p => {
        p.t += p.speed * speedScale;
        
        if (p.t >= 1.0) {
          p.t = 0.0;

          if (p.route) {
            p.routeIndexInChain++;
            if (p.routeIndexInChain >= p.route.length - 1) {
              p.routeIndexInChain = 0;
            }
            
            const fromNodeId = p.route[p.routeIndexInChain];
            const toNodeId = p.route[p.routeIndexInChain + 1];

            const nextConn = connections.find(c => 
              (c.nodeA.id === fromNodeId && c.nodeB.id === toNodeId) || 
              (c.nodeA.id === toNodeId && c.nodeB.id === fromNodeId)
            );
            
            if (nextConn) {
              p.currentConnection = nextConn;
              p.direction = nextConn.nodeA.id === fromNodeId ? 1 : -1;
            } else {
              p.route = null;
              p.currentConnection = connections[Math.floor(Math.random() * connections.length)];
              p.direction = Math.random() > 0.5 ? 1 : -1;
            }
          } else {
            p.currentConnection = connections[Math.floor(Math.random() * connections.length)];
            p.direction = Math.random() > 0.5 ? 1 : -1;
          }
        }

        const progress = p.direction === 1 ? p.t : 1.0 - p.t;
        p.currentConnection.curve.getPointAt(progress, p.mesh.position);
        
        const pScale = 0.6 + Math.sin(progress * Math.PI) * 0.6;
        p.mesh.scale.setScalar(pScale);
      });

      renderer.render(scene, camera);
    }

    // Handle Resize
    function handleResize() {
      const w = container.clientWidth || window.innerWidth;
      const h = container.clientHeight || window.innerHeight;
      
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    }
    window.addEventListener('resize', handleResize);

    // Page visibility listener
    function handleVisibilityChange() {
      if (document.hidden) {
        isLooping = false;
        clock.stop();
      } else {
        if (!isLooping) {
          isLooping = true;
          clock.start();
          animate();
        }
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Append online status diagnostic badge
    const badge = document.createElement('div');
    badge.id = 'threejs-diagnostic-badge';
    badge.style.position = 'absolute';
    badge.style.bottom = '24px';
    badge.style.right = '24px';
    badge.style.padding = '6px 12px';
    badge.style.backgroundColor = 'rgba(11, 31, 58, 0.85)';
    badge.style.border = '1px solid #38BDF8';
    badge.style.borderRadius = '4px';
    badge.style.color = '#38BDF8';
    badge.style.fontFamily = 'monospace';
    badge.style.fontSize = '10px';
    badge.style.letterSpacing = '0.1em';
    badge.style.zIndex = '20';
    badge.style.pointerEvents = 'none';
    badge.innerText = '3D NETWORK: ONLINE';
    
    // Parent element of the container is the absolute visualizer frame
    const parentContainer = container.parentNode;
    if (parentContainer) {
      // Clean up previous badges if any
      const existingBadge = parentContainer.querySelector('#threejs-diagnostic-badge');
      if (existingBadge) {
        parentContainer.removeChild(existingBadge);
      }
      parentContainer.appendChild(badge);
    }

    // Run Visualizer & Print Successful Initialization Logs
    clock.start();
    animate();

    if (typeof THREE !== 'undefined' && container && renderer && scene && camera) {
      console.log("MuleGuard Three.js initialized successfully");
    }
  }

  function tryInit() {
    // Save CPU on small mobile resolutions where the left panel is hidden
    if (window.innerWidth < 768) {
      return;
    }

    const container = document.getElementById('threejs-container-ANIMATION_7');
    if (!container) return;

    const w = container.clientWidth;
    const h = container.clientHeight;

    // Wait until the layout engine has computed non-zero dimensions
    if (w > 0 && h > 0) {
      initVisualizer(container, w, h);
    } else {
      retries++;
      if (retries < MAX_RETRIES) {
        requestAnimationFrame(tryInit);
      } else {
        console.warn("MuleGuard Three.js initialization timed out: container has zero dimensions.");
      }
    }
  }

  // Defer initialization to allow Tailwind CSS layout generation to complete
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    requestAnimationFrame(tryInit);
  } else {
    window.addEventListener('DOMContentLoaded', () => {
      requestAnimationFrame(tryInit);
    });
  }
})();
