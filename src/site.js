// Scroll effects. CSS scroll-driven animations do the heavy lifting where the
// browser supports them; this file adds the floating bar and a fallback reveal.
(function () {
  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Floating bar on the home page, once the big masthead has scrolled away.
  var bar = document.querySelector('.minibar-float');
  var mast = document.querySelector('.masthead-large');
  if (bar && mast && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (e) {
      bar.classList.toggle('is-on', !e[0].isIntersecting);
    }).observe(mast);
  }

  // Reading progress on articles.
  var progress = document.querySelector('.progress');
  if (progress) {
    var tick = function () {
      var max = root.scrollHeight - innerHeight;
      progress.style.transform = 'scaleX(' + (max > 0 ? scrollY / max : 0) + ')';
    };
    addEventListener('scroll', tick, { passive: true });
    tick();
  }

  // Fallback for browsers without scroll-driven animations: reveal and parallax by script.
  if (reduce || (window.CSS && CSS.supports('animation-timeline: view()'))) return;
  root.classList.add('js-motion');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    document.querySelectorAll('.reveal').forEach(function (el) {
      if (el.getBoundingClientRect().top < innerHeight) el.classList.add('is-in'); else io.observe(el);
    });
  }
  var layers = [].slice.call(document.querySelectorAll('.hero-photo .photo-frame > *, .cover-photo .photo-frame > *, .chapter-photo .photo-frame > *'));
  var frame = false;
  var drift = function () {
    frame = false;
    layers.forEach(function (el) {
      var r = el.parentNode.getBoundingClientRect();
      var t = (r.top + r.height / 2 - innerHeight / 2) / innerHeight; // -1..1 around centre
      el.style.transform = 'scale(1.15) translate3d(0,' + (t * -7).toFixed(2) + '%,0)';
    });
  };
  addEventListener('scroll', function () { if (!frame) { frame = true; requestAnimationFrame(drift); } }, { passive: true });
  drift();
})();

