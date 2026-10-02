const fs = require('fs');
const path = require('path');

function generatePage(role) {
    const isCompliance = (role === 'compliance');
    const userInitials = isCompliance ? 'SM' : 'AK';
    const userName = isCompliance ? 'S. Mehta' : 'A. Kumar';
    const userRole = isCompliance ? 'Compliance Officer' : 'Senior Analyst';
    const statusText = isCompliance ? 'Compliance Graph Online' : 'Intelligence Engine Online';
    const pageSub = isCompliance 
        ? 'Compliance graph topology analysis, multi-hop money flow, and mule ring detection.'
        : 'Investigator multi-hop money flow analysis, mule ring detection, and transaction topology.';

    // Nav links for compliance vs investigator
    const complianceNav = `
				<!-- Compliance Control Group -->
				<div class="space-y-1">
					<div class="px-3 mb-1.5 sidebar-group-title">
						<span class="font-mono-technical text-[10px] text-on-primary-container tracking-wider uppercase opacity-55">Compliance Control</span>
					</div>
					<a href="dashboard.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Dashboard">
						<span class="material-symbols-outlined text-[20px]">dashboard</span>
						<span class="sidebar-label">Dashboard</span>
					</a>
					<a href="escalated-cases.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Escalated Cases">
						<span class="material-symbols-outlined text-[20px]">warning</span>
						<span class="sidebar-label">Escalated Cases</span>
					</a>
					<a href="high-risk-alerts.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="High-Risk Alerts">
						<span class="material-symbols-outlined text-[20px]">error</span>
						<span class="sidebar-label">High-Risk Alerts</span>
					</a>
					<a href="decisions.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Decisions / Review">
						<span class="material-symbols-outlined text-[20px]">gavel</span>
						<span class="sidebar-label">Decisions / Review</span>
					</a>
					<a href="reports.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Reports">
						<span class="material-symbols-outlined text-[20px]">assessment</span>
						<span class="sidebar-label">Reports</span>
					</a>
				</div>

				<!-- Investigation Tools Group -->
				<div class="space-y-1">
					<div class="px-3 mb-1.5 sidebar-group-title">
						<span class="font-mono-technical text-[10px] text-on-primary-container tracking-wider uppercase opacity-55">Investigation Tools</span>
					</div>
					<a href="investigations.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Investigations">
						<span class="material-symbols-outlined text-[20px]">search_insights</span>
						<span class="sidebar-label">Investigations</span>
					</a>
					<a href="transactions.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Transactions">
						<span class="material-symbols-outlined text-[20px]">receipt_long</span>
						<span class="sidebar-label">Transactions</span>
					</a>
					<a href="entities.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Entities">
						<span class="material-symbols-outlined text-[20px]">group</span>
						<span class="sidebar-label">Entities</span>
					</a>
					<a href="fraud_networks.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Fraud Networks">
						<span class="material-symbols-outlined text-[20px]">share</span>
						<span class="sidebar-label">Fraud Networks</span>
					</a>
					<a href="network-intelligence.html" class="sidebar-menu-item active-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary font-body-md text-[13px] bg-secondary-container/25 border-l-2 border-secondary-container transition-all duration-150" title="Network Intelligence">
						<span class="material-symbols-outlined text-[20px] text-secondary-container">hub</span>
						<span class="sidebar-label font-bold">Network Intelligence</span>
					</a>
				</div>
    `;

    const investigatorNav = `
				<!-- Command Center Group -->
				<div class="space-y-1">
					<div class="px-3 mb-1.5 sidebar-group-title">
						<span class="font-mono-technical text-[10px] text-on-primary-container tracking-wider uppercase opacity-55">Command Center</span>
					</div>
					<a href="dashboard.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Dashboard">
						<span class="material-symbols-outlined text-[20px]">dashboard</span>
						<span class="sidebar-label">Dashboard</span>
					</a>
					<a href="investigations.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Investigations">
						<span class="material-symbols-outlined text-[20px]">search_insights</span>
						<span class="sidebar-label">Investigations</span>
					</a>
					<a href="transactions.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Transactions">
						<span class="material-symbols-outlined text-[20px]">receipt_long</span>
						<span class="sidebar-label">Transactions</span>
					</a>
					<a href="entities.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Entities">
						<span class="material-symbols-outlined text-[20px]">group</span>
						<span class="sidebar-label">Entities</span>
					</a>
					<a href="fraud_networks.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Fraud Networks">
						<span class="material-symbols-outlined text-[20px]">share</span>
						<span class="sidebar-label">Fraud Networks</span>
					</a>
					<a href="alerts.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Alerts">
						<span class="material-symbols-outlined text-[20px]">notifications_active</span>
						<span class="sidebar-label">Alerts</span>
					</a>
					<a href="cases.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Cases">
						<span class="material-symbols-outlined text-[20px]">work</span>
						<span class="sidebar-label">Cases</span>
					</a>
				</div>

				<!-- Intelligence Group -->
				<div class="space-y-1">
					<div class="px-3 mb-1.5 sidebar-group-title">
						<span class="font-mono-technical text-[10px] text-on-primary-container tracking-wider uppercase opacity-55">Intelligence</span>
					</div>
					<a href="risk-analytics.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Risk Analytics">
						<span class="material-symbols-outlined text-[20px]">monitoring</span>
						<span class="sidebar-label">Risk Analytics</span>
					</a>
					<a href="network-intelligence.html" class="sidebar-menu-item active-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary font-body-md text-[13px] bg-secondary-container/25 border-l-2 border-secondary-container transition-all duration-150" title="Network Intelligence">
						<span class="material-symbols-outlined text-[20px] text-secondary-container">hub</span>
						<span class="sidebar-label font-bold">Network Intelligence</span>
					</a>
					<a href="watchlists.html" class="sidebar-menu-item flex items-center gap-3 px-3 py-2 rounded-lg text-on-primary-container/70 font-body-md text-[13px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150" title="Watchlists">
						<span class="material-symbols-outlined text-[20px]">rule_folder</span>
						<span class="sidebar-label">Watchlists</span>
					</a>
				</div>
    `;

    return `<!DOCTYPE html>
<html class="light" lang="en">

<head>
	<!-- Authentication Guard -->
	<script src="../../scripts/auth-guard.js"></script>
	<script src="../../scripts/api.js"></script>
	<script src="../../scripts/data-store.js"></script>
	<meta charset="utf-8" />
	<meta content="width=device-width, initial-scale=1.0" name="viewport" />
	<title>MuleGuard - Network Intelligence</title>
	<link href="https://fonts.googleapis.com" rel="preconnect" />
	<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect" />
	<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&amp;display=swap"
		rel="stylesheet" />
	<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
		rel="stylesheet" />
	<link rel="stylesheet" href="../../style.css" />
	<script>
		// Suppress Chrome extension errors
		(function() {
			const originalWarn = console.warn;
			const originalError = console.error;
			const originalLog = console.log;

			const isExtensionMessage = (...args) => {
				const msg = args.join(' ');
				return (
					msg.includes('BHK') || 
					msg.includes('widget') || 
					msg.includes('publicKey') || 
					msg.includes('merchantId') ||
					msg.includes('chrome-extension') ||
					msg.includes('couponCollection')
				);
			};

			console.warn = function(...args) {
				if (isExtensionMessage(...args)) return;
				originalWarn.apply(console, args);
			};

			console.error = function(...args) {
				if (isExtensionMessage(...args)) return;
				originalError.apply(console, args);
			};

			console.log = function(...args) {
				if (isExtensionMessage(...args)) return;
				originalLog.apply(console, args);
			};
		})();
	</script>
	<style>
		.material-symbols-outlined {
			font-variation-settings:
				'FILL' 0,
				'wght' 400,
				'GRAD' 0,
				'opsz' 20
		}
		
		/* Custom scrollbar styles */
		::-webkit-scrollbar {
			width: 6px;
			height: 6px;
		}
		::-webkit-scrollbar-track {
			background: #f1f5f9;
		}
		::-webkit-scrollbar-thumb {
			background: #cbd5e1;
			border-radius: 4px;
		}
		::-webkit-scrollbar-thumb:hover {
			background: #94a3b8;
		}

		/* Visual styling & micro-animations */
		@keyframes flowAnim {
			from { stroke-dashoffset: 24; }
			to { stroke-dashoffset: 0; }
		}
		.flow-line {
			stroke-dasharray: 4, 3;
			animation: flowAnim 1.6s linear infinite;
		}

		/* Staggered entrance animations */
		@keyframes fadeInUp {
			from { opacity: 0; transform: translateY(8px); }
			to { opacity: 1; transform: translateY(0); }
		}
		.fade-in-animate {
			animation: fadeInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
		}
		.kpi-card-animate {
			opacity: 0;
			animation: fadeInUp 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
		}
		.stagger-1 { animation-delay: 0.04s; }
		.stagger-2 { animation-delay: 0.08s; }
		.stagger-3 { animation-delay: 0.04s; }
		.stagger-4 { animation-delay: 0.08s; }

		/* Canvas Pan & Node Drag Styling — Hand-style photo interaction */
		#graph-viewport-wrapper {
			cursor: grab;
			user-select: none;
		}
		#graph-viewport-wrapper svg {
			cursor: grab;
			user-select: none;
		}
		#graph-viewport-wrapper.is-panning,
		body.is-canvas-panning,
		body.is-canvas-panning #graph-viewport-wrapper,
		body.is-canvas-panning #graph-viewport-wrapper svg {
			cursor: grabbing !important;
			user-select: none;
		}
		/* Prevent link lines and badges from intercepting canvas background clicks */
		.links-layer,
		.links-layer * {
			pointer-events: none !important;
		}
		.group\/node, [data-node-id] {
			cursor: grab;
			pointer-events: auto;
		}
		body.is-node-dragging,
		body.is-node-dragging .group\/node,
		body.is-node-dragging #graph-viewport-wrapper {
			cursor: grabbing !important;
			user-select: none;
		}

		/* Fullscreen Entire Network Intelligence Workspace */
		body.network-fullscreen-mode {
			overflow: hidden !important;
		}
		body.network-fullscreen-mode #sidebar-container {
			display: flex !important;
			z-index: 40;
		}
		body.network-fullscreen-mode header {
			display: flex !important;
			z-index: 30;
		}
		body.network-fullscreen-mode #main-content-layout {
			height: 100vh !important;
			overflow: hidden !important;
		}
		body.network-fullscreen-mode #main-workspace-container {
			height: calc(100vh - 56px) !important;
			max-height: calc(100vh - 56px) !important;
			overflow-y: auto !important;
			padding: 1rem !important;
			scroll-behavior: smooth;
		}
		body.network-fullscreen-mode #graph-panel-section {
			width: 100% !important;
			margin-bottom: 1.5rem !important;
		}
		body.network-fullscreen-mode #graph-viewport-wrapper {
			height: calc(100vh - 220px) !important;
			min-height: 560px !important;
		}

		/* Sliding Inspection Drawer Animations */
		#network-inspection-drawer {
			box-shadow: -10px 0 35px -5px rgba(0, 0, 0, 0.6);
		}
		#network-inspection-drawer.drawer-open {
			transform: translateX(0) !important;
		}
		#network-inspection-overlay.overlay-open {
			display: block !important;
			opacity: 1 !important;
		}

		/* Collapsible Sidebar Styles */
		body.sidebar-collapsed #sidebar-container {
			width: 68px !important;
		}
		body.sidebar-collapsed .sidebar-label,
		body.sidebar-collapsed .sidebar-group-title,
		body.sidebar-collapsed #sidebar-logo-container,
		body.sidebar-collapsed #sidebar-user-info,
		body.sidebar-collapsed #sidebar-status-pill {
			display: none !important;
		}
		body.sidebar-collapsed .sidebar-menu-item {
			justify-content: center !important;
			padding-left: 0 !important;
			padding-right: 0 !important;
		}
		body.sidebar-collapsed #sidebar-user-box {
			justify-content: center !important;
			padding: 4px 0 !important;
		}

		/* Accessibility: reduce motion overrides */
		@media (prefers-reduced-motion: reduce) {
			.heading-animate, .kpi-card-animate, .fade-in-animate, .flow-line, .halo-pulse {
				animation: none !important;
				transition: none !important;
			}
		}
	</style>
</head>

<body class="bg-surface-container-low text-on-surface h-screen w-full flex overflow-hidden font-sans select-none">
	
	<!-- Mobile Sidebar Overlay -->
	<div id="sidebar-overlay" class="fixed inset-0 bg-primary/40 backdrop-blur-sm z-30 hidden transition-opacity duration-200" onclick="toggleMobileSidebar()"></div>

	<!-- Left Navigation Sidebar -->
	<aside id="sidebar-container" class="fixed inset-y-0 left-0 z-40 w-[260px] bg-primary-container border-r border-[#1e293b] flex flex-col justify-between transform -translate-x-full md:translate-x-0 transition-all duration-300 ease-in-out select-none">
		
		<div class="flex flex-col flex-1 overflow-y-auto">
			<!-- Sidebar Header & Logo with Collapse/Expand Button -->
			<div id="sidebar-header-box" class="h-[56px] flex items-center justify-between px-4 border-b border-[#1e293b] gap-2 flex-shrink-0">
				<div id="sidebar-logo-container" class="flex items-center gap-2 overflow-hidden transition-all duration-200">
					<img alt="MuleGuard Logo" class="w-[100px] h-auto object-contain" src="../../../assets/MULEGUARD_LOGO_W&G.png" />
				</div>
				<button id="sidebar-collapse-btn" onclick="toggleSidebarCollapse()" class="p-1.5 rounded-lg text-on-primary-container/70 hover:text-white hover:bg-secondary-container/20 transition-all focus:outline-none flex-shrink-0" title="Collapse / Expand Navigation">
					<span id="sidebar-collapse-icon" class="material-symbols-outlined text-[20px]">menu_open</span>
				</button>
			</div>

			<!-- Sidebar Menu Groups -->
			<nav class="flex-1 px-3 py-4 space-y-5">
				${isCompliance ? complianceNav : investigatorNav}
			</nav>
		</div>

		<!-- Sidebar Footer Status -->
		<div class="p-3 border-t border-[#1e293b] space-y-2 flex-shrink-0">
			<div id="sidebar-status-pill" class="flex items-center justify-between px-1">
				<div class="flex items-center gap-2">
					<span class="inline-block w-2 h-2 rounded-full bg-risk-low animate-pulse"></span>
					<span class="font-mono-technical text-[10px] text-[#38BDF8] tracking-wider uppercase">Systems OK</span>
				</div>
				<span class="font-mono-technical text-[10px] text-on-primary-container/40">v2.1</span>
			</div>
			<div id="sidebar-user-box" class="flex items-center justify-between p-2 rounded-lg bg-primary/20 border border-[#1e293b]">
				<div class="flex items-center gap-2.5 overflow-hidden">
					<div class="w-7 h-7 rounded-full bg-secondary-container/40 border border-secondary-container/60 flex items-center justify-center font-mono-technical text-[11px] font-bold text-on-primary flex-shrink-0">
						${userInitials}
					</div>
					<div id="sidebar-user-info" class="flex flex-col min-w-0">
						<span class="font-body-md text-[12px] font-bold text-on-primary truncate">${userName}</span>
						<span class="font-mono-technical text-[10px] text-on-primary-container/50 truncate">${userRole}</span>
					</div>
				</div>
				<a href="../../login.html" class="p-1 rounded text-on-primary-container/60 hover:text-white hover:bg-secondary-container/20 transition-colors" title="Log Out">
					<span class="material-symbols-outlined text-[16px]">logout</span>
				</a>
			</div>
		</div>

	</aside>

	<!-- Main Content Layout Area -->
	<div class="flex-1 flex flex-col h-full overflow-hidden md:pl-[260px] transition-all duration-300 ease-in-out min-w-0" id="main-content-layout">
		
		<!-- Top Application Header Bar -->
		<header class="h-[56px] border-b border-outline-variant/30 bg-interface-base flex items-center justify-between px-4 sm:px-6 z-20 flex-shrink-0">
			<div class="flex items-center gap-3">
				<button class="md:hidden p-1.5 rounded-lg text-on-surface hover:bg-surface-container-high transition-colors focus:outline-none" onclick="toggleMobileSidebar()" title="Toggle Navigation">
					<span class="material-symbols-outlined text-[20px]">menu</span>
				</button>
				<div class="flex items-center gap-2">
					<div class="w-2 h-2 rounded-full bg-secondary-container"></div>
					<h1 class="font-headline-md text-[15px] sm:text-[17px] font-bold text-on-surface tracking-tight">Network Intelligence</h1>
					<span class="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] font-mono-technical uppercase tracking-wider bg-secondary-container/15 text-secondary-container border border-secondary-container/30 font-semibold">PostgreSQL Topology</span>
				</div>
			</div>

			<div class="flex items-center gap-2 sm:gap-3">
				<div class="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-surface-container-low border border-outline-variant/40">
					<span class="w-2 h-2 rounded-full bg-risk-low animate-pulse"></span>
					<span class="font-mono-technical text-[11px] text-on-surface-variant font-medium">${statusText}</span>
				</div>
				<button class="p-1.5 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors focus:outline-none" onclick="loadNetworksData()" title="Refresh Network Topology">
					<span class="material-symbols-outlined text-[18px]">refresh</span>
				</button>
			</div>
		</header>

		<!-- Main Workspace Container with Vertical Scroll -->
		<main class="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4" id="main-workspace-container">
			
			<!-- Page Subtitle & Overview Context -->
			<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-1 border-b border-outline-variant/20">
				<div>
					<p class="font-body-md text-[12.5px] text-on-surface-variant leading-relaxed">
						${pageSub} Authoritative directed links from PostgreSQL ledger transactions.
					</p>
				</div>
			</div>

			<!-- KPI Summary Metric Cards -->
			<section class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4" id="kpi-summary-cards">
				<!-- Card 1 -->
				<div class="bg-interface-base border border-outline-variant/30 p-3.5 rounded-xl shadow-sm hover:shadow hover:-translate-y-0.5 transition-all duration-200 group relative overflow-hidden kpi-card-animate stagger-1">
					<div class="absolute top-0 left-0 w-full h-[2.5px] bg-[#316BF3]"></div>
					<div class="flex justify-between items-start mb-1.5">
						<span class="font-mono-technical text-[9.5px] text-on-surface-variant uppercase tracking-wider font-semibold">Total Networks</span>
						<div class="w-7 h-7 rounded-lg bg-[#316BF3]/10 flex items-center justify-center">
							<span class="material-symbols-outlined text-[16px] text-[#316BF3]">hub</span>
						</div>
					</div>
					<h3 id="count-total" class="font-headline-lg text-[22px] text-on-surface font-extrabold leading-tight select-all tracking-tight">--</h3>
					<div class="flex items-center gap-1 mt-1">
						<span class="font-body-md text-[11px] text-on-surface-variant font-medium leading-none">Extracted from PostgreSQL</span>
					</div>
				</div>

				<!-- Card 2 -->
				<div class="bg-interface-base border border-outline-variant/30 p-3.5 rounded-xl shadow-sm hover:shadow hover:-translate-y-0.5 transition-all duration-200 group relative overflow-hidden kpi-card-animate stagger-2">
					<div class="absolute top-0 left-0 w-full h-[2.5px] bg-risk-critical"></div>
					<div class="flex justify-between items-start mb-1.5">
						<span class="font-mono-technical text-[9.5px] text-on-surface-variant uppercase tracking-wider font-semibold text-risk-critical">High-Risk Mule Rings</span>
						<div class="w-7 h-7 rounded-lg bg-risk-critical/10 flex items-center justify-center">
							<span class="material-symbols-outlined text-[16px] text-risk-critical">warning</span>
						</div>
					</div>
					<h3 id="count-high-risk" class="font-headline-lg text-[22px] text-on-surface font-extrabold leading-tight select-all tracking-tight">--</h3>
					<div class="flex items-center gap-1 mt-1">
						<span class="font-body-md text-[11px] text-risk-critical font-semibold leading-none">Score ≥ 80 / 100</span>
					</div>
				</div>

				<!-- Card 3 -->
				<div class="bg-interface-base border border-outline-variant/30 p-3.5 rounded-xl shadow-sm hover:shadow hover:-translate-y-0.5 transition-all duration-200 group relative overflow-hidden kpi-card-animate stagger-3">
					<div class="absolute top-0 left-0 w-full h-[2.5px] bg-risk-high"></div>
					<div class="flex justify-between items-start mb-1.5">
						<span class="font-mono-technical text-[9.5px] text-on-surface-variant uppercase tracking-wider font-semibold text-risk-high">Under Review</span>
						<div class="w-7 h-7 rounded-lg bg-risk-high/10 flex items-center justify-center">
							<span class="material-symbols-outlined text-[16px] text-risk-high">pending</span>
						</div>
					</div>
					<h3 id="count-review" class="font-headline-lg text-[22px] text-on-surface font-extrabold leading-tight select-all tracking-tight">--</h3>
					<div class="flex items-center gap-1 mt-1">
						<span class="font-body-md text-[11px] text-risk-high font-semibold leading-none">Score 55 - 79</span>
					</div>
				</div>

				<!-- Card 4 -->
				<div class="bg-interface-base border border-outline-variant/30 p-3.5 rounded-xl shadow-sm hover:shadow hover:-translate-y-0.5 transition-all duration-200 group relative overflow-hidden kpi-card-animate stagger-4">
					<div class="absolute top-0 left-0 w-full h-[2.5px] bg-red-600"></div>
					<div class="flex justify-between items-start mb-1.5">
						<span class="font-mono-technical text-[9.5px] text-on-surface-variant uppercase tracking-wider font-semibold text-red-600">Flagged Networks</span>
						<div class="w-7 h-7 rounded-lg bg-red-600/10 flex items-center justify-center">
							<span class="material-symbols-outlined text-[16px] text-red-600">new_releases</span>
						</div>
					</div>
					<h3 id="count-newly-detected" class="font-headline-lg text-[22px] text-on-surface font-extrabold leading-tight select-all tracking-tight">--</h3>
					<div class="flex items-center gap-1 mt-1">
						<span class="font-body-md text-[11px] text-red-600 font-semibold leading-none">Targeted for immediate freeze</span>
					</div>
				</div>
			</section>

			<!-- Live Network Topology Graph Canvas Section -->
			<section id="graph-panel-section" class="bg-[#0b192c] border border-[#1e293b] rounded-xl shadow-md p-4 select-none fade-in-animate text-left relative transition-all duration-200">
				
				<!-- Top Bar: Title, Search Account Field, Active Network Chip, Viewport Controls -->
				<div class="flex flex-col xl:flex-row xl:items-center justify-between pb-3 border-b border-[#1e2e4a] gap-3">
					<div class="flex items-center gap-3">
						<div class="w-9 h-9 rounded-xl bg-gradient-to-br from-[#316bf3]/30 to-[#0284c7]/20 border border-[#38bdf8]/40 flex items-center justify-center flex-shrink-0 shadow-inner">
							<span class="material-symbols-outlined text-[20px] text-[#38bdf8]">hub</span>
						</div>
						<div>
							<div class="flex items-center gap-2">
								<h3 class="font-headline-md text-[15px] text-white font-bold tracking-tight">Real Transaction Network Mesh</h3>
								<span class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">PostgreSQL Force Topology</span>
							</div>
							<p class="font-body-md text-[11px] text-[#94a3b8] leading-tight mt-0.5">Authoritative PostgreSQL money flow. Drag background to pan, drag nodes freely, or search Account ID.</p>
						</div>
					</div>

					<div class="flex items-center gap-2 flex-wrap">
						<!-- Account Search Field -->
						<div class="relative flex items-center w-full sm:w-[280px]">
							<span class="absolute left-3 material-symbols-outlined text-[17px] text-[#38bdf8] pointer-events-none">search</span>
							<input 
								type="text" 
								id="account-graph-search" 
								placeholder="Search Account ID (e.g. ACC-982064)..." 
								class="w-full bg-[#071324] border border-[#1e2e4a] rounded-lg pl-9 pr-8 py-1.5 font-mono-technical text-[12px] text-white placeholder-[#64748b] focus:outline-none focus:border-[#38bdf8] focus:ring-1 focus:ring-[#38bdf8] transition-all"
								autocomplete="off"
								oninput="handleAccountSearchInput(this.value)"
								onkeydown="handleAccountSearchKeyDown(event)"
							/>
							<button id="search-clear-btn" class="absolute right-2.5 text-[#64748b] hover:text-white hidden focus:outline-none" onclick="clearAccountSearch()" title="Clear search">
								<span class="material-symbols-outlined text-[15px]">close</span>
							</button>
							<!-- Suggestions dropdown -->
							<div id="account-search-suggestions" class="absolute top-full left-0 right-0 mt-1 max-h-[220px] overflow-y-auto bg-[#071324] border border-[#1e2e4a] rounded-lg shadow-2xl py-1 z-50 hidden divide-y divide-[#1e2e4a]/40 text-left"></div>
						</div>

						<!-- Active Network Chip -->
						<div id="active-network-chip" class="hidden sm:flex items-center gap-2 bg-[#071324] border border-[#1e2e4a] rounded-lg px-3 py-1.5 text-[12px] select-none">
							<span class="w-2 h-2 rounded-full bg-secondary-container animate-pulse flex-shrink-0"></span>
							<span class="font-mono-technical text-[10px] text-[#94a3b8] uppercase font-bold tracking-wider">Active Net:</span>
							<span id="active-network-name-badge" class="font-mono-technical text-[11px] font-bold text-white whitespace-nowrap">...</span>
						</div>

						<!-- Zoom, Pan, Reset & Fullscreen Controls -->
						<div class="flex items-center bg-[#071324] border border-[#1e2e4a] rounded-lg p-0.5">
							<button class="p-1.5 hover:bg-[#1e2e4a] text-[#94a3b8] hover:text-white rounded transition-colors" title="Zoom In (+)" onclick="zoomInGraph()">
								<span class="material-symbols-outlined text-[18px]">zoom_in</span>
							</button>
							<button class="p-1.5 hover:bg-[#1e2e4a] text-[#94a3b8] hover:text-white rounded transition-colors" title="Zoom Out (-)" onclick="zoomOutGraph()">
								<span class="material-symbols-outlined text-[18px]">zoom_out</span>
							</button>
							<button class="p-1.5 hover:bg-[#1e2e4a] text-[#94a3b8] hover:text-white rounded transition-colors" title="Reset View" onclick="resetActiveVisualizerGraph()">
								<span class="material-symbols-outlined text-[18px]">restart_alt</span>
							</button>
							<button id="fullscreen-btn" class="p-1.5 hover:bg-[#1e2e4a] text-[#94a3b8] hover:text-white rounded transition-colors" title="Toggle Fullscreen" onclick="toggleFullscreenVisualizer()">
								<span class="material-symbols-outlined text-[18px]">fullscreen</span>
							</button>
						</div>
					</div>
				</div>

				<!-- Secondary Controls Toolbar: Hop filters & Feature Toggles -->
				<div class="flex flex-wrap items-center justify-between gap-3 pt-2.5 text-[12px] border-b border-[#1e2e4a]/60 pb-2.5">
					<!-- Hop Neighborhood Selector -->
					<div class="flex items-center gap-2">
						<span class="font-mono-technical text-[10px] text-[#94a3b8] uppercase font-bold tracking-wider">Neighborhood:</span>
						<div class="inline-flex rounded-lg border border-[#1e2e4a] bg-[#071324] p-0.5" id="hop-filter-group">
							<button class="hop-btn px-2.5 py-1 text-[11px] font-mono rounded font-semibold transition-all bg-[#1d4ed8] text-white" data-hop="0" onclick="setHopDepthFilter(0)">All</button>
							<button class="hop-btn px-2.5 py-1 text-[11px] font-mono rounded font-semibold transition-all text-[#94a3b8] hover:text-white" data-hop="1" onclick="setHopDepthFilter(1)">1-Hop</button>
							<button class="hop-btn px-2.5 py-1 text-[11px] font-mono rounded font-semibold transition-all text-[#94a3b8] hover:text-white" data-hop="2" onclick="setHopDepthFilter(2)">2-Hop</button>
							<button class="hop-btn px-2.5 py-1 text-[11px] font-mono rounded font-semibold transition-all text-[#94a3b8] hover:text-white" data-hop="3" onclick="setHopDepthFilter(3)">3-Hop</button>
						</div>
					</div>

					<!-- Toggles: Labels, Amounts, Directions, High-Risk Only -->
					<div class="flex items-center gap-4 flex-wrap">
						<label class="inline-flex items-center gap-1.5 cursor-pointer text-[#94a3b8] hover:text-white transition-colors">
							<input type="checkbox" id="toggle-labels" class="rounded bg-[#071324] border-[#1e2e4a] text-secondary focus:ring-0" checked onchange="toggleGraphLabels(this.checked)" />
							<span class="font-mono-technical text-[11px]">Labels</span>
						</label>
						<label class="inline-flex items-center gap-1.5 cursor-pointer text-[#94a3b8] hover:text-white transition-colors">
							<input type="checkbox" id="toggle-amounts" class="rounded bg-[#071324] border-[#1e2e4a] text-secondary focus:ring-0" checked onchange="toggleGraphAmounts(this.checked)" />
							<span class="font-mono-technical text-[11px]">Amounts</span>
						</label>
						<label class="inline-flex items-center gap-1.5 cursor-pointer text-[#94a3b8] hover:text-white transition-colors">
							<input type="checkbox" id="toggle-directions" class="rounded bg-[#071324] border-[#1e2e4a] text-secondary focus:ring-0" checked onchange="toggleGraphDirections(this.checked)" />
							<span class="font-mono-technical text-[11px]">Directions</span>
						</label>
						<label class="inline-flex items-center gap-1.5 cursor-pointer text-red-400 hover:text-red-300 transition-colors">
							<input type="checkbox" id="toggle-suspicious" class="rounded bg-[#071324] border-[#1e2e4a] text-red-500 focus:ring-0" onchange="toggleSuspiciousOnly(this.checked)" />
							<span class="font-mono-technical text-[11px]">High-Risk Only</span>
						</label>
					</div>
				</div>

				<!-- Interactive SVG Graph Viewport Canvas -->
				<div id="graph-viewport-wrapper" class="w-full h-[500px] relative mt-2.5 flex items-center justify-center bg-[#071324] border border-[#122543] rounded-xl overflow-hidden">
					<svg id="network-graph-svg" class="w-full h-full select-none" viewBox="0 0 1000 500">
						<!-- Markers & Viewport Group will be rendered dynamically -->
					</svg>

					<!-- Canvas Legend Overlay -->
					<div class="absolute bottom-3 left-3 bg-[#0b192c]/90 backdrop-blur-sm border border-[#1e2e4a] rounded-lg px-3 py-1.5 text-[10.5px] text-[#94a3b8] flex flex-wrap items-center gap-3.5 shadow-md pointer-events-none">
						<span class="font-mono-technical text-[9.5px] uppercase font-bold text-white tracking-wider">Legend:</span>
						<div class="flex items-center gap-1.5">
							<span class="w-3 h-3 rounded-full bg-[#ef4444] border border-[#fca5a5] shadow-[0_0_8px_rgba(239,68,68,0.8)]"></span>
							<span>Suspicious / Mule</span>
						</div>
						<div class="flex items-center gap-1.5">
							<span class="w-2.5 h-2.5 rounded-full bg-[#f97316] border border-[#fdba74]"></span>
							<span>Under Review</span>
						</div>
						<div class="flex items-center gap-1.5">
							<span class="w-2.5 h-2.5 rounded-full bg-[#38bdf8] border border-[#7dd3fc]"></span>
							<span>Legitimate Retail</span>
						</div>
						<div class="flex items-center gap-1.5">
							<span class="w-3 h-2.5 rounded-sm bg-[#422006] border border-[#eab308]"></span>
							<span>Small Business</span>
						</div>
						<div class="flex items-center gap-1.5">
							<span class="w-3.5 h-[2px] bg-[#f59e0b]"></span>
							<span>Focus Edge</span>
						</div>
					</div>

					<!-- Viewport Hints Overlay -->
					<div class="absolute top-3 right-3 bg-[#0b192c]/80 backdrop-blur-sm border border-[#1e2e4a] rounded px-2 py-1 text-[10px] text-[#94a3b8] pointer-events-none hidden sm:block">
						Drag background to pan • Drag node to move • Scroll to zoom
					</div>
				</div>

			</section>

			<!-- Selected Account Dossier Section (19 PostgreSQL Fields) -->
			<section class="bg-[#071324] border border-[#1e293b] rounded-xl shadow-md p-4 text-left space-y-4 fade-in-animate" id="selected-account-dossier">
				<div class="py-8 text-center text-slate-400 font-body-md">
					<span class="material-symbols-outlined text-[28px] text-sky-400 animate-spin">progress_activity</span>
					<p class="mt-2 text-[12px]">Loading account investigation details from PostgreSQL...</p>
				</div>
			</section>

			<!-- Filter & Search Controls for Networks Queue -->
			<section class="bg-interface-base border border-outline-variant/30 p-3.5 rounded-xl shadow-sm space-y-3">
				<div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
					<div class="flex items-center gap-2">
						<span class="material-symbols-outlined text-[18px] text-secondary">filter_list</span>
						<h4 class="font-headline-md text-[13.5px] text-on-surface font-bold">Network Queue Filters</h4>
					</div>
					<div class="flex items-center gap-2 flex-wrap">
						<div class="relative w-full sm:w-[220px]">
							<span class="absolute left-2.5 top-2 material-symbols-outlined text-[16px] text-on-surface-variant pointer-events-none">search</span>
							<input type="text" id="filter-search" placeholder="Search network name or ID..." class="w-full bg-surface-container-low border border-outline-variant/40 rounded-lg pl-8 pr-3 py-1 font-body-md text-[12px] text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" oninput="onSearchInput()" />
						</div>
						<select id="filter-risk" class="bg-surface-container-low border border-outline-variant/40 rounded-lg px-2.5 py-1 font-mono-technical text-[11.5px] text-on-surface focus:outline-none focus:border-secondary" onchange="applyWorkspaceFilters()">
							<option value="All">All Risk Levels</option>
							<option value="Critical">Critical (≥ 90)</option>
							<option value="High">High (70 - 89)</option>
							<option value="Medium">Medium (50 - 69)</option>
							<option value="Low">Low (&lt; 50)</option>
						</select>
						<select id="filter-type" class="bg-surface-container-low border border-outline-variant/40 rounded-lg px-2.5 py-1 font-body-md text-[11.5px] text-on-surface focus:outline-none focus:border-secondary" onchange="applyWorkspaceFilters()">
							<option value="All">All Topology Types</option>
							<option value="Layering Loop">Layering Loop</option>
							<option value="Fan-In Aggregator">Fan-In Aggregator</option>
							<option value="Fan-Out Distributor">Fan-Out Distributor</option>
							<option value="Merchant Settlement Mesh">Merchant Settlement Mesh</option>
							<option value="Transaction Chain">Transaction Chain</option>
						</select>
						<select id="filter-status" class="bg-surface-container-low border border-outline-variant/40 rounded-lg px-2.5 py-1 font-body-md text-[11.5px] text-on-surface focus:outline-none focus:border-secondary" onchange="applyWorkspaceFilters()">
							<option value="All">All Statuses</option>
							<option value="Flagged">Flagged</option>
							<option value="Under Review">Under Review</option>
							<option value="Blocked">Blocked</option>
							<option value="Active">Active</option>
						</select>
						<button class="px-2.5 py-1 text-[11.5px] font-mono-technical rounded bg-surface-container-high text-on-surface hover:bg-surface-container-highest transition-colors" onclick="clearAllWorkspaceFilters()">
							Reset
						</button>
					</div>
				</div>
			</section>

			<!-- Main Table Networks Queue -->
			<section class="bg-interface-base border border-outline-variant/30 p-4 rounded-xl shadow-sm fade-in-animate">
				<div class="flex items-center justify-between pb-3 border-b border-[#e2e8f0]">
					<div>
						<h3 class="font-headline-md text-[15px] text-on-surface font-extrabold tracking-tight">Detected Transaction Networks</h3>
						<p class="font-body-md text-[11px] text-on-surface-variant">Click any Network ID or "Inspect" to open inspection drawer. Inspect drawer allows loading real topology into canvas.</p>
					</div>
					<span id="filtered-networks-count" class="font-mono-technical text-[11px] bg-surface-container-low px-2.5 py-1 rounded text-on-surface-variant border border-outline-variant/40">Showing all</span>
				</div>
				<div class="w-full overflow-x-auto mt-2">
					<table class="w-full border-collapse text-left" id="networks-table">
						<thead>
							<tr class="border-b border-[#e2e8f0]">
								<th class="py-2.5 px-3 font-mono-technical text-[10px] text-on-surface-variant uppercase tracking-wider whitespace-nowrap min-w-[110px]">Network ID</th>
								<th class="py-2.5 px-3 font-mono-technical text-[10px] text-on-surface-variant uppercase tracking-wider min-w-[170px]">Network Name</th>
								<th class="py-2.5 px-3 font-mono-technical text-[10px] text-on-surface-variant uppercase tracking-wider min-w-[135px]">Type</th>
								<th class="py-2.5 px-3 font-mono-technical text-[10px] text-on-surface-variant uppercase tracking-wider text-right min-w-[95px]">Risk Score</th>
								<th class="py-2.5 px-3 font-mono-technical text-[10px] text-on-surface-variant uppercase tracking-wider text-right min-w-[110px]">Total Value</th>
								<th class="py-2.5 px-3 font-mono-technical text-[10px] text-on-surface-variant uppercase tracking-wider text-right min-w-[80px]">Members</th>
								<th class="py-2.5 px-3 font-mono-technical text-[10px] text-on-surface-variant uppercase tracking-wider text-right min-w-[125px]">Connected Flow</th>
								<th class="py-2.5 px-3 font-mono-technical text-[10px] text-on-surface-variant uppercase tracking-wider min-w-[100px]">Last Activity</th>
								<th class="py-2.5 px-3 font-mono-technical text-[10px] text-on-surface-variant uppercase tracking-wider min-w-[100px]">Status</th>
								<th class="py-2.5 px-3 font-mono-technical text-[10px] text-on-surface-variant uppercase tracking-wider text-right min-w-[100px]">Action</th>
							</tr>
						</thead>
						<tbody id="networks-table-body" class="divide-y divide-[#e2e8f0]/80">
							<tr><td colspan="10" class="py-8 text-center text-on-surface-variant font-body-md">Connecting to PostgreSQL network intelligence...</td></tr>
						</tbody>
					</table>
				</div>
			</section>

		</main>
	</div>

	<!-- Custom Notification Toast -->
	<div id="toast" class="fixed bottom-5 right-5 bg-[#1e293b] text-white border border-[#334155] rounded-lg px-4 py-2.5 shadow-xl flex items-center gap-2.5 transform translate-y-20 opacity-0 transition-all duration-300 z-50 pointer-events-none">
		<span class="material-symbols-outlined text-[18px] text-secondary-container">info</span>
		<span id="toast-text" class="font-body-md text-[12px]">Notification message</span>
	</div>

	<!-- Network Inspection Drawer Backdrop Overlay -->
	<div id="network-inspection-overlay" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 hidden opacity-0 transition-opacity duration-300" onclick="closeNetworkInspectionDrawer()"></div>

	<!-- Network Inspection Drawer (Slide-in from Right) -->
	<aside id="network-inspection-drawer" class="fixed top-0 right-0 h-full w-[480px] max-w-[94vw] bg-[#0b192c] border-l border-[#1e2e4a] shadow-2xl z-50 transform translate-x-full transition-transform duration-300 ease-in-out flex flex-col text-left select-text" aria-labelledby="drawer-title" role="dialog" aria-modal="true">
		<!-- Drawer Header -->
		<div class="h-[62px] px-5 border-b border-[#1e2e4a] flex items-center justify-between flex-shrink-0 bg-[#071324]">
			<div class="flex items-center gap-3">
				<div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600/30 to-indigo-600/20 border border-blue-500/40 flex items-center justify-center text-sky-400">
					<span class="material-symbols-outlined text-[20px]">hub</span>
				</div>
				<div>
					<h3 id="drawer-title" class="font-headline-md text-[15px] text-white font-bold tracking-tight">Network Inspection</h3>
					<span id="drawer-network-id-subtitle" class="font-mono text-[11px] text-sky-400 font-semibold">Select a network</span>
				</div>
			</div>
			<button onclick="closeNetworkInspectionDrawer()" class="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#1e2e4a] transition-colors focus:outline-none" title="Close Drawer">
				<span class="material-symbols-outlined text-[20px]">close</span>
			</button>
		</div>

		<!-- Drawer Body (Scrollable with full network metrics and member details) -->
		<div id="drawer-content-body" class="flex-1 overflow-y-auto p-5 space-y-4 text-slate-300">
			<!-- Populated dynamically via openNetworkInspectionDrawer(netId) -->
		</div>

		<!-- Drawer Footer with Primary Action -->
		<div class="p-4 border-t border-[#1e2e4a] bg-[#071324] flex-shrink-0">
			<button id="drawer-view-graph-btn" onclick="executeLoadNetworkFromDrawer()" class="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-500 hover:to-indigo-500 text-white font-headline-md font-bold text-[14px] shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2 transition-all transform active:scale-[0.99] focus:outline-none">
				<span class="material-symbols-outlined text-[19px]">hub</span>
				<span>View Network Graph</span>
				<span class="material-symbols-outlined text-[16px]">arrow_forward</span>
			</button>
		</div>
	</aside>

	<!-- Javascript Dynamic Page Interactions -->
	<script>
		// Global network database loaded from PostgreSQL via FastAPI /api/v1/networks
		let networksDb = {};
		let currentlyRenderedNetworkId = null;
		let activeDrawerNetworkId = null;
		let cachedRows = [];
		let searchDebounceTimeout = null;

		// Graph Viewport State
		const graphState = {
			zoom: 1.0,
			panX: 0,
			panY: 0,
			isDraggingCanvas: false,
			isDraggingNode: false,
			draggedNodeId: null,
			draggedPos: null,
			dragStart: { x: 0, y: 0 },
			dragStartPointer: { x: 0, y: 0 },
			hasMovedNode: false,
			showLabels: true,
			showAmounts: true,
			showDirections: true,
			suspiciousOnly: false,
			hopDepth: 0, // 0 = All, 1 = 1-Hop, 2 = 2-Hop, 3 = 3-Hop
			selectedNodeId: null,
			nodePositions: {},
			canvasWidth: 1000,
			canvasHeight: 500
		};

		// 1. Sidebar Collapse / Expand Functionality
		function toggleSidebarCollapse() {
			const isCollapsed = document.body.classList.toggle('sidebar-collapsed');
			localStorage.setItem('muleguard_sidebar_collapsed', isCollapsed ? 'true' : 'false');
			const icon = document.getElementById('sidebar-collapse-icon');
			if (icon) {
				icon.textContent = isCollapsed ? 'menu' : 'menu_open';
			}
			setTimeout(() => {
				handleGraphResize();
			}, 310);
		}

		function initSidebarState() {
			if (localStorage.getItem('muleguard_sidebar_collapsed') === 'true') {
				document.body.classList.add('sidebar-collapsed');
				const icon = document.getElementById('sidebar-collapse-icon');
				if (icon) icon.textContent = 'menu';
			}
		}

		function toggleMobileSidebar() {
			const sidebar = document.getElementById('sidebar-container');
			const overlay = document.getElementById('sidebar-overlay');
			if (sidebar.classList.contains('-translate-x-full')) {
				sidebar.classList.remove('-translate-x-full');
				overlay.classList.remove('hidden');
			} else {
				sidebar.classList.add('-translate-x-full');
				overlay.classList.add('hidden');
			}
		}

		function showToast(message) {
			const toast = document.getElementById('toast');
			const toastText = document.getElementById('toast-text');
			if (!toast || !toastText) return;
			toastText.textContent = message;
			toast.classList.remove('translate-y-20', 'opacity-0', 'pointer-events-none');
			toast.classList.add('translate-y-0', 'opacity-100');
			setTimeout(() => {
				toast.classList.remove('translate-y-0', 'opacity-100');
				toast.classList.add('translate-y-20', 'opacity-0', 'pointer-events-none');
			}, 3200);
		}

		// 2. Fetch authoritative data from PostgreSQL -> FastAPI
		async function loadNetworksData() {
			try {
				let networksList = [];
				if (window.MuleGuardAPI && typeof window.MuleGuardAPI.getNetworks === 'function') {
					networksList = await window.MuleGuardAPI.getNetworks();
				} else {
					const res = await fetch('/api/v1/networks');
					if (res.ok) {
						networksList = await res.json();
					}
				}

				if (Array.isArray(networksList) && networksList.length > 0) {
					networksDb = {};
					networksList.forEach(net => {
						networksDb[net.id] = net;
					});
				} else {
					console.warn('[MuleGuard] Empty network response, initializing fallback...');
				}

				renderNetworksTable(Object.values(networksDb));

				// Auto-load first network into the graph workspace if none rendered
				const netIds = Object.keys(networksDb);
				if (netIds.length > 0 && !currentlyRenderedNetworkId) {
					const initialId = netIds[0];
					currentlyRenderedNetworkId = initialId;
					renderNetworkGraph(initialId, 'network-graph-svg');
					updateActiveNetworkBadge(networksDb[initialId]);
				}
			} catch (err) {
				console.error('[MuleGuard] Error loading network intelligence data:', err);
				showToast('Failed to load transaction networks.');
			}
		}

		function updateActiveNetworkBadge(net) {
			const badge = document.getElementById('active-network-name-badge');
			if (badge && net) {
				badge.textContent = \`\${net.id} (\${net.name})\`;
			}
		}

		// 3. Natural 2D Force-Directed Simulation
		function run2DForceSimulation(nodes, links, width, height, iterations = 80) {
			const count = nodes.length;
			if (count === 0) return {};

			const centerX = width / 2;
			const centerY = height / 2;
			const initialRadius = Math.min(width, height) * 0.32;

			// Initialize positions in a loose dispersion
			const posMap = {};
			nodes.forEach((n, idx) => {
				const angle = (2 * Math.PI * idx) / count + (idx % 2 === 0 ? 0.2 : -0.2);
				const r = initialRadius + ((idx % 3) - 1) * 25;
				posMap[n.id] = {
					id: n.id,
					x: Math.round(centerX + Math.cos(angle) * r),
					y: Math.round(centerY + Math.sin(angle) * r),
					vx: 0,
					vy: 0
				};
			});

			const kRepulsion = 7200;
			const kSpring = 0.045;
			const restLength = 115;
			const kGravity = 0.015;
			const damping = 0.65;

			for (let iter = 0; iter < iterations; iter++) {
				// 1. Repulsion between all node pairs
				for (let i = 0; i < count; i++) {
					const pA = posMap[nodes[i].id];
					for (let j = i + 1; j < count; j++) {
						const pB = posMap[nodes[j].id];
						const dx = pA.x - pB.x;
						const dy = pA.y - pB.y;
						const distSq = dx * dx + dy * dy + 0.1;
						const dist = Math.sqrt(distSq);
						const force = kRepulsion / distSq;
						const fx = (dx / dist) * force;
						const fy = (dy / dist) * force;
						pA.vx += fx;
						pA.vy += fy;
						pB.vx -= fx;
						pB.vy -= fy;
					}
				}

				// 2. Spring attraction strictly along real transaction edges
				links.forEach(link => {
					const sId = link.source_id || link.source;
					const tId = link.target_id || link.target;
					const pA = posMap[sId];
					const pB = posMap[tId];
					if (!pA || !pB) return;

					const dx = pA.x - pB.x;
					const dy = pA.y - pB.y;
					const dist = Math.sqrt(dx * dx + dy * dy) + 0.1;
					const displacement = dist - restLength;
					const force = displacement * kSpring;
					const fx = (dx / dist) * force;
					const fy = (dy / dist) * force;
					pA.vx -= fx;
					pA.vy -= fy;
					pB.vx += fx;
					pB.vy += fy;
				});

				// 3. Center gravity and position integration
				nodes.forEach(n => {
					const p = posMap[n.id];
					p.vx += (centerX - p.x) * kGravity;
					p.vy += (centerY - p.y) * kGravity;
					p.vx *= damping;
					p.vy *= damping;
					p.x += Math.max(-18, Math.min(18, p.vx));
					p.y += Math.max(-18, Math.min(18, p.vy));

					p.x = Math.max(50, Math.min(width - 50, p.x));
					p.y = Math.max(50, Math.min(height - 50, p.y));
				});
			}

			return posMap;
		}

		// 4. Update Node Position and Connected Links in DOM without rebuilding SVG
		function updateNodePositionInDOM(nodeId, newPos, svgElementId = 'network-graph-svg') {
			const nodeGroup = document.getElementById(\`\${svgElementId}-node-group-\${nodeId}\`);
			if (nodeGroup) {
				nodeGroup.setAttribute('transform', \`translate(\${newPos.x}, \${newPos.y})\`);
			}

			const net = networksDb[currentlyRenderedNetworkId];
			if (!net) return;
			const netKey = \`\${currentlyRenderedNetworkId}_\${net.graphNodes.length}_\${graphState.canvasWidth}_\${graphState.canvasHeight}\`;
			const posMap = graphState.nodePositions[netKey] || {};

			// Update all directed links connected to this node
			const links = net.graphLinks || [];
			links.forEach((link, idx) => {
				const sId = link.source_id || link.source;
				const tId = link.target_id || link.target;
				if (sId !== nodeId && tId !== nodeId) return;

				const pS = posMap[sId];
				const pT = posMap[tId];
				if (!pS || !pT) return;

				const line = document.getElementById(\`\${svgElementId}-link-\${idx}\`);
				if (!line) return;

				const dx = pT.x - pS.x;
				const dy = pT.y - pS.y;
				const dist = Math.sqrt(dx * dx + dy * dy) || 1;
				const targetRadius = 13;
				const endX = pT.x - (dx / dist) * targetRadius;
				const endY = pT.y - (dy / dist) * targetRadius;

				line.setAttribute('x1', pS.x);
				line.setAttribute('y1', pS.y);
				line.setAttribute('x2', endX);
				line.setAttribute('y2', endY);

				// Update amount badge if present
				const badge = document.getElementById(\`\${svgElementId}-amount-badge-\${idx}\`);
				if (badge) {
					const midX = (pS.x + endX) / 2;
					const midY = (pS.y + endY) / 2;
					const rect = badge.querySelector('rect');
					const text = badge.querySelector('text');
					if (rect && text) {
						const amtText = text.textContent;
						const textWidth = Math.max(34, amtText.length * 6.2);
						rect.setAttribute('x', midX - textWidth / 2);
						rect.setAttribute('y', midY - 7);
						text.setAttribute('x', midX);
						text.setAttribute('y', midY + 3);
					}
				}
			});
		}

		// 5. Render Network Graph
		function renderNetworkGraph(networkId, svgElementId = 'network-graph-svg') {
			const data = networksDb[networkId];
			if (!data || !data.graphNodes || data.graphNodes.length === 0) return;

			const svg = document.getElementById(svgElementId);
			if (!svg) return;

			svg.innerHTML = '';
			const isMainVisualizer = (svgElementId === 'network-graph-svg');
			const wrapper = document.getElementById('graph-viewport-wrapper');
			const width = isMainVisualizer ? (wrapper ? wrapper.clientWidth || 1000 : 1000) : 400;
			const height = isMainVisualizer ? (wrapper ? wrapper.clientHeight || 500 : 500) : 180;
			svg.setAttribute('viewBox', \`0 0 \${width} \${height}\`);
			graphState.canvasWidth = width;
			graphState.canvasHeight = height;

			let activeNodes = data.graphNodes.slice();
			let activeLinks = data.graphLinks.slice();

			// Auto-select primary or highest risk account if not set
			if (isMainVisualizer) {
				if (!graphState.selectedNodeId || !activeNodes.some(n => n.id === graphState.selectedNodeId)) {
					const sorted = [...activeNodes].sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0));
					graphState.selectedNodeId = sorted[0].id;
				}
			}

			// Suspicious only filter
			if (isMainVisualizer && graphState.suspiciousOnly) {
				const suspNodeIds = new Set(
					activeNodes
						.filter(n => ['Flagged', 'Critical', 'Under Review', 'Blocked'].includes(n.status) || n.risk_score >= 70)
						.map(n => n.id)
				);
				activeNodes = activeNodes.filter(n => suspNodeIds.has(n.id));
				const activeSet = new Set(activeNodes.map(n => n.id));
				activeLinks = activeLinks.filter(l => activeSet.has(l.source_id || l.source) && activeSet.has(l.target_id || l.target));
			}

			// Hop depth filter from selected node
			if (isMainVisualizer && graphState.hopDepth > 0 && graphState.selectedNodeId) {
				const reachable = new Set([graphState.selectedNodeId]);
				let currentFrontier = new Set([graphState.selectedNodeId]);
				for (let h = 0; h < graphState.hopDepth; h++) {
					const nextFrontier = new Set();
					data.graphLinks.forEach(l => {
						const sId = l.source_id || l.source;
						const tId = l.target_id || l.target;
						if (currentFrontier.has(sId) && !reachable.has(tId)) {
							reachable.add(tId);
							nextFrontier.add(tId);
						}
						if (currentFrontier.has(tId) && !reachable.has(sId)) {
							reachable.add(sId);
							nextFrontier.add(sId);
						}
					});
					currentFrontier = nextFrontier;
				}
				activeNodes = activeNodes.filter(n => reachable.has(n.id));
				const activeSet = new Set(activeNodes.map(n => n.id));
				activeLinks = activeLinks.filter(l => activeSet.has(l.source_id || l.source) && activeSet.has(l.target_id || l.target));
			}

			// Ensure all visible nodes strictly belong to real PostgreSQL transactions
			const connectedNodeIds = new Set();
			activeLinks.forEach(l => {
				connectedNodeIds.add(l.source_id || l.source);
				connectedNodeIds.add(l.target_id || l.target);
			});
			if (connectedNodeIds.size > 0) {
				activeNodes = activeNodes.filter(n => connectedNodeIds.has(n.id));
			}

			if (activeNodes.length === 0) {
				activeNodes = data.graphNodes.slice(0, 3);
			}

			// Calculate 2D Force Layout Positions
			let posMap;
			const netKey = \`\${networkId}_\${activeNodes.length}_\${width}_\${height}\`;
			if (isMainVisualizer && graphState.nodePositions[netKey]) {
				posMap = graphState.nodePositions[netKey];
			} else {
				posMap = run2DForceSimulation(activeNodes, activeLinks, width, height, isMainVisualizer ? 80 : 45);
				if (isMainVisualizer) {
					graphState.nodePositions[netKey] = posMap;
				}
			}

			// Arrowhead markers & glow filters attached to nodes
			const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
			defs.innerHTML = \`
				<marker id="arrowhead" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
					<path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#316BF3" />
				</marker>
				<marker id="arrowhead-flagged" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
					<path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#EF4444" />
				</marker>
				<marker id="arrowhead-selected" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
					<path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#F59E0B" />
				</marker>
				<filter id="suspicious-glow" x="-50%" y="-50%" width="200%" height="200%">
					<feDropShadow dx="0" dy="0" stdDeviation="4.5" flood-color="#ef4444" flood-opacity="0.85" />
				</filter>
				<filter id="review-glow" x="-50%" y="-50%" width="200%" height="200%">
					<feDropShadow dx="0" dy="0" stdDeviation="3.5" flood-color="#f97316" flood-opacity="0.75" />
				</filter>
				<filter id="node-glow" x="-20%" y="-20%" width="140%" height="140%">
					<feGaussianBlur stdDeviation="3" result="blur" />
					<feComposite in="SourceGraphic" in2="blur" operator="over" />
				</filter>
			\`;
			svg.appendChild(defs);

			// Viewport Transform Group for Pan & Zoom
			const viewportGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
			viewportGroup.setAttribute('id', \`\${svgElementId}-viewport\`);
			if (isMainVisualizer) {
				viewportGroup.setAttribute('transform', \`translate(\${graphState.panX}, \${graphState.panY}) scale(\${graphState.zoom})\`);
			}
			svg.appendChild(viewportGroup);

			// 1. Draw Real Directed Edges
			const linksGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
			linksGroup.setAttribute('class', 'links-layer pointer-events-none');
			viewportGroup.appendChild(linksGroup);

			activeLinks.forEach((link, idx) => {
				const sId = link.source_id || link.source;
				const tId = link.target_id || link.target;
				const pS = posMap[sId];
				const pT = posMap[tId];
				if (!pS || !pT) return;

				const isConnectedToSelected = (sId === graphState.selectedNodeId || tId === graphState.selectedNodeId);
				const isHighRisk = (link.amount >= 25000);

				// Compute offset vector so arrowhead rests outside node
				const dx = pT.x - pS.x;
				const dy = pT.y - pS.y;
				const dist = Math.sqrt(dx * dx + dy * dy) || 1;
				const targetRadius = 13;
				const endX = pT.x - (dx / dist) * targetRadius;
				const endY = pT.y - (dy / dist) * targetRadius;

				const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
				line.setAttribute('id', \`\${svgElementId}-link-\${idx}\`);
				line.setAttribute('data-source', sId);
				line.setAttribute('data-target', tId);
				line.setAttribute('x1', pS.x);
				line.setAttribute('y1', pS.y);
				line.setAttribute('x2', endX);
				line.setAttribute('y2', endY);
				line.setAttribute('stroke', isConnectedToSelected ? '#f59e0b' : (isHighRisk ? '#ef4444' : '#316bf3'));
				line.setAttribute('stroke-width', isConnectedToSelected ? '2' : (isHighRisk ? '1.8' : '1.3'));
				line.setAttribute('stroke-opacity', isConnectedToSelected ? '0.95' : '0.65');

				if (graphState.showDirections) {
					line.setAttribute('class', 'flow-line');
					line.setAttribute('marker-end', isConnectedToSelected ? 'url(#arrowhead-selected)' : (isHighRisk ? 'url(#arrowhead-flagged)' : 'url(#arrowhead)'));
				}
				linksGroup.appendChild(line);

				// Edge Amount Badge
				if (isMainVisualizer && (graphState.showAmounts || isConnectedToSelected)) {
					const midX = (pS.x + endX) / 2;
					const midY = (pS.y + endY) / 2;
					const amountG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
					amountG.setAttribute('id', \`\${svgElementId}-amount-badge-\${idx}\`);
					amountG.setAttribute('data-link-index', idx);
					amountG.setAttribute('class', 'edge-amount-badge pointer-events-none');
					
					const amtText = link.amount_formatted || \`₹\${link.amount.toLocaleString('en-IN')}\`;
					const textWidth = Math.max(34, amtText.length * 6.2);
					
					const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
					rect.setAttribute('x', midX - textWidth / 2);
					rect.setAttribute('y', midY - 7);
					rect.setAttribute('width', textWidth);
					rect.setAttribute('height', 14);
					rect.setAttribute('rx', 3);
					rect.setAttribute('fill', '#071324');
					rect.setAttribute('stroke', isConnectedToSelected ? '#f59e0b' : '#1e2e4a');
					rect.setAttribute('stroke-width', '0.8');
					amountG.appendChild(rect);

					const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
					text.setAttribute('x', midX);
					text.setAttribute('y', midY + 3);
					text.setAttribute('fill', isConnectedToSelected ? '#fbbf24' : '#94a3b8');
					text.setAttribute('font-size', '8');
					text.setAttribute('font-family', 'monospace');
					text.setAttribute('font-weight', 'bold');
					text.setAttribute('text-anchor', 'middle');
					text.textContent = amtText;
					amountG.appendChild(text);

					linksGroup.appendChild(amountG);
				}
			});

			// 2. Draw Clean Nodes with <g transform="translate(x, y)">
			const nodesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
			nodesGroup.setAttribute('class', 'nodes-layer');
			viewportGroup.appendChild(nodesGroup);

			activeNodes.forEach(node => {
				const pos = posMap[node.id];
				if (!pos) return;

				const isSelected = (isMainVisualizer && node.id === graphState.selectedNodeId);
				const isBusiness = node.is_business || (node.account_type === 'Current');
				const isHighRisk = (node.risk_score >= 80 || ['Flagged', 'Critical', 'Blocked'].includes(node.status));
				const isUnderReview = (node.risk_score >= 60 && !isHighRisk);
				const nodeRadius = isHighRisk ? 13 : (isUnderReview ? 11.5 : 10);

				const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
				g.setAttribute('class', 'cursor-grab group/node select-none');
				g.setAttribute('id', \`\${svgElementId}-node-group-\${node.id}\`);
				g.setAttribute('data-node-id', node.id);
				g.setAttribute('transform', \`translate(\${pos.x}, \${pos.y})\`);

				// Selection Halo Ring (Active Account Selection)
				if (isSelected) {
					const selRing = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
					selRing.setAttribute('cx', 0);
					selRing.setAttribute('cy', 0);
					selRing.setAttribute('r', isBusiness ? 18 : (nodeRadius + 6));
					selRing.setAttribute('fill', 'none');
					selRing.setAttribute('stroke', '#f59e0b');
					selRing.setAttribute('stroke-width', '2');
					selRing.setAttribute('stroke-dasharray', '3,2');
					selRing.setAttribute('filter', 'url(#node-glow)');
					g.appendChild(selRing);
				}

				// Suspicious/Mule Account: attached outer glowing halo ring (strictly concentric on the node, no detach)
				if (isHighRisk) {
					const outerHalo = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
					outerHalo.setAttribute('cx', 0);
					outerHalo.setAttribute('cy', 0);
					outerHalo.setAttribute('r', nodeRadius + 4);
					outerHalo.setAttribute('fill', 'none');
					outerHalo.setAttribute('stroke', '#ef4444');
					outerHalo.setAttribute('stroke-width', '1.2');
					outerHalo.setAttribute('stroke-opacity', '0.75');
					outerHalo.setAttribute('filter', 'url(#suspicious-glow)');
					g.appendChild(outerHalo);
				} else if (isUnderReview) {
					const reviewHalo = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
					reviewHalo.setAttribute('cx', 0);
					reviewHalo.setAttribute('cy', 0);
					reviewHalo.setAttribute('r', nodeRadius + 3);
					reviewHalo.setAttribute('fill', 'none');
					reviewHalo.setAttribute('stroke', '#f97316');
					reviewHalo.setAttribute('stroke-width', '1.0');
					reviewHalo.setAttribute('stroke-opacity', '0.6');
					reviewHalo.setAttribute('filter', 'url(#review-glow)');
					g.appendChild(reviewHalo);
				}

				// Color coding according to visual state
				let fillColor = '#0f172a';
				let strokeColor = '#38bdf8';

				if (node.status === 'Blocked') {
					fillColor = '#1e1b4b';
					strokeColor = '#64748b';
				} else if (isHighRisk) {
					fillColor = '#450a0a';
					strokeColor = '#ef4444';
				} else if (isUnderReview) {
					fillColor = '#431407';
					strokeColor = '#f97316';
				} else if (isBusiness) {
					fillColor = '#422006';
					strokeColor = '#eab308';
				}

				if (isBusiness) {
					const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
					rect.setAttribute('x', -11);
					rect.setAttribute('y', -10);
					rect.setAttribute('width', 22);
					rect.setAttribute('height', 20);
					rect.setAttribute('rx', 4);
					rect.setAttribute('fill', fillColor);
					rect.setAttribute('stroke', strokeColor);
					rect.setAttribute('stroke-width', isSelected ? '2.5' : '1.8');
					g.appendChild(rect);

					const bizText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
					bizText.setAttribute('x', 0);
					bizText.setAttribute('y', 3.5);
					bizText.setAttribute('fill', '#fde047');
					bizText.setAttribute('font-size', '8');
					bizText.setAttribute('font-family', 'monospace');
					bizText.setAttribute('font-weight', 'bold');
					bizText.setAttribute('text-anchor', 'middle');
					bizText.textContent = 'BIZ';
					g.appendChild(bizText);
				} else {
					const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
					circle.setAttribute('cx', 0);
					circle.setAttribute('cy', 0);
					circle.setAttribute('r', nodeRadius);
					circle.setAttribute('fill', fillColor);
					circle.setAttribute('stroke', strokeColor);
					circle.setAttribute('stroke-width', isSelected ? '2.5' : (isHighRisk ? '2' : '1.5'));
					if (isHighRisk) {
						circle.setAttribute('filter', 'url(#suspicious-glow)');
					} else if (isUnderReview) {
						circle.setAttribute('filter', 'url(#review-glow)');
					}
					g.appendChild(circle);

					const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
					dot.setAttribute('cx', 0);
					dot.setAttribute('cy', 0);
					dot.setAttribute('r', isHighRisk ? 3.5 : 2.5);
					dot.setAttribute('fill', isHighRisk ? '#fca5a5' : (isUnderReview ? '#fdba74' : '#7dd3fc'));
					g.appendChild(dot);
				}

				// Intelligent Clean Labels
				if (isMainVisualizer) {
					const labelGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
					labelGroup.setAttribute('class', 'node-label-group pointer-events-none');
					if (!graphState.showLabels) labelGroup.style.display = 'none';

					const cleanName = (node.customer_name || node.label || '').length > 15
						? (node.customer_name || node.label).slice(0, 14) + '…'
						: (node.customer_name || node.label);

					const pillY = isBusiness ? 13 : nodeRadius + 4;
					const pillWidth = Math.max(cleanName.length * 6.2 + 8, 64);

					const labelPill = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
					labelPill.setAttribute('x', -pillWidth / 2);
					labelPill.setAttribute('y', pillY);
					labelPill.setAttribute('width', pillWidth);
					labelPill.setAttribute('height', 23);
					labelPill.setAttribute('rx', 3);
					labelPill.setAttribute('fill', '#071324');
					labelPill.setAttribute('fill-opacity', '0.88');
					labelPill.setAttribute('stroke', isSelected ? '#f59e0b' : '#1e2e4a');
					labelPill.setAttribute('stroke-width', isSelected ? '1' : '0.6');
					labelGroup.appendChild(labelPill);

					const idLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
					idLabel.setAttribute('x', 0);
					idLabel.setAttribute('y', pillY + 10);
					idLabel.setAttribute('fill', isSelected ? '#fbbf24' : '#e2e8f0');
					idLabel.setAttribute('font-size', '8.5');
					idLabel.setAttribute('font-family', 'monospace');
					idLabel.setAttribute('font-weight', isSelected ? 'bold' : '600');
					idLabel.setAttribute('text-anchor', 'middle');
					idLabel.textContent = node.id;
					labelGroup.appendChild(idLabel);

					const nameLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
					nameLabel.setAttribute('x', 0);
					nameLabel.setAttribute('y', pillY + 19);
					nameLabel.setAttribute('fill', isSelected ? '#ffffff' : '#94a3b8');
					nameLabel.setAttribute('font-size', '8');
					nameLabel.setAttribute('font-weight', '500');
					nameLabel.setAttribute('text-anchor', 'middle');
					nameLabel.textContent = cleanName;
					labelGroup.appendChild(nameLabel);

					g.appendChild(labelGroup);
				}

				// Interactive Click & Drag Handlers for Nodes
				if (isMainVisualizer) {
					g.onmousedown = (e) => {
						if (e.button !== 0) return;
						e.stopPropagation();
						e.preventDefault();
						graphState.isDraggingNode = true;
						graphState.draggedNodeId = node.id;
						graphState.draggedPos = pos;
						graphState.dragStartPointer = { x: e.clientX, y: e.clientY };
						graphState.hasMovedNode = false;
						document.body.classList.add('is-node-dragging');
					};
				} else {
					g.onclick = (e) => {
						e.stopPropagation();
						selectAccountNode(node.id, svgElementId);
					};
				}

				nodesGroup.appendChild(g);
			});

			// Populate Selected Account Dossier for currently selected node
			if (isMainVisualizer && graphState.selectedNodeId) {
				showNodeDetails(graphState.selectedNodeId, svgElementId);
			}
		}

		// 6. Global Canvas & Drag Interaction Handlers (Initialized once)
		function initGraphInteractionHandlers() {
			const wrap = document.getElementById('graph-viewport-wrapper');
			if (!wrap) return;

			// 1. Canvas Panning Start on empty background
			wrap.addEventListener('mousedown', (e) => {
				if (e.button !== 0) return;
				if (e.target.closest('.group\\/node') || e.target.closest('[data-node-id]')) return;
				graphState.isDraggingCanvas = true;
				graphState.dragStart = { x: e.clientX - graphState.panX, y: e.clientY - graphState.panY };
				document.body.classList.add('is-canvas-panning');
				wrap.classList.add('is-panning');
			});

			// 2. Window MouseMove for silky-smooth node drag & canvas pan
			window.addEventListener('mousemove', (e) => {
				if (graphState.isDraggingNode && graphState.draggedPos) {
					const moveDist = Math.hypot(e.clientX - graphState.dragStartPointer.x, e.clientY - graphState.dragStartPointer.y);
					if (moveDist > 3) {
						graphState.hasMovedNode = true;
					}
					const svg = document.getElementById('network-graph-svg');
					const vp = document.getElementById('network-graph-svg-viewport');
					if (!svg || !vp) return;
					const pt = svg.createSVGPoint();
					pt.x = e.clientX;
					pt.y = e.clientY;
					const svgP = pt.matrixTransform(vp.getScreenCTM().inverse());
					graphState.draggedPos.x = Math.round(svgP.x);
					graphState.draggedPos.y = Math.round(svgP.y);
					updateNodePositionInDOM(graphState.draggedNodeId, graphState.draggedPos, 'network-graph-svg');
				} else if (graphState.isDraggingCanvas) {
					graphState.panX = e.clientX - graphState.dragStart.x;
					graphState.panY = e.clientY - graphState.dragStart.y;
					applyGraphViewportTransform();
				}
			});

			// 3. Window MouseUp
			window.addEventListener('mouseup', () => {
				if (graphState.isDraggingNode) {
					const clickedNodeId = graphState.draggedNodeId;
					const wasDrag = graphState.hasMovedNode;
					graphState.isDraggingNode = false;
					graphState.draggedPos = null;
					graphState.draggedNodeId = null;
					document.body.classList.remove('is-node-dragging');
					if (!wasDrag && clickedNodeId) {
						selectAccountNode(clickedNodeId, 'network-graph-svg');
					}
				}
				if (graphState.isDraggingCanvas) {
					graphState.isDraggingCanvas = false;
					document.body.classList.remove('is-canvas-panning');
					const wrapEl = document.getElementById('graph-viewport-wrapper');
					if (wrapEl) wrapEl.classList.remove('is-panning');
				}
			});

			// 4. Mouse wheel zoom restricted to graph wrapper (does not block page scroll outside)
			wrap.addEventListener('wheel', (e) => {
				e.preventDefault();
				const zoomFactor = (e.deltaY < 0) ? 1.12 : 0.89;
				const nextZoom = Math.min(3.5, Math.max(0.3, graphState.zoom * zoomFactor));
				const rect = wrap.getBoundingClientRect();
				const mouseX = e.clientX - rect.left;
				const mouseY = e.clientY - rect.top;
				graphState.panX = mouseX - (mouseX - graphState.panX) * (nextZoom / graphState.zoom);
				graphState.panY = mouseY - (mouseY - graphState.panY) * (nextZoom / graphState.zoom);
				graphState.zoom = nextZoom;
				applyGraphViewportTransform();
			}, { passive: false });
		}

		function applyGraphViewportTransform() {
			const vp = document.getElementById('network-graph-svg-viewport');
			if (vp) {
				vp.setAttribute('transform', \`translate(\${graphState.panX}, \${graphState.panY}) scale(\${graphState.zoom})\`);
			}
		}

		// 7. Account Selection & Centering
		function selectAccountNode(nodeId, svgElementId = 'network-graph-svg') {
			graphState.selectedNodeId = nodeId;
			if (currentlyRenderedNetworkId) {
				renderNetworkGraph(currentlyRenderedNetworkId, svgElementId);
			}
			showNodeDetails(nodeId, svgElementId);
		}

		function centerGraphOnAccountNode(nodeId) {
			const net = networksDb[currentlyRenderedNetworkId];
			if (!net) return;
			const netKey = \`\${net.id}_\${net.graphNodes.length}_\${graphState.canvasWidth}_\${graphState.canvasHeight}\`;
			const posMap = graphState.nodePositions[netKey];
			if (!posMap || !posMap[nodeId]) return;

			const pos = posMap[nodeId];
			const wrapper = document.getElementById('graph-viewport-wrapper');
			const w = wrapper ? wrapper.clientWidth : 1000;
			const h = wrapper ? wrapper.clientHeight : 500;

			if (graphState.zoom < 0.95) graphState.zoom = 1.05;
			graphState.panX = (w / 2) - pos.x * graphState.zoom;
			graphState.panY = (h / 2) - pos.y * graphState.zoom;
			applyGraphViewportTransform();
		}

		// 8. Comprehensive Selected Account Dossier (19 PostgreSQL fields)
		function showNodeDetails(nodeId, svgElementId = 'network-graph-svg') {
			const dossierContainer = document.getElementById('selected-account-dossier');
			if (!dossierContainer) return;

			const currentNet = networksDb[currentlyRenderedNetworkId];
			if (!currentNet) return;

			let node = currentNet.graphNodes.find(n => n.id === nodeId);
			let parentNet = currentNet;

			if (!node) {
				for (const [netId, net] of Object.entries(networksDb)) {
					const found = (net.graphNodes || []).find(n => n.id === nodeId);
					if (found) {
						node = found;
						parentNet = net;
						break;
					}
				}
			}
			if (!node) return;

			const isFlagged = (node.status === 'Flagged' || node.status === 'Critical' || node.risk_score >= 80);
			const isUnderReview = (node.status === 'Under Review' || (node.risk_score >= 60 && node.risk_score < 80));
			const isBusiness = node.is_business || (node.account_type === 'Current');

			let badgeColor = "bg-blue-500/20 text-blue-300 border-blue-500/30";
			if (node.status === 'Blocked') badgeColor = "bg-slate-700/60 text-slate-300 border-slate-600";
			else if (isFlagged) badgeColor = "bg-red-500/20 text-red-300 border-red-500/40";
			else if (isUnderReview) badgeColor = "bg-orange-500/20 text-orange-300 border-orange-500/40";

			const muleStatusText = isFlagged 
				? 'Flagged Mule Account' 
				: (isUnderReview ? 'Under Review (Suspicious)' : 'Legitimate Retail');
			const muleStatusBadge = isFlagged 
				? 'bg-red-500/20 text-red-300 border-red-500/40' 
				: (isUnderReview ? 'bg-orange-500/20 text-orange-300 border-orange-500/40' : 'bg-green-500/20 text-green-300 border-green-500/40');

			const customerType = isBusiness ? 'Small Business / Merchant' : 'Individual Retail Customer';
			const city = node.city || 'India Retail Branch';
			const riskScore = node.risk_score || 20;

			// Connected accounts rows
			const connectedAccounts = node.connected_accounts || [];
			const connectedRows = connectedAccounts.slice(0, 8).map(cp => {
				const isCpFlagged = (cp.status === 'Flagged' || cp.status === 'Critical');
				const cpBadge = isCpFlagged 
					? 'bg-red-500/20 text-red-400 border-red-500/30'
					: 'bg-slate-800 text-slate-300 border-slate-700';

				return \`
					<tr class="hover:bg-[#122543] transition-colors cursor-pointer" onclick="selectAndFocusAccount('\${cp.account_id}')">
						<td class="py-2 px-3 font-mono text-[11.5px] text-sky-400 font-bold hover:underline">\${cp.account_id}</td>
						<td class="py-2 px-3 font-medium text-[11.5px] text-white truncate max-w-[140px]">\${cp.customer_name}</td>
						<td class="py-2 px-3 text-[11px] text-slate-300">\${cp.account_type}\${cp.is_business ? ' (Biz)' : ''}</td>
						<td class="py-2 px-3 text-[10.5px] text-slate-400">\${cp.direction}</td>
						<td class="py-2 px-3 font-mono text-[11.5px] text-right font-semibold text-white">\${cp.total_amount_formatted}</td>
						<td class="py-2 px-3 font-mono text-[11px] text-right text-slate-400">\${cp.transaction_count}</td>
						<td class="py-2 px-3 text-center">
							<span class="px-2 py-0.5 rounded text-[10px] font-mono border \${cpBadge}">\${cp.status}</span>
						</td>
						<td class="py-2 px-3 text-right">
							<button class="text-[11px] font-mono text-sky-400 hover:text-white hover:underline focus:outline-none" onclick="event.stopPropagation(); selectAndFocusAccount('\${cp.account_id}')">
								Focus →
							</button>
						</td>
					</tr>
				\`;
			}).join('');

			// Recent transactions rows
			const recentTransactions = node.recent_transactions || [];
			const recentTxRows = recentTransactions.slice(0, 8).map(tx => {
				const isIn = tx.is_inbound || (tx.direction === 'INBOUND');
				const dirBadge = isIn
					? '<span class="text-green-400 font-bold text-[10.5px]">↓ INBOUND</span>'
					: '<span class="text-orange-400 font-bold text-[10.5px]">↑ OUTBOUND</span>';

				return \`
					<tr class="hover:bg-[#122543] transition-colors">
						<td class="py-2 px-3 font-mono text-[11px] text-slate-300">\${tx.id}</td>
						<td class="py-2 px-3 text-[10.5px] text-slate-400 whitespace-nowrap">\${(tx.timestamp || '').split('T')[0] || tx.timestamp}</td>
						<td class="py-2 px-3 text-[11px] text-slate-300">\${tx.type || 'UPI'}</td>
						<td class="py-2 px-3 text-center">\${dirBadge}</td>
						<td class="py-2 px-3 font-mono text-[11.5px] text-right font-bold text-white">\${tx.amount_formatted}</td>
						<td class="py-2 px-3 font-mono text-[11px] text-sky-400 hover:underline cursor-pointer" onclick="selectAndFocusAccount('\${tx.counterparty_id}')">\${tx.counterparty_id}</td>
						<td class="py-2 px-3 text-[11px] text-slate-400 truncate max-w-[120px]">\${tx.counterparty_name}</td>
					</tr>
				\`;
			}).join('');

			// Behavioral risk reasons
			const reasonsHtml = (node.suspicion_reasons || []).map(r => \`
				<div class="flex items-start gap-1.5 text-[11.5px] \${isFlagged ? 'text-red-300' : 'text-slate-300'}">
					<span class="text-red-400 font-bold leading-none mt-0.5">•</span>
					<span>\${r}</span>
				</div>
			\`).join('');

			const suspiciousConnected = (connectedAccounts || []).filter(c => c.risk_score >= 70 || ['Flagged', 'Blocked', 'Critical'].includes(c.status));
			const suspiciousBadges = suspiciousConnected.map(sc => \`
				<button class="px-2 py-0.5 rounded bg-red-950/60 hover:bg-red-900 border border-red-500/40 text-red-300 text-[10.5px] font-mono font-bold transition-colors inline-flex items-center gap-1" onclick="selectAndFocusAccount('\${sc.account_id}')">
					<span>\${sc.account_id} (\${sc.customer_name})</span>
					<span class="text-[9px]">→</span>
				</button>
			\`).join('');

			const inCount = node.in_degree || 0;
			const outCount = node.out_degree || 0;
			const totalTxCount = inCount + outCount;

			dossierContainer.innerHTML = \`
				<!-- Top Header Banner -->
				<div class="flex flex-col lg:flex-row lg:items-center justify-between pb-3 border-b border-[#1e2e4a] gap-3">
					<div>
						<div class="flex items-center gap-2.5 flex-wrap">
							<h4 class="font-headline-md text-[17px] text-white font-extrabold tracking-tight">\${node.customer_name}</h4>
							<span class="font-mono text-[12px] text-sky-400 font-bold bg-sky-950/60 px-2.5 py-0.5 rounded border border-sky-800 select-all">\${node.id}</span>
							<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold border \${badgeColor}">\${node.status}</span>
							<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold border \${muleStatusBadge}">\${muleStatusText}</span>
						</div>
						<div class="flex items-center gap-3.5 text-[11px] text-slate-400 mt-1 flex-wrap">
							<span>Customer Type: <strong class="text-slate-200">\${customerType}</strong></span>
							<span>Account Type: <strong class="text-slate-200">\${node.account_type || 'Savings'}</strong></span>
							<span>City: <strong class="text-slate-200">\${city}</strong></span>
							<span>Network: <strong class="text-sky-300 font-mono">\${parentNet.id} (\${parentNet.name})</strong></span>
						</div>
					</div>

					<div class="flex items-center gap-3 self-start lg:self-center">
						<div class="flex flex-col items-end">
							<span class="font-mono-technical text-[9.5px] text-slate-400 uppercase font-semibold">Mule Risk Score</span>
							<span class="font-mono text-[18px] font-extrabold \${isFlagged ? 'text-red-400' : (isUnderReview ? 'text-orange-400' : 'text-blue-400')}">\${riskScore} / 100</span>
						</div>
					</div>
				</div>

				<!-- Behavioral Suspicion Triggers Banner -->
				\${reasonsHtml ? \`
					<div class="bg-red-950/30 border border-red-900/50 rounded-lg p-3 space-y-1">
						<div class="font-mono-technical text-[10px] text-red-400 uppercase font-bold tracking-wider flex items-center gap-1.5">
							<span class="material-symbols-outlined text-[14px]">warning</span>
							Relevant Behavioral & Risk Indicators:
						</div>
						<div class="grid grid-cols-1 md:grid-cols-2 gap-1.5 pt-0.5">
							\${reasonsHtml}
						</div>
					</div>
				\` : ''}

				<!-- 6 KPI Metrics Grid -->
				<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
					<div class="bg-[#0b192c] border border-[#1e2e4a] rounded-lg p-2.5 text-left">
						<span class="font-mono-technical text-[9px] text-slate-400 uppercase font-semibold block">Balance</span>
						<span class="font-mono text-[14px] font-bold text-white">\${node.balance_formatted || '₹0'}</span>
					</div>
					<div class="bg-[#0b192c] border border-[#1e2e4a] rounded-lg p-2.5 text-left">
						<span class="font-mono-technical text-[9px] text-slate-400 uppercase font-semibold block">Total Inflow</span>
						<span class="font-mono text-[14px] font-bold text-green-400">\${node.total_incoming_formatted || '₹0'}</span>
					</div>
					<div class="bg-[#0b192c] border border-[#1e2e4a] rounded-lg p-2.5 text-left">
						<span class="font-mono-technical text-[9px] text-slate-400 uppercase font-semibold block">Total Outflow</span>
						<span class="font-mono text-[14px] font-bold text-orange-400">\${node.total_outgoing_formatted || '₹0'}</span>
					</div>
					<div class="bg-[#0b192c] border border-[#1e2e4a] rounded-lg p-2.5 text-left">
						<span class="font-mono-technical text-[9px] text-slate-400 uppercase font-semibold block">Total Transactions</span>
						<span class="font-mono text-[14px] font-bold text-white">\${totalTxCount} <span class="text-[10px] text-slate-400 font-normal">(\${inCount} in / \${outCount} out)</span></span>
					</div>
					<div class="bg-[#0b192c] border border-[#1e2e4a] rounded-lg p-2.5 text-left">
						<span class="font-mono-technical text-[9px] text-slate-400 uppercase font-semibold block">Unique Counterparties</span>
						<span class="font-mono text-[14px] font-bold text-sky-400">\${node.connected_accounts_count || connectedAccounts.length}</span>
					</div>
					<div class="bg-[#0b192c] border border-[#1e2e4a] rounded-lg p-2.5 text-left">
						<span class="font-mono-technical text-[9px] text-slate-400 uppercase font-semibold block">Suspicious Connected</span>
						<span class="font-mono text-[14px] font-bold \${suspiciousConnected.length > 0 ? 'text-red-400' : 'text-slate-400'}">\${suspiciousConnected.length} accounts</span>
					</div>
				</div>

				<!-- Suspicious Connected Badges -->
				\${suspiciousBadges ? \`
					<div class="flex items-center gap-2 flex-wrap pt-0.5">
						<span class="font-mono-technical text-[10px] text-red-400 uppercase font-bold">Suspicious Counterparties:</span>
						\${suspiciousBadges}
					</div>
				\` : ''}

				<!-- Dual Tables: Connected Accounts & Recent Transactions -->
				<div class="grid grid-cols-1 xl:grid-cols-2 gap-4 pt-2">
					<!-- Connected Accounts Table -->
					<div class="bg-[#0b192c] border border-[#1e2e4a] rounded-lg p-3">
						<div class="flex items-center justify-between pb-2 border-b border-[#1e2e4a]">
							<span class="font-mono-technical text-[10.5px] text-sky-400 uppercase font-bold">Direct Connected Counterparties (\${connectedAccounts.length})</span>
							<span class="text-[10px] text-slate-400">Click any row to focus in graph</span>
						</div>
						<div class="overflow-x-auto max-h-[220px] overflow-y-auto mt-1">
							<table class="w-full border-collapse text-left">
								<thead>
									<tr class="border-b border-[#1e2e4a]/60 text-slate-400 font-mono-technical text-[9.5px] uppercase">
										<th class="py-1.5 px-3">Account</th>
										<th class="py-1.5 px-3">Name</th>
										<th class="py-1.5 px-3">Type</th>
										<th class="py-1.5 px-3">Direction</th>
										<th class="py-1.5 px-3 text-right">Volume</th>
										<th class="py-1.5 px-3 text-right">Txs</th>
										<th class="py-1.5 px-3 text-center">Status</th>
										<th class="py-1.5 px-3 text-right">Action</th>
									</tr>
								</thead>
								<tbody class="divide-y divide-[#1e2e4a]/40">
									\${connectedRows || '<tr><td colspan="8" class="py-4 text-center text-slate-400 text-[11px]">No direct counterparties recorded</td></tr>'}
								</tbody>
							</table>
						</div>
					</div>

					<!-- Recent Transactions Table -->
					<div class="bg-[#0b192c] border border-[#1e2e4a] rounded-lg p-3">
						<div class="flex items-center justify-between pb-2 border-b border-[#1e2e4a]">
							<span class="font-mono-technical text-[10.5px] text-sky-400 uppercase font-bold">Recent PostgreSQL Ledger Transactions (\${recentTransactions.length})</span>
							<span class="text-[10px] text-slate-400">Chronological money movement</span>
						</div>
						<div class="overflow-x-auto max-h-[220px] overflow-y-auto mt-1">
							<table class="w-full border-collapse text-left">
								<thead>
									<tr class="border-b border-[#1e2e4a]/60 text-slate-400 font-mono-technical text-[9.5px] uppercase">
										<th class="py-1.5 px-3">Tx ID</th>
										<th class="py-1.5 px-3">Date</th>
										<th class="py-1.5 px-3">Channel</th>
										<th class="py-1.5 px-3 text-center">Flow</th>
										<th class="py-1.5 px-3 text-right">Amount</th>
										<th class="py-1.5 px-3">Counterparty</th>
										<th class="py-1.5 px-3">Name</th>
									</tr>
								</thead>
								<tbody class="divide-y divide-[#1e2e4a]/40">
									\${recentTxRows || '<tr><td colspan="7" class="py-4 text-center text-slate-400 text-[11px]">No ledger records found</td></tr>'}
								</tbody>
							</table>
						</div>
					</div>
				</div>
			\`;
		}

		// 9. Account Search & Focus
		function handleAccountSearchInput(val) {
			const query = (val || '').trim();
			const clearBtn = document.getElementById('search-clear-btn');
			const suggBox = document.getElementById('account-search-suggestions');
			if (clearBtn) clearBtn.classList.toggle('hidden', query.length === 0);
			if (!suggBox) return;

			if (query.length < 2) {
				suggBox.classList.add('hidden');
				suggBox.innerHTML = '';
				return;
			}

			const q = query.toLowerCase();
			const matches = [];
			const seenIds = new Set();

			for (const [netId, net] of Object.entries(networksDb)) {
				(net.graphNodes || []).forEach(node => {
					if (seenIds.has(node.id)) return;
					const matchId = node.id.toLowerCase().includes(q);
					const matchName = (node.customer_name || '').toLowerCase().includes(q);
					if (matchId || matchName) {
						seenIds.add(node.id);
						matches.push({
							account_id: node.id,
							customer_name: node.customer_name,
							account_type: node.account_type,
							risk_score: node.risk_score || 20,
							status: node.status || 'Active',
							network_id: netId,
							network_name: net.name
						});
					}
				});
				if (matches.length >= 7) break;
			}

			if (matches.length === 0) {
				suggBox.innerHTML = '<div class="px-3 py-2 text-[11px] text-[#64748b] italic">No matching accounts found</div>';
				suggBox.classList.remove('hidden');
				return;
			}

			suggBox.innerHTML = matches.map(m => {
				const isHigh = m.risk_score >= 70;
				const badgeClass = isHigh ? 'bg-red-500/20 text-red-300 border-red-500/40' : 'bg-blue-500/20 text-blue-300 border-blue-500/40';
				return \`
					<div class="px-3 py-2 hover:bg-[#122543] cursor-pointer flex items-center justify-between transition-colors" onclick="selectSearchAccountResult('\${m.account_id}', '\${m.network_id}')">
						<div class="flex flex-col">
							<div class="flex items-center gap-1.5">
								<span class="font-mono text-[11.5px] text-[#38bdf8] font-bold">\${m.account_id}</span>
								<span class="text-[11px] text-white font-medium">• \${m.customer_name}</span>
							</div>
							<span class="text-[9.5px] text-[#64748b] font-mono">\${m.network_name}</span>
						</div>
						<span class="px-1.5 py-0.5 rounded text-[9.5px] font-mono border \${badgeClass}">Risk: \${m.risk_score}</span>
					</div>
				\`;
			}).join('');
			suggBox.classList.remove('hidden');
		}

		function handleAccountSearchKeyDown(e) {
			if (e.key === 'Enter') {
				const val = e.target.value.trim();
				if (!val) return;
				selectAndFocusAccount(val);
				const suggBox = document.getElementById('account-search-suggestions');
				if (suggBox) suggBox.classList.add('hidden');
			} else if (e.key === 'Escape') {
				clearAccountSearch();
			}
		}

		function selectSearchAccountResult(accId, netId) {
			const input = document.getElementById('account-graph-search');
			if (input) input.value = accId;
			const suggBox = document.getElementById('account-search-suggestions');
			if (suggBox) suggBox.classList.add('hidden');
			selectAndFocusAccount(accId, netId);
		}

		function clearAccountSearch() {
			const input = document.getElementById('account-graph-search');
			if (input) input.value = '';
			const clearBtn = document.getElementById('search-clear-btn');
			if (clearBtn) clearBtn.classList.add('hidden');
			const suggBox = document.getElementById('account-search-suggestions');
			if (suggBox) { suggBox.innerHTML = ''; suggBox.classList.add('hidden'); }
		}

		function selectAndFocusAccount(query, hintNetId) {
			const q = query.trim().toUpperCase();
			let targetNetId = hintNetId;
			let targetNode = null;

			// Check in current network first
			if (!targetNetId && currentlyRenderedNetworkId && networksDb[currentlyRenderedNetworkId]) {
				const found = (networksDb[currentlyRenderedNetworkId].graphNodes || []).find(n => n.id.toUpperCase() === q || (n.customer_name && n.customer_name.toUpperCase().includes(q)));
				if (found) {
					targetNetId = currentlyRenderedNetworkId;
					targetNode = found;
				}
			}

			// Check all networks if not found
			if (!targetNode) {
				for (const [netId, net] of Object.entries(networksDb)) {
					const found = (net.graphNodes || []).find(n => n.id.toUpperCase() === q || (n.customer_name && n.customer_name.toUpperCase().includes(q)));
					if (found) {
						targetNetId = netId;
						targetNode = found;
						break;
					}
				}
			}

			if (!targetNode || !targetNetId) {
				showToast(\`Account "\${query}" not found in transaction networks.\`);
				return;
			}

			if (targetNetId !== currentlyRenderedNetworkId) {
				currentlyRenderedNetworkId = targetNetId;
				renderNetworkGraph(targetNetId, 'network-graph-svg');
			}

			updateActiveNetworkBadge(networksDb[targetNetId]);
			selectAccountNode(targetNode.id, 'network-graph-svg');
			centerGraphOnAccountNode(targetNode.id);

			showToast(\`Focused \${targetNode.id} (\${targetNode.customer_name}) • Risk: \${targetNode.risk_score || 20}\`);
		}

		// 10. Load Network into Main Graph Workspace (Direct Trigger or from Drawer)
		function loadNetworkIntoWorkspace(netId) {
			if (!networksDb[netId]) return;
			currentlyRenderedNetworkId = netId;
			renderNetworkGraph(netId, 'network-graph-svg');

			const net = networksDb[netId];
			if (net.graphNodes && net.graphNodes.length > 0) {
				const sorted = [...net.graphNodes].sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0));
				selectAccountNode(sorted[0].id, 'network-graph-svg');
			}

			updateActiveNetworkBadge(net);

			// Smooth scroll to graph workspace
			const graphSection = document.getElementById('graph-panel-section');
			if (graphSection && typeof graphSection.scrollIntoView === 'function') {
				graphSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
			}

			showToast(\`Loaded network \${net.id} into workspace\`);
		}

		// 11. Sliding Network Inspection Drawer Functions
		function openNetworkInspectionDrawer(netId) {
			const net = networksDb[netId];
			if (!net) return;
			activeDrawerNetworkId = netId;

			const overlay = document.getElementById('network-inspection-overlay');
			const drawer = document.getElementById('network-inspection-drawer');
			const subtitle = document.getElementById('drawer-network-id-subtitle');
			const body = document.getElementById('drawer-content-body');

			if (subtitle) {
				subtitle.textContent = \`\${net.id} • \${net.name}\`;
			}

			const score = (net.score !== undefined && net.score !== null) ? net.score : 50;
			let scoreColor = "text-sky-400";
			if (score >= 90) scoreColor = "text-red-400";
			else if (score >= 70) scoreColor = "text-orange-400";
			else if (score >= 50) scoreColor = "text-yellow-400";

			const status = net.status || 'Active';
			let statusBadge = "bg-green-950/60 text-green-300 border-green-500/40";
			if (status === 'Blocked') statusBadge = "bg-red-950/60 text-red-300 border-red-500/40";
			else if (status === 'Critical' || status === 'Flagged') statusBadge = "bg-orange-950/60 text-orange-300 border-orange-500/40";
			else if (status === 'Under Review') statusBadge = "bg-blue-950/60 text-blue-300 border-blue-500/40";

			const nodes = net.graphNodes || [];
			const links = net.graphLinks || [];

			// Calculate suspicious members
			const suspiciousNodes = nodes.filter(n => 
				['Flagged', 'Critical', 'Under Review', 'Blocked'].includes(n.status) || (n.risk_score || 0) >= 70
			);

			// Inflow & outflow across network members
			let totalInflow = 0;
			let totalOutflow = 0;
			nodes.forEach(n => {
				totalInflow += (n.total_incoming || 0);
				totalOutflow += (n.total_outgoing || 0);
			});

			const formatINRValue = (num) => {
				if (!num || isNaN(num)) return '₹0';
				return '₹' + Math.round(num).toLocaleString('en-IN');
			};

			// Indicators badges
			const indicatorsHtml = (net.indicators || ['Standard Retail Flow']).map(ind => \`
				<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold bg-[#122543] text-sky-300 border border-[#1e2e4a]">
					<span class="w-1.5 h-1.5 rounded-full bg-sky-400"></span>
					\${ind}
				</span>
			\`).join('');

			// Member Accounts List HTML
			const membersHtml = nodes.map(node => {
				const isHigh = (node.risk_score >= 80 || ['Flagged', 'Critical', 'Blocked'].includes(node.status));
				const isReview = (node.risk_score >= 60 && !isHigh);
				const nodeScoreClass = isHigh ? 'text-red-400' : (isReview ? 'text-orange-400' : 'text-sky-400');
				const nodeBadgeClass = isHigh ? 'bg-red-950/50 text-red-300 border-red-500/30' : (isReview ? 'bg-orange-950/50 text-orange-300 border-orange-500/30' : 'bg-slate-800 text-slate-300 border-slate-700');

				return \`
					<div class="p-2.5 rounded-lg bg-[#071324] border border-[#1e2e4a] hover:border-sky-500/50 transition-colors flex items-center justify-between text-left">
						<div class="flex flex-col min-w-0 pr-2">
							<div class="flex items-center gap-2">
								<span class="font-mono text-[12px] text-sky-400 font-bold select-all">\${node.id}</span>
								<span class="px-1.5 py-0.2 rounded text-[9.5px] font-mono border \${nodeBadgeClass}">\${node.status || 'Active'}</span>
							</div>
							<span class="text-[12px] font-medium text-white truncate mt-0.5">\${node.customer_name}</span>
							<div class="flex items-center gap-2 text-[10.5px] text-slate-400 mt-0.5">
								<span>\${node.account_type || 'Savings'}\${node.is_business ? ' (Biz)' : ''}</span>
								<span>•</span>
								<span>Bal: <strong class="text-slate-200">\${node.balance_formatted || '₹0'}</strong></span>
							</div>
						</div>
						<div class="flex flex-col items-end flex-shrink-0">
							<span class="text-[9.5px] font-mono text-slate-400 uppercase">Risk</span>
							<span class="font-mono text-[14px] font-bold \${nodeScoreClass}">\${node.risk_score || 20}</span>
						</div>
					</div>
				\`;
			}).join('');

			body.innerHTML = \`
				<!-- Top Action Card: Primary View Network Graph trigger -->
				<div class="p-3.5 rounded-xl bg-gradient-to-r from-blue-900/40 to-indigo-900/40 border border-blue-500/30 flex items-center justify-between gap-3">
					<div>
						<span class="text-[10px] font-mono uppercase tracking-wider text-sky-300 font-bold block">Ready for Analysis</span>
						<span class="text-[12px] text-slate-200">Load real topology directly into graph workspace</span>
					</div>
					<button onclick="executeLoadNetworkFromDrawer()" class="px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-mono text-[11.5px] font-bold shadow-md shadow-blue-500/30 flex items-center gap-1.5 flex-shrink-0 transition-transform active:scale-95">
						<span>View Graph</span>
						<span class="material-symbols-outlined text-[15px]">arrow_forward</span>
					</button>
				</div>

				<!-- Network Header Overview -->
				<div class="bg-[#071324] border border-[#1e2e4a] rounded-xl p-4 space-y-3">
					<div class="flex items-start justify-between gap-2">
						<div>
							<div class="flex items-center gap-2">
								<span class="font-mono text-[14px] text-sky-400 font-bold select-all">\${net.id}</span>
								<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold border \${statusBadge}">\${status}</span>
							</div>
							<h4 class="font-headline-md text-[17px] text-white font-extrabold tracking-tight mt-1">\${net.name}</h4>
							<span class="inline-block mt-1 px-2.5 py-0.5 rounded-full text-[10.5px] font-mono font-semibold bg-blue-500/10 text-sky-300 border border-blue-500/20">\${net.type || 'Transaction Chain'}</span>
						</div>
						<div class="flex flex-col items-end">
							<span class="font-mono-technical text-[9px] text-slate-400 uppercase font-semibold">Network Risk</span>
							<span class="font-mono text-[22px] font-extrabold \${scoreColor}">\${score} <span class="text-[12px] text-slate-400 font-normal">/ 100</span></span>
						</div>
					</div>

					<!-- Summary Narrative -->
					<p class="font-body-md text-[12px] text-slate-300 bg-[#0b192c] p-2.5 rounded-lg border border-[#1e2e4a]/70 leading-relaxed">
						\${net.summary || 'Authoritative multi-hop transaction cluster detected from live PostgreSQL ledger records.'}
					</p>
				</div>

				<!-- 4-Card Metrics Grid -->
				<div class="grid grid-cols-2 gap-2.5">
					<div class="bg-[#071324] border border-[#1e2e4a] rounded-lg p-3">
						<span class="font-mono-technical text-[9.5px] text-slate-400 uppercase font-semibold block">Total Value</span>
						<span class="font-mono text-[15px] font-bold text-white mt-0.5 block">\${net.totalValue || '₹0'}</span>
						<span class="text-[10px] text-slate-400 mt-0.5 block">\${links.length} directed transaction paths</span>
					</div>
					<div class="bg-[#071324] border border-[#1e2e4a] rounded-lg p-3">
						<span class="font-mono-technical text-[9.5px] text-slate-400 uppercase font-semibold block">Members</span>
						<span class="font-mono text-[15px] font-bold text-white mt-0.5 block">\${nodes.length} Accounts</span>
						<span class="text-[10px] \${suspiciousNodes.length > 0 ? 'text-red-400 font-semibold' : 'text-slate-400'} mt-0.5 block">\${suspiciousNodes.length} Suspicious</span>
					</div>
					<div class="bg-[#071324] border border-[#1e2e4a] rounded-lg p-3">
						<span class="font-mono-technical text-[9.5px] text-slate-400 uppercase font-semibold block">Member Inflow</span>
						<span class="font-mono text-[14px] font-bold text-green-400 mt-0.5 block">\${formatINRValue(totalInflow)}</span>
						<span class="text-[10px] text-slate-400 mt-0.5 block">Aggregate incoming</span>
					</div>
					<div class="bg-[#071324] border border-[#1e2e4a] rounded-lg p-3">
						<span class="font-mono-technical text-[9.5px] text-slate-400 uppercase font-semibold block">Member Outflow</span>
						<span class="font-mono text-[14px] font-bold text-orange-400 mt-0.5 block">\${formatINRValue(totalOutflow)}</span>
						<span class="text-[10px] text-slate-400 mt-0.5 block">Aggregate outgoing</span>
					</div>
				</div>

				<!-- Relevant Network Indicators -->
				<div class="bg-[#071324] border border-[#1e2e4a] rounded-xl p-3.5 space-y-2">
					<span class="font-mono-technical text-[10px] text-sky-400 uppercase font-bold tracking-wider block">Relevant Network Indicators:</span>
					<div class="flex flex-wrap gap-1.5">
						\${indicatorsHtml}
					</div>
				</div>

				<!-- Member Accounts Section -->
				<div class="space-y-2">
					<div class="flex items-center justify-between px-0.5">
						<span class="font-mono-technical text-[10.5px] text-sky-400 uppercase font-bold">Network Members (\${nodes.length})</span>
						<span class="text-[10px] text-slate-400">PostgreSQL Verified</span>
					</div>
					<div class="space-y-1.5 max-h-[300px] overflow-y-auto pr-0.5">
						\${membersHtml || '<div class="text-[11px] text-slate-400 italic">No member data available</div>'}
					</div>
				</div>
			\`;

			overlay.classList.remove('hidden');
			void overlay.offsetWidth; // Force reflow
			overlay.classList.add('overlay-open');
			drawer.classList.add('drawer-open');
		}

		function closeNetworkInspectionDrawer() {
			const overlay = document.getElementById('network-inspection-overlay');
			const drawer = document.getElementById('network-inspection-drawer');
			if (drawer) drawer.classList.remove('drawer-open');
			if (overlay) {
				overlay.classList.remove('overlay-open');
				setTimeout(() => {
					if (!overlay.classList.contains('overlay-open')) {
						overlay.classList.add('hidden');
					}
				}, 300);
			}
		}

		function executeLoadNetworkFromDrawer() {
			if (!activeDrawerNetworkId) return;
			const targetNetId = activeDrawerNetworkId;
			closeNetworkInspectionDrawer();
			loadNetworkIntoWorkspace(targetNetId);
		}

		// 12. Fullscreen Visualizer Controls (Requirement 2)
		function toggleFullscreenVisualizer() {
			const isCurrentlyFullscreen = document.fullscreenElement || document.body.classList.contains('network-fullscreen-mode');
			if (!isCurrentlyFullscreen) {
				if (document.documentElement.requestFullscreen) {
					document.documentElement.requestFullscreen().then(() => {
						setFullscreenVisualizerMode(true);
					}).catch(() => {
						// Fallback if browser security denies iframe/subwindow fullscreen
						setFullscreenVisualizerMode(true);
					});
				} else {
					setFullscreenVisualizerMode(true);
				}
			} else {
				if (document.fullscreenElement && document.exitFullscreen) {
					document.exitFullscreen().then(() => {
						setFullscreenVisualizerMode(false);
					}).catch(() => {
						setFullscreenVisualizerMode(false);
					});
				} else {
					setFullscreenVisualizerMode(false);
				}
			}
		}

		function setFullscreenVisualizerMode(active) {
			document.body.classList.toggle('network-fullscreen-mode', active);
			const fsBtn = document.getElementById('fullscreen-btn');
			if (fsBtn) {
				const icon = fsBtn.querySelector('.material-symbols-outlined');
				if (icon) {
					icon.textContent = active ? 'fullscreen_exit' : 'fullscreen';
				}
				fsBtn.setAttribute('title', active ? 'Exit Fullscreen' : 'Toggle Fullscreen');
			}
			setTimeout(handleGraphResize, 160);
		}

		document.addEventListener('fullscreenchange', () => {
			const isFs = !!document.fullscreenElement;
			setFullscreenVisualizerMode(isFs);
		});

		// 13. Zoom, Reset & Filter Handlers
		function zoomInGraph() {
			graphState.zoom = Math.min(3.5, graphState.zoom * 1.25);
			applyGraphViewportTransform();
		}

		function zoomOutGraph() {
			graphState.zoom = Math.max(0.3, graphState.zoom * 0.8);
			applyGraphViewportTransform();
		}

		function resetActiveVisualizerGraph() {
			graphState.zoom = 1.0;
			graphState.panX = 0;
			graphState.panY = 0;
			graphState.hopDepth = 0;
			graphState.suspiciousOnly = false;
			const suspToggle = document.getElementById('toggle-suspicious');
			if (suspToggle) suspToggle.checked = false;
			updateHopButtonsUI();
			applyGraphViewportTransform();
			if (currentlyRenderedNetworkId) {
				renderNetworkGraph(currentlyRenderedNetworkId, 'network-graph-svg');
			}
			showToast('Graph viewport reset.');
		}

		function setHopDepthFilter(hop) {
			graphState.hopDepth = parseInt(hop, 10) || 0;
			updateHopButtonsUI();
			if (currentlyRenderedNetworkId) {
				renderNetworkGraph(currentlyRenderedNetworkId, 'network-graph-svg');
			}
		}

		function updateHopButtonsUI() {
			const btns = document.querySelectorAll('.hop-btn');
			btns.forEach(b => {
				const h = parseInt(b.getAttribute('data-hop'), 10);
				if (h === graphState.hopDepth) {
					b.className = "hop-btn px-2.5 py-1 text-[11px] font-mono rounded font-semibold transition-all bg-[#1d4ed8] text-white";
				} else {
					b.className = "hop-btn px-2.5 py-1 text-[11px] font-mono rounded font-semibold transition-all text-[#94a3b8] hover:text-white";
				}
			});
		}

		function toggleGraphLabels(show) {
			graphState.showLabels = show;
			const groups = document.querySelectorAll('.node-label-group');
			groups.forEach(g => { g.style.display = show ? '' : 'none'; });
		}

		function toggleGraphAmounts(show) {
			graphState.showAmounts = show;
			if (currentlyRenderedNetworkId) {
				renderNetworkGraph(currentlyRenderedNetworkId, 'network-graph-svg');
			}
		}

		function toggleGraphDirections(show) {
			graphState.showDirections = show;
			if (currentlyRenderedNetworkId) {
				renderNetworkGraph(currentlyRenderedNetworkId, 'network-graph-svg');
			}
		}

		function toggleSuspiciousOnly(show) {
			graphState.suspiciousOnly = show;
			if (currentlyRenderedNetworkId) {
				renderNetworkGraph(currentlyRenderedNetworkId, 'network-graph-svg');
			}
		}

		function handleGraphResize() {
			const svg = document.getElementById('network-graph-svg');
			const wrapper = document.getElementById('graph-viewport-wrapper');
			if (!svg || !wrapper) return;

			const w = wrapper.clientWidth || 1000;
			const h = wrapper.clientHeight || 500;
			svg.setAttribute('viewBox', \`0 0 \${w} \${h}\`);
			graphState.canvasWidth = w;
			graphState.canvasHeight = h;

			if (currentlyRenderedNetworkId) {
				renderNetworkGraph(currentlyRenderedNetworkId, 'network-graph-svg');
			}
		}

		// 14. Networks Table Rendering & Filtering
		function renderNetworksTable(netList) {
			const tbody = document.getElementById('networks-table-body');
			if (!tbody) return;

			tbody.innerHTML = '';
			if (!netList || netList.length === 0) {
				tbody.innerHTML = '<tr><td colspan="10" class="py-8 text-center text-on-surface-variant font-body-md">No networks found in database.</td></tr>';
				recountSummaryCards();
				return;
			}

			netList.forEach(net => {
				const netId = net.id;
				const name = net.name || \`Network \${netId}\`;
				const type = net.type || 'Transaction Chain';
				const score = (net.score !== undefined && net.score !== null) ? net.score : 50;
				const totalValue = net.totalValue || '₹0';
				const members = net.members || (net.graphNodes ? net.graphNodes.length : 0);
				const connectedCount = net.connectedCount || 0;
				const lastActivity = net.lastActivity || 'Recent';
				const status = net.status || 'Active';

				let riskCategory = "Low";
				let scoreBadgeClass = "text-blue-800 bg-blue-50 border-blue-200";
				if (score >= 90) {
					riskCategory = "Critical";
					scoreBadgeClass = "text-red-600 bg-red-50 border-red-200";
				} else if (score >= 70) {
					riskCategory = "High";
					scoreBadgeClass = "text-orange-600 bg-orange-50 border-orange-200";
				} else if (score >= 50) {
					riskCategory = "Medium";
					scoreBadgeClass = "text-yellow-600 bg-yellow-50 border-yellow-200";
				}

				let statusBadgeClass = "bg-green-50 text-green-700 border-green-200";
				if (status === 'Blocked') statusBadgeClass = "bg-red-50 text-red-700 border-red-200";
				else if (status === 'Flagged') statusBadgeClass = "bg-orange-50 text-orange-700 border-orange-200";
				else if (status === 'Under Review') statusBadgeClass = "bg-blue-50 text-blue-700 border-blue-200";

				const tr = document.createElement('tr');
				tr.className = "hover:bg-[#f0f7ff]/70 transition-colors duration-150 group cursor-pointer";
				tr.setAttribute('data-net-id', netId);
				tr.setAttribute('data-risk', riskCategory);
				tr.setAttribute('data-status', status);
				tr.setAttribute('data-type', type);
				// Clicking row opens inspection drawer (Requirement 3 & 5)
				tr.onclick = () => openNetworkInspectionDrawer(netId);

				tr.innerHTML = \`
					<td class="py-2.5 px-3 font-mono-technical text-[12.5px] text-secondary font-bold hover:underline whitespace-nowrap" onclick="event.stopPropagation(); openNetworkInspectionDrawer('\${netId}')">\${netId}</td>
					<td class="py-2.5 px-3 font-headline-md text-[12.5px] text-on-surface font-bold truncate max-w-[190px]">\${name}</td>
					<td class="py-2.5 px-3 font-body-md text-[12px] text-on-surface whitespace-nowrap">\${type}</td>
					<td class="py-2.5 px-3 text-right whitespace-nowrap">
						<span class="font-mono-technical text-[11px] font-bold px-2 py-0.5 rounded border \${scoreBadgeClass}">\${score} / 100</span>
					</td>
					<td class="py-2.5 px-3 font-mono-technical text-[12px] text-on-surface text-right font-semibold whitespace-nowrap">\${totalValue}</td>
					<td class="py-2.5 px-3 font-mono-technical text-[12px] text-on-surface-variant text-right font-semibold whitespace-nowrap">\${members}</td>
					<td class="py-2.5 px-3 font-mono-technical text-[12px] text-on-surface-variant text-right font-semibold whitespace-nowrap">\${connectedCount}</td>
					<td class="py-2.5 px-3 font-body-md text-[11.5px] text-on-surface-variant whitespace-nowrap">\${lastActivity}</td>
					<td class="py-2.5 px-3 whitespace-nowrap">
						<span class="px-2 py-0.5 rounded-full text-[10.5px] font-semibold \${statusBadgeClass}">\${status}</span>
					</td>
					<td class="py-2.5 px-3 text-right whitespace-nowrap">
						<button class="inspect-btn text-[11.5px] font-bold text-secondary hover:text-secondary-container focus:outline-none inline-flex items-center gap-1 group/btn" onclick="event.stopPropagation(); openNetworkInspectionDrawer('\${netId}')">
							Inspect <span class="inline-block transition-transform duration-150 group-hover/btn:translate-x-0.5">→</span>
						</button>
					</td>
				\`;
				tbody.appendChild(tr);
			});

			cachedRows = Array.from(tbody.querySelectorAll('tr')).map(row => {
				const netId = row.getAttribute('data-net-id');
				const data = networksDb[netId];
				return {
					element: row,
					id: netId ? netId.toLowerCase() : '',
					name: data ? (data.name || '').toLowerCase() : '',
					type: data ? (data.type || '').toLowerCase() : '',
					risk: row.getAttribute('data-risk'),
					status: data ? data.status : 'Active'
				};
			});

			recountSummaryCards();
		}

		function recountSummaryCards() {
			const allNets = Object.values(networksDb);
			document.getElementById('count-total').textContent = allNets.length.toString();
			document.getElementById('count-high-risk').textContent = allNets.filter(n => (n.score || 0) >= 80).length.toString();
			document.getElementById('count-review').textContent = allNets.filter(n => (n.score || 0) >= 55 && (n.score || 0) < 80).length.toString();
			document.getElementById('count-newly-detected').textContent = allNets.filter(n => ['Flagged', 'Blocked'].includes(n.status)).length.toString();
		}

		function applyWorkspaceFilters() {
			const search = (document.getElementById('filter-search').value || '').toLowerCase().trim();
			const risk = document.getElementById('filter-risk').value;
			const type = document.getElementById('filter-type').value;
			const status = document.getElementById('filter-status').value;

			let visibleCount = 0;
			cachedRows.forEach(item => {
				const matchSearch = (!search || item.id.includes(search) || item.name.includes(search));
				const matchRisk = (risk === 'All' || item.risk === risk);
				const matchType = (type === 'All' || item.type.toLowerCase().includes(type.toLowerCase()));
				const matchStatus = (status === 'All' || item.status === status);

				if (matchSearch && matchRisk && matchType && matchStatus) {
					item.element.classList.remove('hidden');
					visibleCount++;
				} else {
					item.element.classList.add('hidden');
				}
			});

			const counter = document.getElementById('filtered-networks-count');
			if (counter) counter.textContent = \`Showing \${visibleCount} of \${cachedRows.length}\`;
		}

		function clearAllWorkspaceFilters() {
			document.getElementById('filter-search').value = '';
			document.getElementById('filter-risk').value = 'All';
			document.getElementById('filter-type').value = 'All';
			document.getElementById('filter-status').value = 'All';
			applyWorkspaceFilters();
		}

		function onSearchInput() {
			clearTimeout(searchDebounceTimeout);
			searchDebounceTimeout = setTimeout(applyWorkspaceFilters, 200);
		}

		// Global Init
		window.addEventListener('DOMContentLoaded', () => {
			initSidebarState();
			initGraphInteractionHandlers();
			loadNetworksData();
			window.addEventListener('resize', handleGraphResize);

			// Close search dropdown on click outside
			document.addEventListener('click', (e) => {
				const searchContainer = document.getElementById('account-graph-search');
				const suggBox = document.getElementById('account-search-suggestions');
				if (suggBox && !e.target.closest('#account-graph-search') && !e.target.closest('#account-search-suggestions')) {
					suggBox.classList.add('hidden');
				}
			});

			// Escape key closes inspection drawer
			document.addEventListener('keydown', (e) => {
				if (e.key === 'Escape') {
					closeNetworkInspectionDrawer();
				}
			});
		});

		window.addEventListener('muleguard:transaction-ingested', () => {
			loadNetworksData().then(() => {
				if (currentlyRenderedNetworkId) {
					renderNetworkGraph(currentlyRenderedNetworkId, 'network-graph-svg');
				}
			});
		});
	</script>
</body>

</html>
`;
}

// Write both compliance and investigator files
const complianceHtml = generatePage('compliance');
const investigatorHtml = generatePage('investigator');

fs.writeFileSync(path.join(__dirname, '../frontend/bank/compliance/network-intelligence.html'), complianceHtml, 'utf8');
fs.writeFileSync(path.join(__dirname, '../frontend/bank/investigator/network-intelligence.html'), investigatorHtml, 'utf8');

console.log('Successfully generated refined compliance and investigator network-intelligence.html pages!');
