const canvas = document.getElementById('energy-canvas');
const ctx = canvas.getContext('2d');
const btn = document.getElementById('energy-btn');

// Configuration de l'espace autour du bouton pour l'animation
const paddingX = 250; // Longueur du cône
const paddingY = 150; // Hauteur maximale du cône
let width, height, btnRect;

// Palette de couleurs : différentes teintes de vert
const greenShades = [
    '#44fe449e', // Vert classique (Lime)
    '#63df90b9', // LimeGreen
    '#1bffa79b', // MediumSpringGreen
    '#48bc095f', // LightGreen
    '#17d368b3', // SeaGreen
    '#7fc614ce'  // GreenYellow
];

// Met à jour la taille du canvas en fonction du bouton
function resize() {
    btnRect = btn.getBoundingClientRect();
    width = btnRect.width + (paddingX * 2);
    height = btnRect.height + (paddingY * 2);
    canvas.width = width;
    canvas.height = height;
}

// Classe gérant chaque particule individuelle
class Particle {
    constructor(side) {
        this.side = side; // 'left' ou 'right'
        this.reset();
    }

    reset() {
        // 1. POINT DE DÉPART : X sur le bord du bouton, Y aléatoire sur sa hauteur
        const startX = this.side === 'left' ? paddingX : paddingX + btnRect.width;
        const startY = paddingY + (Math.random() * btnRect.height);

        this.x = startX;
        this.y = startY;

        // 2. POINT DE CONVERGENCE (CIBLE) : Extrémité gauche/droite, centré en Y
        const offset = 75; // Plus ce chiffre est petit, plus le point est proche du bouton
        const targetX = this.side === 'left' ? (paddingX - offset) : (paddingX + btnRect.width + offset);
        const targetY = paddingY + (btnRect.height / 2);  // Centre du bouton

        // 3. CALCUL DE LA TRAJECTOIRE
        // On calcule la distance en X et en Y entre le départ et la cible
        const dx = targetX - this.x;
        const dy = targetY - this.y;
        
        // Math.atan2 donne l'angle exact vers lequel la particule doit se diriger
        const angle = Math.atan2(dy, dx); 
        
        // Vitesse de la particule
        const speed = Math.random() * 3 + 3;

        // Application de l'angle aux vecteurs de vitesse
        this.vx = Math.cos(angle) * speed;
        this.vy = Math.sin(angle) * speed;

        this.life = 1.0; 
        
        // 4. ASTUCE : Disparition parfaite
        // On calcule le temps qu'il faut pour atteindre la cible, 
        // pour que la particule disparaisse (life = 0) exactement au point de convergence !
        const distanceTotal = Math.sqrt(dx * dx + dy * dy);
        const timeToReach = distanceTotal / speed;
        const speedFactor = 1.25; // 1.0 = normal, 2.0 = deux fois plus vite
        this.decay = (1.0 / timeToReach) * speedFactor;
        
        // Esthétique
        this.color = greenShades[Math.floor(Math.random() * greenShades.length)];
        this.size = Math.random() * 3 + 1.5;
    }

    update() {
        this.x += this.vx;
        this.y += this.vy;
        this.life -= this.decay;
        
        // Relance la particule une fois morte
        if (this.life <= 0) {
            this.reset();
        }
    }

    draw() {
        ctx.globalAlpha = Math.max(0, this.life); // max(0, ...) évite les valeurs négatives
        ctx.fillStyle = this.color;
        ctx.shadowBlur = 10;
        ctx.shadowColor = this.color;
        
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
    }
}

// Initialisation
window.addEventListener('resize', resize);
resize();

const particles = [];
const PARTICLE_COUNT = 100; // Nombre total de particules

// Créer les particules réparties à gauche et à droite
for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push(new Particle(i % 2 === 0 ? 'left' : 'right'));
}

// Boucle d'animation principale
function animate() {
    ctx.clearRect(0, 0, width, height); // Nettoie la frame précédente
    
    particles.forEach(p => {
        p.update();
        p.draw();
    });
    
    requestAnimationFrame(animate);
}

// Lance l'animation
animate();