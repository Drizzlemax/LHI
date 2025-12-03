// script.js
// Data for companies
const companiesData = [
    {
        name: "Lion Heart International – PNG",
        tagline: "Regional headquarters and strategic operations",
        icon: "fas fa-globe-asia",
        color: "#c0392b"
    },
    {
        name: "Lion Heart International – Australia",
        tagline: "Corporate governance and investments",
        icon: "fas fa-building",
        color: "#c0392b"
    },
    {
        name: "Lion Heart International – South Africa",
        tagline: "African operations and market expansion",
        icon: "fas fa-globe-africa",
        color: "#c0392b"
    },
    {
        name: "Genesis Communications PNG Ltd.",
        tagline: "Telecommunications and connectivity solutions",
        icon: "fas fa-satellite-dish",
        color: "#2c3e50"
    },
    {
        name: "Genesis Communications Australia",
        tagline: "Advanced communication technologies",
        icon: "fas fa-broadcast-tower",
        color: "#2c3e50"
    },
    {
        name: "Lion Heart Agriculture Mineral Investments LTD",
        tagline: "Sustainable agriculture and resource development",
        icon: "fas fa-tractor",
        color: "#27ae60"
    },
    {
        name: "Lion Track Limited",
        tagline: "Infrastructure and logistics solutions",
        icon: "fas fa-road",
        color: "#f39c12"
    },
    {
        name: "Superior Coffee (Australia) Limited",
        tagline: "Premium commodity production and export",
        icon: "fas fa-coffee",
        color: "#8b4513"
    }
];

// Data for leadership
const leadershipData = [
    {
        name: "Sir James Wilson",
        title: "Group Chairman & CEO",
        bio: "Visionary leader with over 25 years in international business development and strategic investments across Asia-Pacific and Africa.",
        imgColor: "#c0392b"
    },
    {
        name: "Dr. Elizabeth Chen",
        title: "Chief Operations Officer",
        bio: "Expert in operational excellence with a Ph.D. in International Business and extensive experience in cross-border enterprise management.",
        imgColor: "#2c3e50"
    },
    {
        name: "Michael Rodriguez",
        title: "Chief Financial Officer",
        bio: "Finance executive with deep expertise in global capital markets, M&A, and sustainable investment strategies.",
        imgColor: "#d4af37"
    }
];

// Data for sectors
const sectorsData = [
    {
        name: "Communications",
        description: "Driving connectivity through advanced telecommunications infrastructure and digital solutions.",
        icon: "fas fa-satellite"
    },
    {
        name: "Agriculture",
        description: "Sustainable farming practices and agribusiness investments for food security and export.",
        icon: "fas fa-seedling"
    },
    {
        name: "Mining",
        description: "Responsible resource extraction with a focus on environmental stewardship and community development.",
        icon: "fas fa-mountain"
    },
    {
        name: "Infrastructure",
        description: "Building critical transportation, logistics, and energy infrastructure to support economic growth.",
        icon: "fas fa-hard-hat"
    },
    {
        name: "Premium Commodities",
        description: "Production and global distribution of high-value agricultural and mineral products.",
        icon: "fas fa-gem"
    }
];

// Initialize the page when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize map
    initMap();
    
    // Populate companies
    populateCompanies();
    
    // Populate leadership
    populateLeadership();
    
    // Populate sectors
    populateSectors();
    
    // Setup navigation
    setupNavigation();
    
    // Setup scroll animations
    setupScrollAnimations();
    
    // Setup mobile menu toggle
    setupMobileMenu();
});

// Initialize the global map
function initMap() {
    // Create map centered on Pacific region
    const map = L.map('global-map').setView([-8.7832, 124.5085], 3);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Add markers for company locations
    const locations = [
        { name: "PNG Headquarters", coords: [-9.4438, 147.1803], type: "headquarters" },
        { name: "Australia Office", coords: [-35.2809, 149.1300], type: "headquarters" },
        { name: "South Africa Office", coords: [-25.7479, 28.2293], type: "headquarters" },
        { name: "Mining Operations", coords: [-6.0833, 145.3833], type: "operations" },
        { name: "Agriculture Projects", coords: [-6.3149, 143.9555], type: "operations" },
        { name: "Communications Hub", coords: [-33.8688, 151.2093], type: "operations" }
    ];
    
    locations.forEach(location => {
        const markerColor = location.type === "headquarters" ? "#d4af37" : "#c0392b";
        const marker = L.circleMarker(location.coords, {
            color: markerColor,
            fillColor: markerColor,
            fillOpacity: 0.8,
            radius: 8
        }).addTo(map);
        
        marker.bindPopup(`<strong>${location.name}</strong><br>Lion Heart International Group`);
    });
}

// Populate companies section
function populateCompanies() {
    const companiesGrid = document.querySelector('.companies-grid');
    
    companiesData.forEach(company => {
        const companyCard = document.createElement('div');
        companyCard.className = 'company-card';
        
        companyCard.innerHTML = `
            <div class="company-logo">
                <i class="${company.icon}" style="color: ${company.color};"></