window.onload = function() {
  const canvas = document.getElementById('backgroundParticles');
  const ctx = canvas.getContext('2d');
  let particlesArray;

  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  window.addEventListener('resize', function(){
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    init();
  });

  function Particle(x, y, directionX, directionY, size, color){
    this.x = x;
    this.y = y;
    this.directionX = directionX;
    this.directionY = directionY;
    this.size = size;
    this.color = color;
  }

  Particle.prototype.draw = function(){
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2, false);
    ctx.fillStyle = this.color;
    ctx.fill();
  }

  Particle.prototype.update = function(){
    if(this.x > canvas.width || this.x < 0){
      this.directionX = -this.directionX;
    }
    if(this.y > canvas.height || this.y < 0){
      this.directionY = -this.directionY;
    }
    this.x += this.directionX;
    this.y += this.directionY;
    this.draw();
  }

  function init(){
    particlesArray = [];
    for(let i = 0; i < 50; i++){
      let size = Math.random() * 4;
      let x = Math.random() * (innerWidth - size * 2);
      let y = Math.random() * (innerHeight - size * 2);
      let directionX = (Math.random() * 0.4) - 0.2;
      let directionY = (Math.random() * 0.4) - 0.2;
      let color = 'rgba(255,255,255,0.8)';
      particlesArray.push(new Particle(x, y, directionX, directionY, size, color));
    }
  }

  function animate(){
    requestAnimationFrame(animate);
    ctx.clearRect(0,0,innerWidth,innerHeight);
    for(let i = 0; i < particlesArray.length; i++){
      particlesArray[i].update();
    }
  }

  init();
  animate();
};
