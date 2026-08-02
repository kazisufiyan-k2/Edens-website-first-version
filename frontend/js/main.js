// ============================================================
// EDENS REFRIGERATION & AIR-CONDITIONING — SITE-WIDE SCRIPTS
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

  // ---- Mobile menu toggle ----
  const menuToggle = document.querySelector('.menu-toggle');
  const navWrap = document.querySelector('.nav-wrap');
  if (menuToggle && navWrap) {
    menuToggle.addEventListener('click', () => {
      navWrap.classList.toggle('menu-open');
    });
    // close menu when a link is clicked (mobile)
    document.querySelectorAll('.nav-links a').forEach(link => {
      link.addEventListener('click', () => navWrap.classList.remove('menu-open'));
    });
  }

  // ---- Duplicate ticker content for seamless infinite scroll ----
  const ticker = document.querySelector('.ticker-track');
  if (ticker) {
    ticker.innerHTML += ticker.innerHTML;
  }

  // ---- Form tabs (Enquiry / Review) on contact page ----
  const tabs = document.querySelectorAll('.form-tab');
  const panels = document.querySelectorAll('.form-panel');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(tab.dataset.target).classList.add('active');
    });
  });

  // ---- Star rating widget ----
  const starWrap = document.querySelector('.star-rating');
  if (starWrap) {
    const stars = starWrap.querySelectorAll('span');
    const ratingInput = document.getElementById('review-rating');
    stars.forEach(star => {
      star.addEventListener('click', () => {
        const value = parseInt(star.dataset.value, 10);
        ratingInput.value = value;
        stars.forEach(s => {
          s.classList.toggle('active', parseInt(s.dataset.value, 10) <= value);
        });
      });
    });
  }

  // ---- Scroll reveal (simple, respects reduced motion) ----
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!prefersReduced && 'IntersectionObserver' in window) {
    const revealEls = document.querySelectorAll('.service-card, .why-card, .review-card, .service-full-card, .value-card');
    revealEls.forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(16px)';
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    });
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(el => observer.observe(el));
  }

});
