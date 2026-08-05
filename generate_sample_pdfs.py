import os
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

sample_dir = os.path.join(os.path.dirname(__file__), 'sample_docs')
os.makedirs(sample_dir, exist_ok=True)

domains = [
    {
        'project': 'Project Helios Solar Grid',
        'code': 'HELIOS',
        'type': 'BRD',
        'filename': 'Project_Helios_Solar_Grid_BRD.pdf',
        'lead': 'Dr. Robert Thorne',
        'role': 'Chief Power Systems Architect',
        'email': 'r.thorne@helios-grid.io',
        'topic': 'Renewable Energy Systems & Smart Grid Management',
        'details': [
            'Helios Solar Grid manages multi-gigawatt photovoltaic distribution across 14 regional substations.',
            'The core ingestion engine processes 50,000 telemetry samples per second from high-voltage inverters.',
            'System security complies with NERC-CIP cybersecurity standards using AES-256 encrypted VPN channels.',
            'Failover procedures dictate automatic battery bank isolation within 12 milliseconds of grid frequency drop.'
        ]
    },
    {
        'project': 'Project Chrono Supply Chain',
        'code': 'CHRONO',
        'type': 'FRD',
        'filename': 'Project_Chrono_Supply_Chain_FRD.pdf',
        'lead': 'Elena Rostova',
        'role': 'Global Logistics Lead',
        'email': 'e.rostova@chrono-logistics.com',
        'topic': 'Autonomous Cargo & Supply Chain Tracking',
        'details': [
            'Chrono tracks over 250,000 multi-modal freight containers in real-time across international shipping lanes.',
            'Integrates RFID sensor arrays with automated customs clearance workflows at major maritime ports.',
            'System throughput handles 1.2 million status events per hour with zero data loss SLAs.',
            'Machine learning models predict customs bottleneck delays with 94.8% accuracy.'
        ]
    },
    {
        'project': 'Project Aegis Cyber Vault',
        'code': 'AEGIS',
        'type': 'Architecture',
        'filename': 'Project_Aegis_Cyber_Vault_Specs.pdf',
        'lead': 'Marcus Vance',
        'role': 'Head of Threat Intelligence',
        'email': 'm.vance@aegis-security.net',
        'topic': 'Zero-Trust Cyber Defense & Vault Security',
        'details': [
            'Aegis Cyber Vault implements quantum-resistant lattice cryptographic algorithms for bank vault storage.',
            'Continuous threat scanning isolates anomalous payload executions within isolated hypervisor enclaves.',
            'Biometric multi-factor authentication requires quorum consensus from three security officers.',
            'Audit logging writes immutable event hashes directly to tamper-proof hardware security modules (HSM).'
        ]
    },
    {
        'project': 'Project BioHealth Clinical Engine',
        'code': 'BIOHEALTH',
        'type': 'BRD',
        'filename': 'Project_BioHealth_Clinical_BRD.pdf',
        'lead': 'Dr. Alistair Finch',
        'role': 'Chief Medical Informatics Officer',
        'email': 'a.finch@biohealth-clinical.org',
        'topic': 'Genomic & EHR Data Integration Platform',
        'details': [
            'BioHealth processes high-throughput genomic sequencing datasets for oncology clinical trials.',
            'Complies strictly with HIPAA, HITECH, and GDPR data privacy frameworks for patient records.',
            'HL7 FHIR API interfaces communicate with hospital electronic health record systems nationwide.',
            'Real-time adverse event detection flags potential drug-drug interaction risks within 300ms.'
        ]
    },
    {
        'project': 'Project Quantum Trade Engine',
        'code': 'QUANTUM',
        'type': 'FRD',
        'filename': 'Project_Quantum_Trade_Engine_FRD.pdf',
        'lead': 'Samantha Sterling',
        'role': 'VP of Algorithmic Trading Systems',
        'email': 's.sterling@quantum-cap.com',
        'topic': 'Ultra-Low Latency High Frequency Trading',
        'details': [
            'Quantum Trade Engine executes equity and futures orders with sub-microsecond matching latency.',
            'Uses FPGA hardware acceleration cards for direct market data feed handler parsing.',
            'Risk management engine evaluates portfolio margin thresholds prior to order gateway dispatch.',
            'Includes automated circuit breaker trip logic to prevent runaway algorithmic order cascades.'
        ]
    },
    {
        'project': 'Project Neptune Subsea Cable',
        'code': 'NEPTUNE',
        'type': 'SOP',
        'filename': 'Project_Neptune_Subsea_SOP.pdf',
        'lead': 'Captain David H. Miller',
        'role': 'Offshore Fiber Operations Director',
        'email': 'd.miller@neptune-telecom.io',
        'topic': 'Trans-Oceanic Fiber Maintenance & Repair',
        'details': [
            'Neptune operates 38,000 kilometers of deep-sea fiber optic cables across Atlantic routes.',
            'Optical Time-Domain Reflectometers (OTDR) pinpoint undersea fiber cable breaks to within 5 meters.',
            'ROV repair vessels deploy specialized cutting and splicing tools at ocean depths exceeding 4,000 meters.',
            'Dynamic path rerouting redirects global internet traffic through backup trans-pacific trunks.'
        ]
    },
    {
        'project': 'Project Apex Cloud Native K8s',
        'code': 'APEX',
        'type': 'Architecture',
        'filename': 'Project_Apex_Cloud_Architecture.pdf',
        'lead': 'Siddharth Nair',
        'role': 'Principal Cloud Infrastructure Architect',
        'email': 's.nair@apex-cloud.io',
        'topic': 'Multi-Region Distributed Kubernetes Platform',
        'details': [
            'Apex orchestrates 15,000 microservices across AWS, Azure, and Google Cloud Platform hybrid clusters.',
            'Istio service mesh manages mutual TLS (mTLS) traffic encryption and traffic splitting policies.',
            'Prometheus and Grafana stacks collect over 10 million metrics points per minute for telemetry.',
            'Automated GitOps pipeline via ArgoCD deploys microservice updates without downtime.'
        ]
    },
    {
        'project': 'Project Titan Mining Automation',
        'code': 'TITAN',
        'type': 'BRD',
        'filename': 'Project_Titan_Mining_BRD.pdf',
        'lead': 'Jocelyn Dupree',
        'role': 'Autonomous Fleet Director',
        'email': 'j.dupree@titan-heavy.com',
        'topic': 'Heavy Machinery Autonomous Navigation',
        'details': [
            'Titan automates 400-ton haul trucks operating in open-pit copper mines under extreme weather.',
            'LiDAR and millimeter-wave radar fusion detects obstacles in dense dust and blizzard conditions.',
            'Central fleet dispatcher optimizes ore hauling routes to reduce diesel fuel consumption by 18%.',
            'Emergency remote kill-switch stops heavy vehicles within 3 meters upon perimeter boundary breach.'
        ]
    },
    {
        'project': 'Project Iris Vision AI Security',
        'code': 'IRIS',
        'type': 'FRD',
        'filename': 'Project_Iris_Vision_AI_FRD.pdf',
        'lead': 'Dr. Kenneth Zhao',
        'role': 'Director of Computer Vision R&D',
        'email': 'k.zhao@iris-ai.tech',
        'topic': 'Biometric Access & Perimeter Video Analytics',
        'details': [
            'Iris analyzes 4K video streams from 2,000 airport security cameras simultaneously.',
            'Deep convolutional neural networks detect unattended baggage and restricted zone intrusions.',
            'Edge AI processing units process 60 frames per second at local camera junction boxes.',
            'Integrates with municipal law enforcement emergency alert feeds during critical incidents.'
        ]
    },
    {
        'project': 'Project Horizon Banking Engine',
        'code': 'HORIZON',
        'type': 'BRD',
        'filename': 'Project_Horizon_Core_Banking_BRD.pdf',
        'lead': 'Victoria Montgomery',
        'role': 'Head of Core Banking Transformation',
        'email': 'v.montgomery@horizon-bank.com',
        'topic': 'Next-Gen Distributed Core Banking System',
        'details': [
            'Horizon Core Banking processes 45 million customer account ledger postings daily.',
            'ACID-compliant relational database cluster guarantees zero ledger variance during nightly settlement.',
            'Real-time fraud analytics engine scores transaction risk vectors in under 45 milliseconds.',
            'Open Banking RESTful APIs enable third-party fintech app integrations via OAuth2 security.'
        ]
    },
    {
        'project': 'Project Astra Satellite Telemetry',
        'code': 'ASTRA',
        'type': 'SOP',
        'filename': 'Project_Astra_Satellite_SOP.pdf',
        'lead': 'Commander Raymond Cruz',
        'role': 'Orbital Operations Commander',
        'email': 'r.cruz@astra-space.gov',
        'topic': 'Low-Earth Orbit Satellite Constellation Operations',
        'details': [
            'Astra manages telemetry, tracking, and command (TT&C) for 120 earth observation satellites.',
            'Ground stations in Norway, Chile, and Svalbard download 50 Terabytes of imagery data daily.',
            'Automated collision avoidance algorithms perform thruster burn maneuvers to prevent space debris impacts.',
            'Battery degradation tracking models optimize solar panel angles during orbital eclipse phases.'
        ]
    },
    {
        'project': 'Project Sentinel Disaster Recovery',
        'code': 'SENTINEL',
        'type': 'SOP',
        'filename': 'Project_Sentinel_Disaster_Recovery_SOP.pdf',
        'lead': 'Hannah Abbott',
        'role': 'Enterprise Business Continuity Manager',
        'email': 'h.abbott@sentinel-resilience.org',
        'topic': 'Enterprise Disaster Recovery & Failover',
        'details': [
            'Sentinel guarantees a Recovery Time Objective (RTO) of under 15 minutes for mission-critical apps.',
            'Recovery Point Objective (RPO) is maintained at less than 1 second using synchronous storage replication.',
            'Annual disaster recovery simulation tests failover of primary datacenter workload to secondary site.',
            'Automated DNS failover updates public IP routes globally within 30 seconds of outage detection.'
        ]
    },
    {
        'project': 'Project Vantage Real Estate Analytics',
        'code': 'VANTAGE',
        'type': 'BRD',
        'filename': 'Project_Vantage_RealEstate_BRD.pdf',
        'lead': 'Oliver Kingsley',
        'role': 'VP of Commercial Property Analytics',
        'email': 'o.kingsley@vantage-prop.com',
        'topic': 'Commercial Real Estate Valuation Engine',
        'details': [
            'Vantage evaluates commercial property portfolios valued at over $50 Billion globally.',
            'Spatial GIS mapping overlays flood risk, foot traffic, zoning, and transit accessibility metrics.',
            'Automated cash flow forecasting calculates net operating income (NOI) under various inflation scenarios.',
            'Tenant lease management subsystem alerts property managers 180 days prior to lease expiration.'
        ]
    },
    {
        'project': 'Project Nexus Smart City Grid',
        'code': 'NEXUS',
        'type': 'FRD',
        'filename': 'Project_Nexus_Smart_City_FRD.pdf',
        'lead': 'Dr. Sophia Lorenzen',
        'role': 'Urban Technology Innovation Director',
        'email': 's.lorenzen@nexus-smartcity.gov',
        'topic': 'Urban Traffic & Environmental IoT Grid',
        'details': [
            'Nexus integrates 50,000 IoT sensors measuring air quality, noise levels, and traffic flow.',
            'Adaptive traffic signals dynamically adjust green-light duration to relieve congestion during peak hours.',
            'Smart street lighting dims automatically when no pedestrian or vehicle activity is detected.',
            'Public dashboard publishes real-time PM2.5 and nitrogen dioxide environmental health indexes.'
        ]
    },
    {
        'project': 'Project CyberShield IAM Platform',
        'code': 'CYBERSHIELD',
        'type': 'Architecture',
        'filename': 'Project_CyberShield_IAM_Architecture.pdf',
        'lead': 'Gabriel Thorne',
        'role': 'Chief Information Security Officer (CISO)',
        'email': 'g.thorne@cybershield-iam.com',
        'topic': 'Enterprise Identity & Access Management',
        'details': [
            'CyberShield provisions user access across 500 corporate applications using SCIM 2.0 protocols.',
            'Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) enforce least privilege.',
            'Privileged Access Management (PAM) vault records and audits all root administrator SSH sessions.',
            'Single Sign-On (SSO) integration supports SAML 2.0, OpenID Connect (OIDC), and FIDO2 webauthn keys.'
        ]
    }
]

print(f"Generating {len(domains)} comprehensive PDF files (5-6 pages each)...")

styles = getSampleStyleSheet()
normal_style = styles['Normal']
title_style = styles['Title']
heading1 = styles['Heading1']
heading2 = styles['Heading2']
heading3 = styles['Heading3']

for idx, dom in enumerate(domains):
    pdf_path = os.path.join(sample_dir, dom['filename'])
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
    story = []
    
    # --- PAGE 1: Cover & Executive Summary ---
    story.append(Paragraph(f"{dom['project']} ({dom['type']})", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph(f"<b>Document Type:</b> {dom['type']} | <b>Project Code:</b> {dom['code']}", heading3))
    story.append(Paragraph(f"<b>Domain:</b> {dom['topic']}", heading3))
    story.append(Paragraph(f"<b>Lead Contact / Author:</b> {dom['lead']} ({dom['role']}) - <i>{dom['email']}</i>", heading3))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("1. Executive Summary & Strategic Objectives", heading1))
    story.append(Paragraph(f"This document represents the formal enterprise specification for <b>{dom['project']}</b>. Developed under the governance of {dom['lead']}, this project addresses mission-critical infrastructure demands within {dom['topic']}. The primary mandate of this initiative is to deliver an ultra-resilient, scalable, and secure operational framework.", normal_style))
    story.append(Spacer(1, 10))
    for det in dom['details']:
        story.append(Paragraph(f"• {det}", normal_style))
        story.append(Spacer(1, 4))
    story.append(Spacer(1, 20))
    
    # Add structured table on Page 1
    table_data = [
        ['Attribute', 'Specification Value'],
        ['Project Lead Name', dom['lead']],
        ['Designated Role', dom['role']],
        ['Official Email', dom['email']],
        ['Classification Level', 'Enterprise Confidential / Tier 1'],
        ['Target SLA Uptime', '99.999% Availability'],
        ['Security Standard', 'ISO/IEC 27001 & SOC2 Type II']
    ]
    t = Table(table_data, colWidths=[180, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))
    story.append(t)
    story.append(PageBreak())
    
    # --- PAGE 2: Architectural Framework & Components ---
    story.append(Paragraph("2. System Architecture & Technical Specifications", heading1))
    story.append(Paragraph(f"The technical design of {dom['project']} relies on decoupled microservices and event-driven data distribution. High-frequency telemetry streams are ingested by dedicated edge clusters and routed to central data repositories.", normal_style))
    story.append(Spacer(1, 10))
    
    code_low = dom['code'].lower()
    story.append(Paragraph("2.1 Subsystem Blueprint", heading2))
    story.append(Paragraph(f"The subsystem pipeline for {dom['code']} is partitioned into three principal layers:", normal_style))
    story.append(Paragraph(f"1. <b>Ingestion Gateway Subsystem ({code_low}-ingest)</b>: Accepts incoming data payloads over secure TLS/UDP sockets. Maintains strict throughput quotas.", normal_style))
    story.append(Paragraph(f"2. <b>Normalization Subsystem ({code_low}-processor)</b>: Parses incoming data streams, validates schema definitions, and extracts key business attributes.", normal_style))
    story.append(Paragraph(f"3. <b>Persistence Subsystem ({code_low}-store)</b>: Stores normalized events into relational databases and vector indices for real-time RAG querying.", normal_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("2.2 Data Ingestion Protocol & Hex Mapping", heading2))
    story.append(Paragraph(f"Data packets ingested by {dom['project']} follow a standardized 256-byte binary schema:", normal_style))
    story.append(Paragraph("• Bytes 0-3: Magic Header Preamble (0x50524F4A - 'PROJ')", normal_style))
    story.append(Paragraph("• Bytes 4-7: Subsystem Tenant ID (32-bit Unsigned Integer)", normal_style))
    story.append(Paragraph("• Bytes 8-15: Precise UTC Timestamp (64-bit Microsecond Epoch)", normal_style))
    story.append(Paragraph("• Bytes 16-31: Security Authentication Signature (HMAC-SHA256)", normal_style))
    story.append(Paragraph("• Bytes 32-255: Encrypted Payload Content Array", normal_style))
    story.append(Spacer(1, 20))
    story.append(PageBreak())
    
    # --- PAGE 3: Operational Requirements & Workflows ---
    story.append(Paragraph("3. Operational Requirements & Failover Workflows", heading1))
    story.append(Paragraph(f"Ensuring uninterrupted operational availability for {dom['project']} requires rigorous failover protocols and continuous monitoring. The system incorporates automated health checks executed every 500 milliseconds.", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("3.1 Disaster Recovery & High Availability", heading2))
    story.append(Paragraph(f"In the event of a primary region disruption, {dom['lead']} has established the following high-availability guidelines:", normal_style))
    story.append(Paragraph("• <b>Primary Storage Replication</b>: Data is synchronously mirrored across three availability zones with zero loss tolerance.", normal_style))
    story.append(Paragraph("• <b>Automated Failover Trigger</b>: If the primary node fails three consecutive health checks, traffic DNS endpoints are automatically reassigned to standby nodes.", normal_style))
    story.append(Paragraph("• <b>Emergency Escalation Contact</b>: In case of severe outage, operational personnel must alert the lead engineer directly.", normal_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("3.2 Performance Benchmarks", heading2))
    story.append(Paragraph("The platform undergoes weekly performance stress testing under simulated load spikes. Key metrics include:", normal_style))
    story.append(Paragraph("• P99 Processing Latency: Under 25 milliseconds", normal_style))
    story.append(Paragraph("• Maximum Sustained Concurrency: 100,000 active sessions", normal_style))
    story.append(Paragraph("• Maximum Memory Overhead: Under 16 Gigabytes per worker pod", normal_style))
    story.append(Spacer(1, 20))
    story.append(PageBreak())
    
    # --- PAGE 4: Governance, Stakeholders & Compliance ---
    story.append(Paragraph("4. Stakeholder Directory & Governance", heading1))
    story.append(Paragraph(f"Governance for {dom['project']} is managed by an interdisciplinary steering committee. Regular monthly reviews ensure compliance with internal risk frameworks and external regulatory requirements.", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("4.1 Key Personnel Directory", heading2))
    story.append(Paragraph(f"• <b>Project Sponsor & Lead:</b> {dom['lead']}", normal_style))
    story.append(Paragraph(f"• <b>Designated Role:</b> {dom['role']}", normal_style))
    story.append(Paragraph(f"• <b>Direct Communication Channel:</b> {dom['email']}", normal_style))
    story.append(Paragraph("• <b>Security & Compliance Lead:</b> Marcus Vance (m.vance@enterprise-security.org)", normal_style))
    story.append(Paragraph("• <b>Operations Steering Coordinator:</b> Captain Arthur Pendelton (a.pendelton@operations-governance.io)", normal_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("4.2 Regulatory Compliance Matrix", heading2))
    story.append(Paragraph("This project adheres to the following corporate governance standards:", normal_style))
    story.append(Paragraph("1. <b>SOC2 Type II Audit Assurance</b>: Verified controls for security, availability, and confidentiality.", normal_style))
    story.append(Paragraph("2. <b>ISO 27001 Certification</b>: Full compliance with Information Security Management System (ISMS) policies.", normal_style))
    story.append(Paragraph("3. <b>GDPR / Data Privacy Mandates</b>: Right to be forgotten and data minimization routines built into storage schemas.", normal_style))
    story.append(Spacer(1, 20))
    story.append(PageBreak())
    
    # --- PAGE 5: Milestones, Audit & Appendix ---
    story.append(Paragraph("5. Project Milestones & Implementation Roadmap", heading1))
    story.append(Paragraph(f"The deployment of {dom['project']} is divided into four distinct execution phases spanning 18 months. Progress is tracked via weekly sprint reviews.", normal_style))
    story.append(Spacer(1, 10))
    
    roadmap_table = [
        ['Phase Milestone', 'Target Quarter', 'Deliverable Summary', 'Status'],
        ['Phase 1: Architecture & PoC', 'Q1 2026', 'Core engine prototype & vector index pipeline', 'Completed'],
        ['Phase 2: Alpha Testing', 'Q2 2026', 'Multi-node benchmark load testing & RBAC audit', 'In Progress'],
        ['Phase 3: Beta Field Trial', 'Q3 2026', 'Staging deployment with live regional traffic', 'Scheduled'],
        ['Phase 4: Full Enterprise Rollout', 'Q4 2026', 'Production cutover and legacy system sunset', 'Planned']
    ]
    t_road = Table(roadmap_table, colWidths=[130, 80, 200, 70])
    t_road.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F1F5F9')])
    ]))
    story.append(t_road)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("5.1 Appendix: Glossary & Contact Escalation", heading2))
    story.append(Paragraph(f"For questions regarding this document or to request modification rights, contact <b>{dom['lead']}</b> at <code>{dom['email']}</code>. All audit logs for document modifications are permanently recorded in the central database.", normal_style))
    
    doc.build(story)
    print(f"[{idx+1}/15] Generated {dom['filename']} successfully.")

print("=== ALL 15 COMPREHENSIVE PDF FILES GENERATED ===")
